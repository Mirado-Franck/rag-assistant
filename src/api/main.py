"""API FastAPI du projet de classification et de recherche documentaire."""

from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.ingestion.ingest_upload import (
    UploadedDocumentIngestionError,
    ingest_uploaded_document,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
REGISTRY_FILE = PROJECT_ROOT / "data" / "documents_registry.json"
CHUNKS_FILE = PROJECT_ROOT / "data" / "chunks" / "all_chunks.json"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
LLM_MODEL = "llama3.2"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CATEGORIES = [
    "Règlements",
    "Guides pratiques",
    "Procédures",
    "Organisation & plannings",
    "Formulaires & documents ponctuels",
]
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="DocuClassif AI — API",
    description="API de classification et de recherche dans les documents institutionnels",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Modèles de requête/réponse
# ---------------------------------------------------------------------------
class ClassificationResult(BaseModel):
    categorie: str
    confiance: float
    justification: str
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    needs_confirmation: bool
    file_id: str
    filename: str
    text_preview: str


class ConfirmRequest(BaseModel):
    file_id: str
    categorie: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    category: str | None = None
    source_file: str | None = None
    n_results: int = Field(default=4, ge=1, le=20)


class QueryResponse(BaseModel):
    question: str
    reponse: str
    sources: list[dict[str, str]]
    filtre: str
    temps_ms: float
    nb_chunks_trouves: int


class DocumentInfo(BaseModel):
    filename: str
    categorie: str
    date_ajout: str
    type_original: str
    chunks_count: int


class HealthResponse(BaseModel):
    status: str
    modele_llm: str
    modele_embedding: str
    nb_documents: int
    nb_chunks: int
    categories: dict[str, int]


# ---------------------------------------------------------------------------
# Fichiers et données
# ---------------------------------------------------------------------------
def load_registry() -> dict[str, dict[str, Any]]:
    """Charge le registre, ou retourne un registre vide s'il n'existe pas."""
    if not REGISTRY_FILE.exists():
        return {}
    try:
        registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Le registre JSON est invalide.") from exc
    if not isinstance(registry, dict):
        raise HTTPException(status_code=500, detail="Le registre doit être un objet JSON.")
    return registry


def save_registry(registry: dict[str, dict[str, Any]]) -> None:
    """Écrit le registre de façon atomique pour éviter un JSON partiel."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = REGISTRY_FILE.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(REGISTRY_FILE)


def load_chunks() -> list[dict[str, Any]]:
    """Charge les chunks du corpus initial pour les statistiques historiques."""
    if not CHUNKS_FILE.exists():
        return []
    try:
        chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Le fichier de chunks JSON est invalide.") from exc
    if not isinstance(chunks, list):
        raise HTTPException(status_code=500, detail="Le fichier de chunks doit contenir une liste.")
    return chunks


def extract_uploaded_text(filename: str, content: bytes) -> tuple[str, int]:
    """Extrait le texte d'un PDF, DOCX ou TXT téléversé."""
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        try:
            import pymupdf

            with pymupdf.open(stream=content, filetype="pdf") as pdf:
                page_texts = [page.get_text().strip() for page in pdf]
                return "\n\n".join(text for text in page_texts if text), len(page_texts)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"PDF illisible : {exc}") from exc

    if extension == ".docx":
        try:
            from docx import Document

            document = Document(BytesIO(content))
            blocks = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
            for table in document.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    if any(cells):
                        blocks.append(" | ".join(cells))
            # DOCX n'a pas de pagination stable sans moteur de mise en page.
            return "\n\n".join(blocks), 0
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="Le support DOCX nécessite python-docx (pip install python-docx).",
            ) from exc
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"DOCX illisible : {exc}") from exc

    if extension == ".txt":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        return text, 1

    raise HTTPException(status_code=400, detail="Format non supporté.")


def classify_text_mock(text: str) -> dict[str, Any]:
    """Classification heuristique provisoire, en attendant l'intégration A1.

    Le titre du document est examiné avant le corps du texte : un règlement
    peut mentionner des dates/calendriers sans devenir un document de planning.
    """
    title_rules = [
        ("Règlements", ("règlement", "reglement", "code général", "code general", "statut")),
        ("Formulaires & documents ponctuels", ("formulaire", "attestation", "convention")),
        ("Procédures", ("procédure", "procedure", "démarche", "demarche")),
        ("Organisation & plannings", ("calendrier", "planning", "emploi du temps", "organigramme")),
        ("Guides pratiques", ("guide", "foire aux questions", "faq")),
    ]
    for line in (line.strip().casefold() for line in text.splitlines()[:15]):
        if not line or len(line) > 140:
            continue
        for category, keywords in title_rules:
            if any(keyword in line for keyword in keywords):
                return {
                    "categorie": category,
                    "confiance": 0.93,
                    "justification": "La catégorie est déterminée à partir du titre du document (classification simulée).",
                    "alternatives": [],
                    "needs_confirmation": False,
                }

    sample = text[:5000].casefold()
    rules = [
        (
            "Formulaires & documents ponctuels",
            ("formulaire", "attestation", "convention de stage", "nom :", "signature :"),
            0.91,
            "Le texte ressemble à un formulaire ou à un document à compléter.",
        ),
        (
            "Organisation & plannings",
            ("calendrier", "planning", "emploi du temps", "organigramme", "dates officielles"),
            0.87,
            "Le texte contient des dates ou des éléments d'organisation.",
        ),
        (
            "Règlements",
            ("article", "décret", "règlement", "interdit", "sanction", "obligation"),
            0.86,
            "Le texte contient des règles ou des formulations normatives.",
        ),
        (
            "Procédures",
            ("étape 1", "procédure", "démarche", "pièces à fournir", "à déposer"),
            0.82,
            "Le texte semble décrire une démarche à effectuer.",
        ),
        (
            "Guides pratiques",
            ("guide", "conseils", "comment", "foire aux questions", "faq"),
            0.76,
            "Le texte semble être un guide pratique.",
        ),
    ]

    for category, keywords, confidence, justification in rules:
        if any(keyword in sample for keyword in keywords):
            alternatives = []
            if confidence < 0.8:
                alternatives = [
                    {"categorie": "Procédures", "probabilite": 0.15},
                    {"categorie": "Règlements", "probabilite": 0.10},
                ]
            return {
                "categorie": category,
                "confiance": confidence,
                "justification": justification,
                "alternatives": alternatives,
                "needs_confirmation": confidence < 0.8,
            }

    return {
        "categorie": "Guides pratiques",
        "confiance": 0.45,
        "justification": "Classification simulée incertaine : une vérification humaine est nécessaire.",
        "alternatives": [
            {"categorie": "Procédures", "probabilite": 0.25},
            {"categorie": "Règlements", "probabilite": 0.15},
            {"categorie": "Formulaires & documents ponctuels", "probabilite": 0.10},
        ],
        "needs_confirmation": True,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["Système"])
def health_check() -> HealthResponse:
    """Retourne l'état de l'API et des données préparées."""
    registry = load_registry()
    chunks = load_chunks()
    counts = Counter(item.get("categorie", "Non classifié") for item in registry.values())
    return HealthResponse(
        status="ok",
        modele_llm=LLM_MODEL,
        modele_embedding=EMBEDDING_MODEL.rsplit("/", 1)[-1],
        nb_documents=len(registry),
        nb_chunks=len(chunks),
        categories={category: counts.get(category, 0) for category in CATEGORIES},
    )


@app.post("/api/upload", response_model=ClassificationResult, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)) -> ClassificationResult:
    """Sauvegarde, extrait et classe provisoirement un document téléversé."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Le fichier n'a pas de nom.")

    safe_name = Path(file.filename.replace(chr(92), "/")).name
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Formats acceptés : PDF, TXT et DOCX.",
        )

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Le fichier dépasse la limite de 20 Mo.")
    if not content:
        raise HTTPException(status_code=400, detail="Le fichier est vide.")

    try:
        text, _page_count = extract_uploaded_text(safe_name, content)
    finally:
        await file.close()

    if len(text.strip()) < 50:
        raise HTTPException(
            status_code=422,
            detail="Le fichier ne contient pas assez de texte exploitable (50 caractères minimum).",
        )

    file_id = uuid.uuid4().hex[:8]
    stored_name = f"{file_id}_{safe_name}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / stored_name).write_bytes(content)

    result = classify_text_mock(text)
    return ClassificationResult(
        **result,
        file_id=file_id,
        filename=safe_name,
        text_preview=text[:300] + ("..." if len(text) > 300 else ""),
    )


@app.post("/api/confirm", tags=["Documents"])
def confirm_classification(request: ConfirmRequest) -> dict[str, Any]:
    """Confirme la catégorie, indexe le fichier dans ChromaDB et met à jour le registre."""
    if request.categorie not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Catégorie invalide. Choix : {CATEGORIES}")
    if not re.fullmatch(r"[0-9a-fA-F]{8}", request.file_id):
        raise HTTPException(status_code=400, detail="file_id invalide.")

    matches = list(UPLOAD_DIR.glob(f"{request.file_id}_*"))
    if len(matches) != 1 or not matches[0].is_file():
        raise HTTPException(status_code=404, detail="Fichier temporaire introuvable ou expiré.")

    stored_path = matches[0]
    original_name = stored_path.name[len(request.file_id) + 1 :]
    try:
        text, page_count = extract_uploaded_text(original_name, stored_path.read_bytes())
    except HTTPException:
        raise
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Impossible de lire le fichier uploadé : {exc}") from exc

    if len(text.strip()) < 50:
        raise HTTPException(
            status_code=422,
            detail="Le fichier ne contient pas assez de texte exploitable pour être indexé.",
        )

    try:
        chunks_count = ingest_uploaded_document(
            filename=stored_path.name,
            text=text,
            categorie=request.categorie,
            pages=page_count,
        )
    except UploadedDocumentIngestionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Échec de l'indexation du document : {exc}") from exc

    return {
        "status": "success",
        "message": f"Document '{original_name}' confirmé et indexé dans ChromaDB.",
        "file_id": request.file_id,
        "source_file": stored_path.name,
        "categorie": request.categorie,
        "indexe": True,
        "chunks_count": chunks_count,
    }


@lru_cache(maxsize=1)
def get_rag_pipeline() -> Any:
    """Initialise le RAG à la première requête et le réutilise ensuite."""
    from src.rag.rag_pipeline import RAGPipeline

    return RAGPipeline()


@app.post("/api/query", response_model=QueryResponse, tags=["Recherche"])
def query_documents(request: QueryRequest) -> QueryResponse:
    """Exécute une recherche et une génération de réponse avec le pipeline RAG."""
    if request.category and request.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Catégorie invalide. Choix : {CATEGORIES}")

    try:
        result = get_rag_pipeline().query(
            question=request.question,
            n_results=request.n_results,
            category=request.category,
            source_file=request.source_file,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Le pipeline RAG n'est pas disponible. Vérifie que ChromaDB est indexé, "
                f"que le modèle d'embedding est installé et qu'Ollama sert {LLM_MODEL!r}. Détail : {exc}"
            ),
        ) from exc
    return QueryResponse(**result)


@app.get("/api/documents", response_model=list[DocumentInfo], tags=["Documents"])
def list_documents(category: str | None = Query(default=None)) -> list[DocumentInfo]:
    """Liste les documents du registre, avec filtre optionnel par catégorie."""
    if category and category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Catégorie invalide. Choix : {CATEGORIES}")

    registry = load_registry()
    chunk_counts = Counter(chunk.get("source", "") for chunk in load_chunks())
    documents = []
    for filename, info in sorted(registry.items()):
        if category and info.get("categorie") != category:
            continue
        documents.append(
            DocumentInfo(
                filename=filename,
                categorie=info.get("categorie", "Non classifié"),
                date_ajout=info.get("date_ajout", "inconnu"),
                type_original=info.get("type_original", "inconnu"),
                chunks_count=info.get("chunks_count", chunk_counts.get(filename, 0)),
            )
        )
    return documents


@app.get("/api/categories", tags=["Documents"])
def get_categories() -> dict[str, Any]:
    """Retourne les documents et le nombre de documents de chaque catégorie."""
    registry = load_registry()
    categories = {}
    for category in CATEGORIES:
        filenames = sorted(
            filename
            for filename, info in registry.items()
            if info.get("categorie") == category
        )
        categories[category] = {"nb_documents": len(filenames), "documents": filenames}
    return {"categories": categories, "total_documents": len(registry)}


# Routes racine et santé historiques conservées pour la compatibilité.
@app.get("/health", include_in_schema=False)
def legacy_health() -> dict[str, str]:
    return {"status": "ok", "message": "DocuClassif AI - API fonctionnelle"}


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"application": "DocuClassif AI", "version": "1.0.0", "documentation": "/docs"}

"""Indexe dans ChromaDB un document qu'un utilisateur vient de confirmer.

Le nom de source doit être le nom stocké sur disque (par exemple
``4a5b585d_reglement.pdf``) et doit être identique à la clé du registre.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.ingestion.ingest import (
    CATEGORIES,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    IngestionDataError,
    load_registry,
)
from src.ingestion.chunk import split_into_chunks

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma_db"
REGISTRY_PATH = PROJECT_ROOT / "data" / "documents_registry.json"
BATCH_SIZE = 64


class UploadedDocumentIngestionError(RuntimeError):
    """Erreur exploitable par l'API pendant l'indexation d'un upload."""


@lru_cache(maxsize=1)
def _embedding_model() -> Any:
    """Charge une seule fois le même modèle que l'ingestion du corpus initial."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise UploadedDocumentIngestionError(
            "sentence-transformers n'est pas installé. Active le venv et installe requirements.txt."
        ) from exc
    try:
        return SentenceTransformer(EMBEDDING_MODEL)
    except Exception as exc:
        raise UploadedDocumentIngestionError(
            f"Impossible de charger le modèle d'embedding {EMBEDDING_MODEL!r}: {exc}"
        ) from exc


def chunk_text(text: str) -> list[tuple[str, str]]:
    """Découpe le texte en conservant la stratégie et les sections de chunk.py."""
    if not isinstance(text, str) or not text.strip():
        return []
    return split_into_chunks(text)


def _write_registry(registry: dict[str, dict[str, Any]]) -> None:
    """Sauvegarde atomiquement le registre pour éviter de le tronquer."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = REGISTRY_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(REGISTRY_PATH)


def _get_collection() -> Any:
    """Ouvre la collection créée au Jour 3 sans en créer une vide par erreur."""
    try:
        import chromadb
    except ImportError as exc:
        raise UploadedDocumentIngestionError(
            "chromadb n'est pas installé. Active le venv et installe requirements.txt."
        ) from exc

    try:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        return client.get_collection(COLLECTION_NAME)
    except Exception as exc:
        raise UploadedDocumentIngestionError(
            "Collection ChromaDB 'documents' introuvable. Lance d'abord "
            "python src/ingestion/ingest.py pour indexer les 16 documents du corpus."
        ) from exc


def ingest_uploaded_document(
    filename: str,
    text: str,
    categorie: str,
    *,
    pages: int | None = None,
) -> int:
    """Découpe, vectorise et indexe le document confirmé, puis met à jour le registre.

    L'opération est idempotente : confirmer de nouveau le même upload met à jour
    ses chunks au lieu de les dupliquer.
    """
    if not filename or Path(filename).name != filename:
        raise UploadedDocumentIngestionError("Nom de source invalide.")
    if categorie not in CATEGORIES:
        raise UploadedDocumentIngestionError(f"Catégorie invalide : {categorie!r}.")
    if len(text.strip()) < 50:
        raise UploadedDocumentIngestionError(
            "Texte insuffisant pour créer des chunks (50 caractères minimum)."
        )

    chunks_with_sections = chunk_text(text)
    if not chunks_with_sections:
        raise UploadedDocumentIngestionError(
            "Le texte n'a produit aucun chunk valide (minimum 50 caractères par chunk)."
        )

    try:
        registry = load_registry(REGISTRY_PATH)
    except IngestionDataError as exc:
        raise UploadedDocumentIngestionError(f"Registre invalide : {exc}") from exc

    model = _embedding_model()
    chunk_texts = [chunk for chunk, _section in chunks_with_sections]
    try:
        embeddings = model.encode(
            chunk_texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()
    except Exception as exc:
        raise UploadedDocumentIngestionError(f"Échec du calcul des embeddings : {exc}") from exc

    collection = _get_collection()
    source_hash = hashlib.sha256(filename.encode("utf-8")).hexdigest()[:20]
    ids = [f"upload_{source_hash}_chunk_{index}" for index in range(len(chunk_texts))]
    added_on = date.today().isoformat()
    metadata = [
        {
            "source": filename,
            "categorie": categorie,
            "chunk_index": index,
            "date_ajout": added_on,
            "char_count": len(chunk),
            "section": section or "Sans section",
        }
        for index, (chunk, section) in enumerate(chunks_with_sections)
    ]

    try:
        previous = collection.get(where={"source": filename}, include=["metadatas"])
        previous_ids = set(previous.get("ids", []))
        collection.upsert(
            ids=ids,
            documents=chunk_texts,
            metadatas=metadata,
            embeddings=embeddings,
        )
        stale_ids = previous_ids - set(ids)
        if stale_ids:
            collection.delete(ids=sorted(stale_ids))
    except Exception as exc:
        raise UploadedDocumentIngestionError(f"Échec de l'écriture dans ChromaDB : {exc}") from exc

    registry_entry: dict[str, Any] = {
        "categorie": categorie,
        "date_ajout": added_on,
        "type_original": Path(filename).suffix.lstrip(".").upper() or "INCONNU",
        "chunks_count": len(chunk_texts),
        "status": "indexé",
    }
    if pages is not None and pages > 0:
        registry_entry["pages"] = pages
    registry[filename] = registry_entry
    try:
        _write_registry(registry)
    except OSError as exc:
        # Les vecteurs ont été écrits : signale explicitement la désynchronisation.
        raise UploadedDocumentIngestionError(
            f"Document indexé dans ChromaDB, mais impossible d'enregistrer le registre : {exc}"
        ) from exc

    print(f"✅ {len(chunk_texts)} chunks indexés pour {filename} [{categorie}]")
    return len(chunk_texts)

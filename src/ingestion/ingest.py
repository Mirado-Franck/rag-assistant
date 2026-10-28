"""Indexe les chunks préparés dans une collection ChromaDB persistante.

Usage depuis la racine du projet :
    python src/ingestion/ingest.py --validate-only
    python src/ingestion/ingest.py
    python src/ingestion/ingest.py --rebuild

Le modèle Sentence Transformers est utilisé pour les chunks ET doit être
réutilisé par test_search.py pour encoder les requêtes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = PROJECT_ROOT / "data" / "chunks" / "all_chunks.json"
REGISTRY_PATH = PROJECT_ROOT / "data" / "documents_registry.json"
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma_db"
COLLECTION_NAME = "documents"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 64
CATEGORIES = {
    "Règlements",
    "Guides pratiques",
    "Procédures",
    "Organisation & plannings",
    "Formulaires & documents ponctuels",
}
REQUIRED_CHUNK_FIELDS = {"id", "source", "chunk_index", "text", "char_count"}
REQUIRED_REGISTRY_FIELDS = {"categorie", "date_ajout", "type_original"}


class IngestionDataError(ValueError):
    """Erreur de format ou de cohérence des fichiers d'entrée."""


def load_chunks(path: Path = CHUNKS_PATH) -> list[dict[str, Any]]:
    """Charge et valide la liste de chunks issue de chunk.py."""
    try:
        chunks = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IngestionDataError(f"Fichier de chunks introuvable : {path}") from exc
    except json.JSONDecodeError as exc:
        raise IngestionDataError(f"JSON invalide dans {path} : {exc}") from exc

    if not isinstance(chunks, list) or not chunks:
        raise IngestionDataError("Le fichier de chunks doit contenir une liste non vide.")

    ids: set[str] = set()
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise IngestionDataError(f"Le chunk #{index} n'est pas un objet JSON.")
        missing = REQUIRED_CHUNK_FIELDS - chunk.keys()
        if missing:
            raise IngestionDataError(
                f"Le chunk #{index} ne contient pas les champs : {', '.join(sorted(missing))}."
            )
        if not all(isinstance(chunk[key], str) and chunk[key].strip()
                   for key in ("id", "source", "text")):
            raise IngestionDataError(
                f"Le chunk #{index} doit avoir un id, une source et un texte non vides."
            )
        if chunk["id"] in ids:
            raise IngestionDataError(f"Identifiant de chunk dupliqué : {chunk['id']}")
        ids.add(chunk["id"])
        if not isinstance(chunk["chunk_index"], int) or chunk["chunk_index"] < 0:
            raise IngestionDataError(f"chunk_index invalide pour {chunk['id']}.")
        if not isinstance(chunk["char_count"], int) or chunk["char_count"] != len(chunk["text"]):
            raise IngestionDataError(
                f"char_count ne correspond pas au texte pour {chunk['id']}."
            )

    return chunks


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, dict[str, Any]]:
    """Charge et valide le registre qui associe chaque source à sa catégorie."""
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IngestionDataError(f"Registre introuvable : {path}") from exc
    except json.JSONDecodeError as exc:
        raise IngestionDataError(f"JSON invalide dans {path} : {exc}") from exc

    if not isinstance(registry, dict) or not registry:
        raise IngestionDataError("Le registre doit être un objet JSON non vide.")

    for source, entry in registry.items():
        if not isinstance(entry, dict):
            raise IngestionDataError(f"L'entrée du registre pour {source} doit être un objet.")
        missing = REQUIRED_REGISTRY_FIELDS - entry.keys()
        if missing:
            raise IngestionDataError(
                f"L'entrée {source} ne contient pas : {', '.join(sorted(missing))}."
            )
        if entry["categorie"] not in CATEGORIES:
            raise IngestionDataError(
                f"Catégorie inconnue pour {source} : {entry['categorie']!r}."
            )
        if not isinstance(entry["type_original"], str) or not entry["type_original"].strip():
            raise IngestionDataError(f"type_original manquant pour {source}.")
        try:
            date.fromisoformat(entry["date_ajout"])
        except (TypeError, ValueError) as exc:
            raise IngestionDataError(
                f"date_ajout doit être au format AAAA-MM-JJ pour {source}."
            ) from exc
        if "pages" in entry and (not isinstance(entry["pages"], int) or entry["pages"] < 1):
            raise IngestionDataError(f"Nombre de pages invalide pour {source}.")

    return registry


def validate_inputs(
    chunks: list[dict[str, Any]], registry: dict[str, dict[str, Any]]
) -> Counter[str]:
    """Vérifie la couverture du registre et retourne le nombre de chunks/catégorie."""
    chunk_sources = {chunk["source"] for chunk in chunks}
    missing_sources = chunk_sources - registry.keys()
    if missing_sources:
        raise IngestionDataError(
            "Sources présentes dans les chunks mais absentes du registre : "
            + ", ".join(sorted(missing_sources))
        )

    chunk_categories = Counter(registry[chunk["source"]]["categorie"] for chunk in chunks)
    present_categories = set(chunk_categories)
    absent_categories = CATEGORIES - present_categories
    if absent_categories:
        raise IngestionDataError(
            "Aucune source indexable dans ces catégories : "
            + ", ".join(sorted(absent_categories))
        )

    return chunk_categories


def build_metadata(chunk: dict[str, Any], registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Prépare les métadonnées scalaires acceptées par ChromaDB."""
    document = registry[chunk["source"]]
    metadata: dict[str, Any] = {
        "source": chunk["source"],
        "categorie": document["categorie"],
        "date_ajout": document["date_ajout"],
        "type_original": document["type_original"],
        "chunk_index": chunk["chunk_index"],
        "char_count": chunk["char_count"],
    }
    if "section" in chunk and chunk["section"]:
        metadata["section"] = str(chunk["section"])
    return metadata


def _get_collection(client: Any, rebuild: bool) -> Any:
    """Récupère la collection ou la recrée uniquement sur demande explicite."""
    try:
        client.get_collection(COLLECTION_NAME)
        exists = True
    except Exception:
        exists = False

    if exists and rebuild:
        client.delete_collection(COLLECTION_NAME)

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Chunks institutionnels classés pour le RAG",
            "hnsw:space": "cosine",
            "embedding_model": EMBEDDING_MODEL,
        },
    )


def ingest_all(rebuild: bool = False) -> int:
    """Valide les entrées, calcule les embeddings et les stocke dans ChromaDB."""
    chunks = load_chunks()
    registry = load_registry()
    category_counts = validate_inputs(chunks, registry)

    # Imports différés : --validate-only fonctionne sans avoir installé les paquets lourds.
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Dépendances absentes. Active le venv puis lance : "
            "python -m pip install -r requirements.txt"
        ) from exc

    print(f"Chunks validés : {len(chunks)}")
    print(f"Sources dans le registre : {len(registry)}")
    print("Catégories :")
    for category in sorted(CATEGORIES):
        print(f"  - {category}: {category_counts[category]} chunks")

    print(f"Chargement du modèle d'embedding : {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    vectors = model.encode(
        [chunk["text"] for chunk in chunks],
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = _get_collection(client, rebuild=rebuild)

    for start in range(0, len(chunks), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(chunks))
        batch = chunks[start:end]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["text"] for chunk in batch],
            metadatas=[build_metadata(chunk, registry) for chunk in batch],
            embeddings=vectors[start:end].tolist(),
        )
        print(f"Lot indexé : {end}/{len(chunks)}")

    indexed = collection.count()
    print(f"Indexation terminée : {indexed} chunks dans {CHROMA_PATH}")
    if indexed != len(chunks):
        raise RuntimeError(
            f"ChromaDB contient {indexed} chunks, {len(chunks)} attendus. "
            "Si le corpus a changé, relance avec --rebuild pour retirer les anciens chunks."
        )
    return indexed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Valide les chunks et le registre sans charger ChromaDB ni le modèle.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Supprime puis recrée la collection documents avant indexation.",
    )
    args = parser.parse_args()

    chunks = load_chunks()
    registry = load_registry()
    category_counts = validate_inputs(chunks, registry)
    print(f"Entrées valides : {len(chunks)} chunks, {len({c['source'] for c in chunks})} sources.")
    for category in sorted(CATEGORIES):
        print(f"  - {category}: {category_counts[category]} chunks")

    if args.validate_only:
        print("Validation terminée. Aucune base ChromaDB modifiée.")
        return
    ingest_all(rebuild=args.rebuild)


if __name__ == "__main__":
    main()

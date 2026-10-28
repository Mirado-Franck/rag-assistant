"""Tests rapides des recherches ChromaDB, avec le même modèle d'embedding.

À lancer après l'ingestion, depuis la racine du dépôt :
    python src/ingestion/test_search.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Autorise aussi l'exécution directe indiquée dans le planning :
# python src/ingestion/test_search.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.ingest import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    IngestionDataError,
    load_chunks,
    load_registry,
    validate_inputs,
)


QUERY_CATEGORY = "Règlements"
QUERY_SOURCE = "01_reglement_interieur.txt"


def _build_where(categorie: str | None = None, source: str | None = None) -> dict[str, Any] | None:
    """Construit le filtre ChromaDB sur une catégorie et/ou un document source."""
    clauses: list[dict[str, str]] = []
    if categorie:
        clauses.append({"categorie": categorie})
    if source:
        clauses.append({"source": source})
    if len(clauses) == 1:
        return clauses[0]
    if clauses:
        return {"$and": clauses}
    return None


def search(
    query: str,
    *,
    model: Any,
    collection: Any,
    n_results: int = 3,
    categorie: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Recherche par vecteur et applique éventuellement les filtres metadata."""
    vector = model.encode(
        [query], normalize_embeddings=True, convert_to_numpy=True
    )[0]
    embedding = vector.tolist() if hasattr(vector, "tolist") else list(vector)
    count = collection.count()
    if count == 0:
        raise RuntimeError("La collection ChromaDB est vide. Lance d'abord ingest.py.")

    kwargs: dict[str, Any] = {
        "query_embeddings": [embedding],
        "n_results": min(n_results, count),
    }
    where = _build_where(categorie=categorie, source=source)
    if where:
        kwargs["where"] = where

    result = collection.query(**kwargs)
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    if not documents:
        raise AssertionError(f"Aucun résultat pour la question : {query}")

    # Vérifie concrètement que ChromaDB a appliqué les filtres demandés.
    for metadata in metadatas:
        if categorie and metadata.get("categorie") != categorie:
            raise AssertionError("Le filtre catégorie a retourné une source incorrecte.")
        if source and metadata.get("source") != source:
            raise AssertionError("Le filtre source a retourné un document incorrect.")

    return {"documents": documents, "metadatas": metadatas}


def run_smoke_tests() -> None:
    """Teste une recherche générale et les filtres par catégorie et source."""
    chunks = load_chunks()
    registry = load_registry()
    validate_inputs(chunks, registry)

    if QUERY_SOURCE not in registry:
        raise IngestionDataError(f"La source de test {QUERY_SOURCE} manque au registre.")
    if registry[QUERY_SOURCE]["categorie"] != QUERY_CATEGORY:
        raise IngestionDataError(
            f"La source {QUERY_SOURCE} n'est pas classée {QUERY_CATEGORY} dans le registre."
        )

    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Dépendances absentes. Active le venv et installe requirements.txt."
        ) from exc

    if not CHROMA_PATH.exists():
        raise RuntimeError(f"Base ChromaDB introuvable : {CHROMA_PATH}. Lance ingest.py.")

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception as exc:
        raise RuntimeError(
            f"Collection {COLLECTION_NAME!r} introuvable. Lance ingest.py."
        ) from exc

    model = SentenceTransformer(EMBEDDING_MODEL)
    tests = [
        ("Quelles sont les règles et obligations des étudiants ?", None, None),
        ("Quelles sont les sanctions en cas de fraude ?", QUERY_CATEGORY, None),
        ("Quels sont les droits et devoirs des étudiants ?", None, QUERY_SOURCE),
    ]

    labels = ("Recherche générale", "Filtre catégorie", "Filtre fichier")
    for label, (question, categorie, source) in zip(labels, tests):
        print(f"\n{label} : {question}")
        result = search(
            question,
            model=model,
            collection=collection,
            n_results=3,
            categorie=categorie,
            source=source,
        )
        for rank, (text, metadata) in enumerate(
            zip(result["documents"], result["metadatas"]), start=1
        ):
            print(
                f"  {rank}. [{metadata['categorie']}] {metadata['source']} "
                f"(chunk {metadata['chunk_index']})"
            )
            print(f"     {text[:180].replace(chr(10), ' ')}...")

    print(f"\nTests de recherche réussis. Chunks indexés : {collection.count()}.")


if __name__ == "__main__":
    run_smoke_tests()

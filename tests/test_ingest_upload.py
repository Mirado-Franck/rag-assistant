"""Tests autonomes de l'indexation des uploads (Chroma et modèle simulés)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ingestion import ingest_upload
from src.ingestion.ingest import REGISTRY_PATH as SOURCE_REGISTRY_PATH


class FakeCollection:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, object]] = {}

    def get(self, where: dict[str, str], include: list[str]) -> dict[str, list[object]]:
        matches = [
            (chunk_id, row)
            for chunk_id, row in self.rows.items()
            if row["metadata"]["source"] == where["source"]
        ]
        return {
            "ids": [chunk_id for chunk_id, _row in matches],
            "metadatas": [row["metadata"] for _chunk_id, row in matches],
        }

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, object]],
        embeddings: list[list[float]],
    ) -> None:
        for index, chunk_id in enumerate(ids):
            self.rows[chunk_id] = {
                "document": documents[index],
                "metadata": metadatas[index],
                "embedding": embeddings[index],
            }

    def delete(self, ids: list[str]) -> None:
        for chunk_id in ids:
            self.rows.pop(chunk_id, None)


class EncodedVectors(list):
    def tolist(self) -> list[list[float]]:
        return list(self)


class FakeEmbeddingModel:
    def encode(self, texts: list[str], **_kwargs: object) -> EncodedVectors:
        return EncodedVectors([[0.1, 0.2] for _text in texts])


class UploadIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry_path = Path(self.temp_dir.name) / "documents_registry.json"
        self.registry_path.write_text(
            SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.collection = FakeCollection()
        self.text = (
            "Article 1. Dépôt des dossiers.\n\n"
            + "Les pièces justificatives sont déposées auprès du service compétent "
            "avant la date limite indiquée dans le calendrier officiel. "
        ) * 8

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_indexes_chunks_and_updates_registry_idempotently(self) -> None:
        with (
            patch.object(ingest_upload, "REGISTRY_PATH", self.registry_path),
            patch.object(ingest_upload, "_get_collection", return_value=self.collection),
            patch.object(ingest_upload, "_embedding_model", return_value=FakeEmbeddingModel()),
        ):
            count = ingest_upload.ingest_uploaded_document(
                "abcdef12_test.txt", self.text, "Procédures", pages=2
            )
            first_ids = set(self.collection.rows)
            second_count = ingest_upload.ingest_uploaded_document(
                "abcdef12_test.txt", self.text, "Règlements", pages=2
            )

        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.assertGreater(count, 0)
        self.assertEqual(second_count, count)
        self.assertEqual(set(self.collection.rows), first_ids)
        self.assertEqual(registry["abcdef12_test.txt"]["chunks_count"], count)
        self.assertEqual(registry["abcdef12_test.txt"]["categorie"], "Règlements")
        self.assertEqual(registry["abcdef12_test.txt"]["pages"], 2)
        self.assertTrue(
            all(row["metadata"]["source"] == "abcdef12_test.txt" for row in self.collection.rows.values())
        )
        self.assertTrue(
            all(row["metadata"]["categorie"] == "Règlements" for row in self.collection.rows.values())
        )

    def test_rejects_short_text_before_touching_chroma(self) -> None:
        with patch.object(ingest_upload, "_get_collection") as get_collection:
            with self.assertRaises(ingest_upload.UploadedDocumentIngestionError):
                ingest_upload.ingest_uploaded_document(
                    "abcdef12_test.txt", "Trop court.", "Procédures"
                )
        get_collection.assert_not_called()


if __name__ == "__main__":
    unittest.main()

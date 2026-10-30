"""Validation hors-ligne des fichiers de préparation Jour 6 (aucun modèle requis)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.ingestion.ingest import load_chunks, load_registry

ROOT = Path(__file__).resolve().parents[1]


class Day6EvaluationAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads((ROOT / "tests" / "rag_stress_cases.json").read_text(encoding="utf-8"))
        cls.registry = load_registry()
        cls.indexed_sources = {chunk["source"] for chunk in load_chunks()}
        cls.template = (ROOT / "tests" / "evaluation_jour7_template.md").read_text(encoding="utf-8")

    def test_stress_suite_has_30_unique_nonempty_cases(self) -> None:
        self.assertEqual(len(self.cases), 30)
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(set(ids)), 30)
        self.assertTrue(all(case["question"].strip() for case in self.cases))

    def test_expected_sources_cover_entire_indexed_corpus(self) -> None:
        expected_sources = {
            source for case in self.cases for source in case["expected_sources"]
        }
        self.assertEqual(expected_sources, self.indexed_sources)
        for case in self.cases:
            if case.get("source_file"):
                self.assertIn(case["source_file"], self.indexed_sources, case["id"])
            if case.get("category") and case.get("source_file"):
                self.assertEqual(
                    self.registry[case["source_file"]]["categorie"],
                    case["category"],
                    case["id"],
                )

    def test_day7_template_has_20_classification_and_30_rag_rows(self) -> None:
        self.assertEqual(sum(f"| DOC{i:02d} |" in self.template for i in range(1, 21)), 20)
        self.assertEqual(sum(f"| RAG{i:02d} |" in self.template for i in range(1, 31)), 30)


if __name__ == "__main__":
    unittest.main()

"""Vérifications de contrat HTTP et de cas limites de l'API.

Démarre l'API dans un autre terminal, puis lance :
    python tests/api_smoke.py
Pour ajouter une requête RAG réelle (nécessite ChromaDB et Ollama actifs) :
    python tests/api_smoke.py --check-rag
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import requests


class SmokeChecks:
    def __init__(self, base_url: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.passed = 0
        self.failed = 0

    def request(
        self,
        label: str,
        method: str,
        path: str,
        expected_status: int,
        **kwargs: Any,
    ) -> requests.Response | None:
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            self.failed += 1
            print(f"ÉCHEC  {label}: API inaccessible ({exc})")
            return None

        if response.status_code == expected_status:
            self.passed += 1
            print(f"OK     {label}: HTTP {response.status_code}")
        else:
            self.failed += 1
            print(
                f"ÉCHEC  {label}: HTTP {response.status_code}, "
                f"attendu {expected_status}; réponse={response.text[:500]}"
            )
        return response

    def run(self, check_rag: bool = False) -> int:
        self.request("GET /", "GET", "/", 200)
        self.request("GET /health", "GET", "/health", 200)
        health = self.request("GET /api/health", "GET", "/api/health", 200)
        if health is not None and health.status_code == 200:
            body = health.json()
            required = {"status", "modele_llm", "modele_embedding", "nb_documents", "nb_chunks", "categories"}
            missing = required - body.keys()
            if missing:
                self.failed += 1
                print(f"ÉCHEC  schéma /api/health incomplet, manque {sorted(missing)}")
            else:
                self.passed += 1
                print("OK     schéma /api/health")

        categories = self.request("GET /api/categories", "GET", "/api/categories", 200)
        if categories is not None and categories.status_code == 200:
            body = categories.json()
            if isinstance(body.get("categories"), dict) and isinstance(body.get("total_documents"), int):
                self.passed += 1
                print("OK     schéma /api/categories")
            else:
                self.failed += 1
                print("ÉCHEC  schéma /api/categories invalide")

        documents = self.request("GET /api/documents", "GET", "/api/documents", 200)
        if documents is not None and documents.status_code == 200:
            if isinstance(documents.json(), list):
                self.passed += 1
                print("OK     schéma /api/documents")
            else:
                self.failed += 1
                print("ÉCHEC  /api/documents ne renvoie pas une liste")

        self.request("GET /api/documents catégorie inconnue", "GET", "/api/documents?category=__inconnue__", 400)
        self.request(
            "POST /api/query question vide",
            "POST",
            "/api/query",
            422,
            json={"question": ""},
        )
        self.request(
            "POST /api/query catégorie inconnue",
            "POST",
            "/api/query",
            400,
            json={"question": "Question de validation", "category": "__inconnue__"},
        )
        self.request(
            "POST /api/confirm catégorie inconnue",
            "POST",
            "/api/confirm",
            400,
            json={"file_id": "0badcafe", "categorie": "__inconnue__"},
        )
        self.request(
            "POST /api/confirm identifiant invalide",
            "POST",
            "/api/confirm",
            400,
            json={"file_id": "pas-un-id", "categorie": "Règlements"},
        )
        self.request(
            "POST /api/confirm fichier temporaire absent",
            "POST",
            "/api/confirm",
            404,
            json={"file_id": "0badcafe", "categorie": "Règlements"},
        )
        self.request(
            "POST /api/upload extension interdite",
            "POST",
            "/api/upload",
            400,
            files={"file": ("test.html", b"<p>test</p>", "text/html")},
        )
        self.request(
            "POST /api/upload PDF corrompu",
            "POST",
            "/api/upload",
            422,
            files={"file": ("corrompu.pdf", b"ceci n'est pas un PDF", "application/pdf")},
        )

        if check_rag:
            started = time.perf_counter()
            response = self.request(
                "POST /api/query RAG réel (règlement intérieur)",
                "POST",
                "/api/query",
                200,
                json={
                    "question": "Quels sont les droits et devoirs des étudiants ?",
                    "n_results": 4,
                    "category": "Règlements",
                    "source_file": "01_reglement_interieur.txt",
                },
            )
            elapsed = round((time.perf_counter() - started) * 1000, 1)
            if response is not None and response.status_code == 200:
                body = response.json()
                if body.get("sources") and all(
                    source.get("fichier") == "01_reglement_interieur.txt"
                    and source.get("categorie") == "Règlements"
                    for source in body["sources"]
                ):
                    self.passed += 1
                    print(f"OK     filtre fichier + catégorie; durée HTTP observée {elapsed} ms")
                else:
                    self.failed += 1
                    print("ÉCHEC  le RAG n'a pas respecté les filtres demandés")

        print(f"\nBilan : {self.passed} réussis, {self.failed} échecs.")
        return 0 if self.failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument(
        "--check-rag",
        action="store_true",
        help="Exécute également une requête réelle; nécessite ChromaDB, les embeddings et Ollama.",
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout doit être positif.")
    return SmokeChecks(args.base_url, args.timeout).run(check_rag=args.check_rag)


if __name__ == "__main__":
    raise SystemExit(main())

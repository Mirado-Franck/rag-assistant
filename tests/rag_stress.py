"""Benchmark séquentiel des 30 cas RAG via l'API locale.

Lancer depuis la racine après avoir démarré l'API et Ollama :
    python tests/rag_stress.py
Essai court :
    python tests/rag_stress.py --limit 3
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = PROJECT_ROOT / "tests" / "rag_stress_cases.json"
RESULTS_DIR = PROJECT_ROOT / "tests" / "results"
REQUIRED_RESPONSE_KEYS = {
    "question", "reponse", "sources", "filtre", "temps_ms", "nb_chunks_trouves"
}


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(fraction * len(ordered)) - 1)], 1)


def load_cases() -> list[dict[str, Any]]:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) != 30:
        raise ValueError(f"{CASES_PATH} doit contenir exactement 30 cas.")
    ids = [case.get("id") for case in cases]
    if len(set(ids)) != len(ids) or any(not case.get("question") for case in cases):
        raise ValueError("Chaque cas doit avoir un id unique et une question non vide.")
    return cases


def run(base_url: str, limit: int | None, timeout: float, pause: float) -> dict[str, Any]:
    cases = load_cases()
    if limit is not None:
        cases = cases[:limit]

    results: list[dict[str, Any]] = []
    wall_times: list[float] = []
    pipeline_times: list[float] = []
    source_checks: list[bool] = []

    session = requests.Session()
    for position, case in enumerate(cases, start=1):
        payload: dict[str, Any] = {
            "question": case["question"],
            "n_results": 4,
        }
        if case.get("category"):
            payload["category"] = case["category"]
        if case.get("source_file"):
            payload["source_file"] = case["source_file"]

        started = time.perf_counter()
        record: dict[str, Any] = {
            "id": case["id"],
            "type": case.get("type"),
            "request": payload,
            "expected_sources": case.get("expected_sources", []),
            "should_refuse": case.get("should_refuse", False),
        }
        try:
            response = session.post(
                f"{base_url.rstrip('/')}/api/query",
                json=payload,
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            record["http_status"] = response.status_code
            record["wall_time_ms"] = round(elapsed_ms, 1)
            if response.status_code == 200:
                body = response.json()
                missing_keys = REQUIRED_RESPONSE_KEYS - body.keys()
                if missing_keys:
                    raise ValueError(f"Réponse API incomplète : {sorted(missing_keys)}")
                sources = body.get("sources") or []
                actual_sources = [str(source.get("fichier", "")) for source in sources]
                expected_sources = case.get("expected_sources", [])
                record.update({
                    "answer": body.get("reponse"),
                    "sources": sources,
                    "filter_label": body.get("filtre"),
                    "chunks_found": body.get("nb_chunks_trouves"),
                    "pipeline_time_ms": body.get("temps_ms"),
                    "expected_source_hit": (
                        bool(set(expected_sources) & set(actual_sources))
                        if expected_sources else None
                    ),
                })
                if isinstance(body.get("temps_ms"), (int, float)):
                    pipeline_times.append(float(body["temps_ms"]))
                if expected_sources:
                    source_checks.append(bool(set(expected_sources) & set(actual_sources)))
            else:
                try:
                    record["error"] = response.json()
                except ValueError:
                    record["error"] = response.text[:1000]
        except (requests.RequestException, ValueError) as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            record["wall_time_ms"] = round(elapsed_ms, 1)
            record["error"] = str(exc)

        wall_times.append(float(record["wall_time_ms"]))
        results.append(record)
        state = "OK" if record.get("http_status") == 200 and "error" not in record else "ERREUR"
        print(f"[{position:02d}/{len(cases):02d}] {case['id']} {state} — {record['wall_time_ms']} ms")
        if pause > 0 and position < len(cases):
            time.sleep(pause)

    successful = sum(1 for result in results if result.get("http_status") == 200 and "error" not in result)
    summary = {
        "run_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "base_url": base_url,
        "cases_total": len(results),
        "http_success": successful,
        "http_failure": len(results) - successful,
        "wall_time_mean_ms": round(statistics.mean(wall_times), 1) if wall_times else None,
        "wall_time_median_ms": round(statistics.median(wall_times), 1) if wall_times else None,
        "wall_time_p95_ms": percentile(wall_times, 0.95),
        "pipeline_time_mean_ms": round(statistics.mean(pipeline_times), 1) if pipeline_times else None,
        "expected_source_hits": sum(source_checks),
        "expected_source_checks": len(source_checks),
    }
    return {"summary": summary, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--limit", type=int, help="N'exécute que les N premiers cas (diagnostic rapide).")
    parser.add_argument("--timeout", type=float, default=180.0, help="Timeout par question, en secondes.")
    parser.add_argument("--pause", type=float, default=0.25, help="Pause entre deux questions (secondes).")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit doit être supérieur ou égal à 1.")

    try:
        report = run(args.base_url, args.limit, args.timeout, args.pause)
    except requests.RequestException as exc:
        print(f"API inaccessible à {args.base_url}: {exc}")
        print("Démarre d'abord uvicorn et vérifie que l'API répond sur /api/health.")
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Configuration de test invalide : {exc}")
        return 2

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = RESULTS_DIR / f"rag_stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nSynthèse :")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Résultats détaillés : {output.relative_to(PROJECT_ROOT)}")
    return 0 if report["summary"]["http_failure"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

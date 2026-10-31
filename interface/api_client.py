"""
api_client.py — Client de l'API FastAPI (partie B1, Jour 5 rattrapage + Jour 6).

Les appels HTTP sont faits par le serveur Streamlit, pas par le navigateur :
l'adresse 127.0.0.1 reste donc locale à la machine. Toute erreur réseau ou
HTTP est transformée en ApiError avec un message lisible : les pages l'affichent
sans faire planter Streamlit.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from config import DEFAULT_API_URL, SEUIL_CONFIANCE_HAUTE, SEUIL_CONFIANCE_MOYENNE

API_URL = (
    os.environ.get("DOCURAG_API_URL") or os.environ.get("DOCUCLASSIF_API_URL") or DEFAULT_API_URL
).rstrip("/")  # ancien nom accepté

# Délais (secondes). L'upload et la requête RAG peuvent dépasser une minute
# quand Ollama tourne sur CPU.
TIMEOUT_RAPIDE = 4
TIMEOUT_LECTURE = 15
TIMEOUT_UPLOAD = 240
TIMEOUT_CONFIRM = 120
TIMEOUT_QUERY = 300

MESSAGE_API_DOWN = (
    "L'API ne répond pas. Lancez le backend (start.bat, ou "
    "uvicorn src.api.main:app --port 8000), puis réessayez."
)


class ApiError(Exception):
    """Erreur d'appel à l'API, avec un message prêt à afficher."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def confidence_band(value: float) -> str:
    """Cas d'affichage selon la confiance : 'haute', 'moyenne' ou 'faible'."""
    if value > SEUIL_CONFIANCE_HAUTE:
        return "haute"
    if value >= SEUIL_CONFIANCE_MOYENNE:
        return "moyenne"
    return "faible"


def normalize_alternatives(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Uniformise les alternatives : {'categorie', 'probabilite'}, triées par probabilité."""
    result = []
    for item in items or []:
        if not isinstance(item, dict) or not item.get("categorie"):
            continue
        probabilite = item.get("probabilite", item.get("score", 0.0))
        try:
            probabilite = float(probabilite)
        except (TypeError, ValueError):
            probabilite = 0.0
        result.append({"categorie": str(item["categorie"]), "probabilite": probabilite})
    return sorted(result, key=lambda a: a["probabilite"], reverse=True)


def _error_from_response(response: requests.Response) -> str:
    """Extrait un message lisible d'une réponse d'erreur (formats FastAPI et maison)."""
    try:
        payload = response.json()
    except ValueError:
        return f"Erreur HTTP {response.status_code} de l'API."
    detail = payload.get("erreur", payload.get("detail", "")) if isinstance(payload, dict) else payload
    if isinstance(detail, list):  # erreurs de validation FastAPI (422)
        messages = [str(item.get("msg", item)) for item in detail if isinstance(item, dict)]
        return "Requête invalide : " + "; ".join(messages) if messages else "Requête invalide."
    if isinstance(detail, str) and detail:
        return detail
    return f"Erreur HTTP {response.status_code} de l'API."


def _request(method: str, path: str, timeout: float, **kwargs: Any) -> Any:
    url = API_URL + path
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.exceptions.ConnectionError as exc:
        raise ApiError(MESSAGE_API_DOWN) from exc
    except requests.exceptions.Timeout as exc:
        raise ApiError(
            "L'API met trop de temps à répondre. Le modèle est peut-être occupé : réessayez."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ApiError(f"Erreur de communication avec l'API : {exc}") from exc

    if response.status_code >= 400:
        raise ApiError(_error_from_response(response), response.status_code)
    try:
        return response.json()
    except ValueError as exc:
        raise ApiError("Réponse de l'API illisible (JSON attendu).") from exc


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def health() -> dict[str, Any]:
    """GET /api/health — état de l'API, nombre de documents et de chunks."""
    return _request("GET", "/api/health", TIMEOUT_RAPIDE)


def categories() -> dict[str, Any]:
    """GET /api/categories — {'categories': {nom: {'nb_documents', 'documents'}}, 'total_documents'}."""
    return _request("GET", "/api/categories", TIMEOUT_LECTURE)


def documents(category: str | None = None) -> list[dict[str, Any]]:
    """GET /api/documents — liste des documents confirmés (filename, categorie, chunks_count…)."""
    params = {"category": category} if category else None
    return _request("GET", "/api/documents", TIMEOUT_LECTURE, params=params)


def upload(filename: str, content: bytes) -> dict[str, Any]:
    """POST /api/upload — extraction du texte et classification proposée."""
    mime = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
    }.get(os.path.splitext(filename)[1].lower(), "application/octet-stream")
    return _request(
        "POST", "/api/upload", TIMEOUT_UPLOAD, files={"file": (filename, content, mime)}
    )


def confirm(file_id: str, categorie: str) -> dict[str, Any]:
    """POST /api/confirm — confirme la catégorie et lance l'indexation."""
    return _request(
        "POST", "/api/confirm", TIMEOUT_CONFIRM,
        json={"file_id": file_id, "categorie": categorie},
    )


def query(
    question: str,
    n_results: int = 4,
    category: str | None = None,
    source_file: str | None = None,
) -> dict[str, Any]:
    """POST /api/query — question RAG avec filtres facultatifs."""
    body: dict[str, Any] = {"question": question, "n_results": n_results}
    if category:
        body["category"] = category
    if source_file:
        body["source_file"] = source_file
    return _request("POST", "/api/query", TIMEOUT_QUERY, json=body)

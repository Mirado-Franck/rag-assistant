"""
nav.py — Navigation et état système de DocuRAG.

La navigation elle-même est native (st.navigation, défini dans app.py) : le
sidebar reste le même élément d'une page à l'autre, donc il ne clignote pas.
Ce module fournit :
  - page_setup() : état de l'API pour chaque page (sans reconfigurer la page) ;
  - sidebar_status() : encadré « Système » (modèle, moteur, état de l'API).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

import api_client
import theme

INTERFACE = Path(__file__).resolve().parent
PAGE_UPLOAD = str(INTERFACE / "views" / "1_Upload.py")
PAGE_QUESTIONS = str(INTERFACE / "views" / "2_Questions.py")
PAGE_DASHBOARD = str(INTERFACE / "views" / "3_Dashboard.py")


@st.cache_data(ttl=5, show_spinner=False)
def api_state() -> tuple[dict | None, str | None]:
    """État de l'API mis en cache 5 s : (données /api/health, message d'erreur)."""
    try:
        return api_client.health(), None
    except api_client.ApiError as exc:
        return None, exc.message


def page_setup() -> tuple[dict | None, str | None]:
    """À appeler en tête de chaque page. Renvoie (health, erreur)."""
    return api_state()


def sidebar_status(health: dict | None) -> None:
    """Encadré « Système » du sidebar, avec l'état réel de l'API."""
    theme.sidebar_label("Système")
    if health is not None:
        theme.html(f'<div class="dc-side-badge">{theme.badge("100 % offline")}</div>')
        mode = "API connectée"
    else:
        theme.html(f'<div class="dc-side-badge">{theme.badge("API hors ligne", error=True)}</div>')
        mode = "API hors ligne"
    rows = [
        ("Modèle", health.get("modele_llm", "—") if health else "—"),
        ("Moteur", "Ollama"),
        ("Base", "ChromaDB"),
        ("Mode", mode),
    ]
    theme.sidebar_system(
        rows,
        "Aucune donnée n'est envoyée à l'extérieur.<br>Fonctionne sans connexion internet.",
    )

"""
nav.py — Sidebar commune à toutes les pages (partie B1).

La sidebar remplace la navigation multi-pages par défaut de Streamlit :
plus sobre, alignée à gauche, avec état actif — façon ChatGPT.
"""

from __future__ import annotations

import streamlit as st

import theme
from data_mock import APP_NAME, APP_VERSION

NAV = [
    ("accueil", "Accueil", "home", "app.py"),
    ("upload", "Upload", "upload_file", "pages/1_Upload.py"),
    ("questions", "Questions", "forum", "pages/2_Questions.py"),
    ("dashboard", "Tableau de bord", "monitoring", "pages/3_Dashboard.py"),
]

SYSTEM_ROWS = [
    ("Modèle", "Llama 3.2 3B"),
    ("Moteur", "Ollama (local)"),
    ("Base", "ChromaDB (local)"),
    ("Mode", "Maquette"),
]

SYSTEM_NOTE = (
    "Aucune donnée n'est envoyée à l'extérieur.<br>"
    "Fonctionne sans connexion internet."
)


def _button(label: str, *, key: str, primary: bool = False, ico: str | None = None):
    """st.button compatible entre versions de Streamlit (width / icon)."""
    kwargs = {"key": key, "type": "primary" if primary else "secondary"}
    for extra in ({"width": "stretch"}, {"use_container_width": True}):
        try:
            if ico:
                return st.button(label, icon=f":material/{ico}:", **kwargs, **extra)
            return st.button(label, **kwargs, **extra)
        except TypeError:
            continue
    return st.button(label, **kwargs)


def setup(page_key: str, page_title: str, page_icon: str = "◼") -> None:
    """Config + CSS + sidebar. À appeler en tout premier dans chaque page."""
    st.set_page_config(
        page_title=f"{page_title} · {APP_NAME}",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    theme.inject()

    with st.sidebar:
        theme.sidebar_brand(APP_NAME, APP_VERSION)
        theme.sidebar_label("Navigation")
        for key, label, ico, target in NAV:
            clicked = _button(label, key=f"nav_{key}", primary=(key == page_key), ico=ico)
            if clicked and key != page_key:
                st.switch_page(target)

        theme.sidebar_label("Système")
        theme.html(theme.badge("100 % offline"))
        theme.html('<div style="height:.4rem"></div>')
        theme.sidebar_system(SYSTEM_ROWS, SYSTEM_NOTE)

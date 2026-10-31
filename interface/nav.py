"""
nav.py — Sidebar commune à toutes les pages (partie B1).

La sidebar remplace la navigation multi-pages par défaut de Streamlit :
plus sobre, alignée à gauche, avec état actif. Elle affiche l'état réel de
l'API (/api/health) : la pastille « 100 % offline » ne reste verte que si le
backend local répond.
"""

from __future__ import annotations

import streamlit as st

import api_client
import theme
from config import APP_NAME, APP_VERSION

NAV = [
    ("accueil", "Accueil", "home", "app.py"),
    ("upload", "Upload", "upload_file", "pages/1_Upload.py"),
    ("questions", "Questions", "forum", "pages/2_Questions.py"),
    ("dashboard", "Tableau de bord", "monitoring", "pages/3_Dashboard.py"),
]


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


@st.cache_data(ttl=5, show_spinner=False)
def api_state() -> tuple[dict | None, str | None]:
    """État de l'API mis en cache 5 s : (données /api/health, message d'erreur)."""
    try:
        return api_client.health(), None
    except api_client.ApiError as exc:
        return None, exc.message


def setup(page_key: str, page_title: str, page_icon: str = "◼") -> tuple[dict | None, str | None]:
    """Config + CSS + sidebar. À appeler en tout premier dans chaque page.

    Renvoie (health, erreur) pour que la page sache si l'API répond.
    """
    st.set_page_config(
        page_title=f"{page_title} · {APP_NAME}",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    theme.inject()
    health, erreur = api_state()

    with st.sidebar:
        theme.sidebar_brand(APP_NAME, APP_VERSION)
        theme.sidebar_label("Navigation")
        for key, label, ico, target in NAV:
            clicked = _button(label, key=f"nav_{key}", primary=(key == page_key), ico=ico)
            if clicked and key != page_key:
                st.switch_page(target)

        theme.sidebar_label("Système")
        if health is not None:
            theme.html(theme.badge("100 % offline"))
            mode = "API connectée"
        else:
            theme.html(theme.badge("API hors ligne", error=True))
            mode = "API hors ligne"
        theme.html('<div style="height:.4rem"></div>')
        rows = [
            ("Modèle", health.get("modele_llm", "—") if health else "—"),
            ("Moteur", "Ollama (local)"),
            ("Base", "ChromaDB (local)"),
            ("Mode", mode),
        ]
        theme.sidebar_system(
            rows,
            "Aucune donnée n'est envoyée à l'extérieur.<br>"
            "Fonctionne sans connexion internet.",
        )
    return health, erreur

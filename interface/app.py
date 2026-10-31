"""
app.py — Point d'entrée de DocuRAG, assistant RAG documentaire.

Lancement :  streamlit run interface/app.py
L'API doit tourner (par défaut http://127.0.0.1:8000) pour afficher les données réelles.

La navigation est gérée par st.navigation : le sidebar reste en place d'une page
à l'autre, ce qui évite le clignotement des versions précédentes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -> interface/

import streamlit as st

import api_client
import nav
import theme
from config import APP_NAME, APP_TAGLINE, APP_VERSION, CATEGORIES

# Configuration de la page : une seule fois, dans l'entrée.
st.set_page_config(
    page_title=f"{APP_NAME} · Assistant RAG",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)
theme.inject()


def accueil() -> None:
    health, erreur = nav.page_setup()

    theme.page_header(APP_NAME, APP_TAGLINE, eyebrow="Accueil")
    if health is not None:
        etat = (
            theme.badge("100 % offline")
            + theme.badge(f"API connectée · {health.get('nb_documents', 0)} document(s)")
        )
    else:
        etat = theme.badge("API hors ligne", error=True)
    theme.html(
        '<div style="display:flex;gap:.4rem;flex-wrap:wrap;margin:.2rem 0 .4rem 0">' + etat + "</div>"
    )

    theme.section("Ce que fait DocuRAG", "4 modules")
    theme.card_grid(
        [
            (
                "Questions & réponses sourcées",
                "Interrogez la base documentaire en langage naturel. Filtrez par catégorie "
                "ou par fichier : chaque réponse cite les extraits utilisés.",
                "chat",
                "teal",
            ),
            (
                "Ajout de documents",
                "Un PDF, DOCX ou TXT est analysé, puis rangé dans l'une des 5 catégories. "
                "Vous validez la catégorie avant l'indexation.",
                "upload",
                "indigo",
            ),
            (
                "Souveraineté des données",
                "Tout s'exécute en local : modèle via Ollama, base ChromaDB. Aucune donnée "
                "ne quitte la machine, aucune connexion internet requise.",
                "shield",
                "green",
            ),
            (
                "Tableau de bord",
                "Suivez la répartition des documents par catégorie, le nombre de chunks "
                "indexés et les documents en attente d'indexation.",
                "chart",
                "orange",
            ),
        ],
        per_row=2,
    )

    counts: dict[str, int] = {}
    if health is not None:
        try:
            counts = {
                nom: info["nb_documents"]
                for nom, info in api_client.categories()["categories"].items()
            }
        except api_client.ApiError:
            counts = {}
    total = health.get("nb_documents", 0) if health else None
    hint = f"{total} document(s) confirmé(s)" if total is not None else "API indisponible"
    theme.section("Les 5 catégories", hint)
    chips = []
    for cat in CATEGORIES:
        nombre = counts.get(cat["label"])
        suffixe = f"· {cat['desc']}" + (f" · {nombre} doc." if nombre is not None else "")
        chips.append((cat["label"], suffixe, theme.category_icon_name(cat["label"])))
    theme.chips(chips)

    theme.section("Démarrage rapide", "3 étapes")
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        theme.html(theme.card("1 · Ajouter", "Déposez un PDF, un DOCX ou un TXT. Le texte est extrait puis classé.", "upload", "indigo"))
    with col2:
        theme.html(theme.card("2 · Valider", "Vérifiez la catégorie proposée et son score de confiance, puis confirmez.", "check", "teal"))
    with col3:
        theme.html(theme.card("3 · Interroger", "Posez vos questions en français ; les réponses citent leurs sources.", "search", "orange"))

    theme.divider()
    left, right, _ = st.columns([1, 1, 2], gap="small")
    with left:
        if theme.button("Ajouter un document", primary=True, full=True):
            st.switch_page(nav.PAGE_UPLOAD)
    with right:
        if theme.button("Poser une question", full=True):
            st.switch_page(nav.PAGE_QUESTIONS)

    if erreur:
        theme.error_box(erreur)


def build_navigation():
    pages = [
        st.Page(accueil, title="Accueil", icon=":material/home:", default=True),
        st.Page(nav.PAGE_UPLOAD, title="Ajouter", icon=":material/upload_file:"),
        st.Page(nav.PAGE_QUESTIONS, title="Questions", icon=":material/forum:"),
        st.Page(nav.PAGE_DASHBOARD, title="Tableau de bord", icon=":material/monitoring:"),
    ]
    return st.navigation(pages, position="sidebar")


with st.sidebar:
    theme.sidebar_brand(APP_NAME, APP_VERSION)
    health, _erreur = nav.api_state()
    nav.sidebar_status(health)

build_navigation().run()

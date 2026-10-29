"""
app.py — Accueil de DocuClassif AI (Jour 3, partie B1).

Lancement :  streamlit run interface/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -> interface/

import streamlit as st

import nav
import theme
from data_mock import APP_NAME, APP_TAGLINE, CATEGORIES, STATS

nav.setup("accueil", "Accueil", "◼")

# ---------------------------------------------------------------------------
# En-tête
# ---------------------------------------------------------------------------
theme.page_header(
    APP_NAME,
    APP_TAGLINE,
    eyebrow="Accueil",
)
theme.html(
    '<div style="display:flex;gap:.4rem;flex-wrap:wrap;margin:.2rem 0 .4rem 0">'
    + theme.badge("100 % offline")
    + theme.badge("Maquette · Jour 3", warn=True)
    + "</div>"
)

# ---------------------------------------------------------------------------
# Fonctionnalités
# ---------------------------------------------------------------------------
theme.section("Ce que fait la plateforme", "4 modules")
theme.card_grid(
    [
        (
            "Classification automatique",
            "Un document PDF ou Word est classé dans l'une des 5 catégories "
            "institutionnelles, avec un score de confiance. La classification doit "
            "toujours être confirmée par un humain.",
            "upload",
        ),
        (
            "Questions & réponses sourcées",
            "Interrogez la base documentaire en langage naturel. Filtrez par catégorie "
            "ou par fichier : chaque réponse cite les extraits utilisés.",
            "chat",
        ),
        (
            "Souveraineté des données",
            "Tout s'exécute en local : modèle via Ollama, base ChromaDB. Aucune donnée "
            "ne quitte la machine, aucune connexion internet requise.",
            "shield",
        ),
        (
            "Tableau de bord",
            "Suivez la répartition des documents par catégorie, l'historique des "
            "classifications et les statistiques d'utilisation.",
            "chart",
        ),
    ],
    per_row=2,
)

# ---------------------------------------------------------------------------
# Catégories
# ---------------------------------------------------------------------------
theme.section("Les 5 catégories", f"{STATS['documents']} documents indexés")
theme.chips([(c["label"], f"· {c['desc']}", "file") for c in CATEGORIES])

# ---------------------------------------------------------------------------
# Démarrage rapide
# ---------------------------------------------------------------------------
theme.section("Démarrage rapide", "3 étapes")
col1, col2, col3 = st.columns(3, gap="small")
with col1:
    theme.html(
        theme.card(
            "1 · Uploader",
            "Déposez un PDF ou un DOCX. Le texte est extrait puis découpé en chunks.",
            "upload",
        )
    )
with col2:
    theme.html(
        theme.card(
            "2 · Valider",
            "Vérifiez la catégorie proposée et son score de confiance, puis confirmez.",
            "check",
        )
    )
with col3:
    theme.html(
        theme.card(
            "3 · Interroger",
            "Posez vos questions en français ; les réponses citent leurs sources.",
            "search",
        )
    )

theme.divider()

# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------
left, right, _ = st.columns([1, 1, 2], gap="small")
with left:
    if theme.button("Uploader un document", primary=True, full=True):
        st.switch_page("pages/1_Upload.py")
with right:
    if theme.button("Poser une question", full=True):
        st.switch_page("pages/2_Questions.py")

st.caption(
    "Maquette — les données affichées sont simulées. Connexion au backend prévue au Jour 5."
)

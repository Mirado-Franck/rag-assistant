"""
app.py — Accueil de DocuClassif AI (partie B1, Jour 6).

Lancement :  streamlit run interface/app.py
L'API doit tourner (par défaut http://127.0.0.1:8000) pour afficher les chiffres réels.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -> interface/

import streamlit as st

import api_client
import nav
import theme
from config import APP_NAME, APP_TAGLINE, CATEGORIES

health, erreur = nav.setup("accueil", "Accueil", "◼")

# ---------------------------------------------------------------------------
# En-tête
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Fonctionnalités
# ---------------------------------------------------------------------------
theme.section("Ce que fait la plateforme", "4 modules")
theme.card_grid(
    [
        (
            "Classification automatique",
            "Un document PDF, DOCX ou TXT est classé dans l'une des 5 catégories "
            "institutionnelles, avec un score de confiance. La classification doit "
            "toujours être confirmée par un humain.",
            "upload",
            "indigo",
        ),
        (
            "Questions & réponses sourcées",
            "Interrogez la base documentaire en langage naturel. Filtrez par catégorie "
            "ou par fichier : chaque réponse cite les extraits utilisés.",
            "chat",
            "teal",
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

# ---------------------------------------------------------------------------
# Catégories (volumes réels si l'API répond)
# ---------------------------------------------------------------------------
counts: dict[str, int] = {}
if health is not None:
    try:
        counts = {nom: info["nb_documents"] for nom, info in api_client.categories()["categories"].items()}
    except api_client.ApiError:
        counts = {}
total = health.get("nb_documents", 0) if health else None
hint = f"{total} document(s) confirmé(s)" if total is not None else "API indisponible"
theme.section("Les 5 catégories", hint)
chips = []
for cat in CATEGORIES:
    nombre = counts.get(cat["label"])
    suffixe = f"· {cat['desc']}" + (f" · {nombre} doc." if nombre is not None else "")
    chips.append((cat["label"], suffixe, "file"))
theme.chips(chips)

# ---------------------------------------------------------------------------
# Démarrage rapide
# ---------------------------------------------------------------------------
theme.section("Démarrage rapide", "3 étapes")
col1, col2, col3 = st.columns(3, gap="small")
with col1:
    theme.html(
        theme.card(
            "1 · Uploader",
            "Déposez un PDF, un DOCX ou un TXT. Le texte est extrait puis classé.",
            "upload",
            "indigo",
        )
    )
with col2:
    theme.html(
        theme.card(
            "2 · Valider",
            "Vérifiez la catégorie proposée et son score de confiance, puis confirmez.",
            "check",
            "teal",
        )
    )
with col3:
    theme.html(
        theme.card(
            "3 · Interroger",
            "Posez vos questions en français ; les réponses citent leurs sources.",
            "search",
            "orange",
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

if erreur:
    theme.error_box(erreur)

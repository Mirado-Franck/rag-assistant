"""
3_Dashboard.py — Tableau de bord (partie B1, Jour 6).

Statistiques réelles lues depuis l'API : /api/categories, /api/documents, /api/health.
L'API ne fournit pas d'historique des questions ni des classifications : ces
indicateurs ne sont donc pas affichés (plutôt que d'être inventés).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # -> interface/

import altair as alt
import pandas as pd
import streamlit as st

import api_client
import nav
import theme
from config import CATEGORIES

health, _erreur_api = nav.setup("dashboard", "Tableau de bord", "◼")

CATEGORY_NAMES = [c["label"] for c in CATEGORIES]

# ---------------------------------------------------------------------------
# Données réelles
# ---------------------------------------------------------------------------
erreur = None
documents: list[dict] = []
categories: dict = {}
try:
    documents = api_client.documents()
    categories = api_client.categories()["categories"]
except api_client.ApiError as exc:
    erreur = exc.message

# ---------------------------------------------------------------------------
# En-tête
# ---------------------------------------------------------------------------
head_l, head_r = st.columns([3, 1], gap="small")
with head_l:
    theme.page_header(
        "Tableau de bord",
        "Vue d'ensemble de la base documentaire, lue en direct depuis l'API locale.",
        eyebrow="Étape 3",
    )
with head_r:
    st.write("")
    if documents:
        csv = pd.DataFrame(documents).to_csv(index=False).encode("utf-8")
        st.download_button(
            "Exporter (CSV)",
            data=csv,
            file_name="docuclassif_documents.csv",
            mime="text/csv",
            width="stretch",
        )
    else:
        theme.button("Actualiser", full=True)

if erreur:
    theme.error_box(erreur)
    st.stop()

# ---------------------------------------------------------------------------
# Indicateurs clés
# ---------------------------------------------------------------------------
total_docs = len(documents)
total_chunks = health.get("nb_chunks", 0) if health else sum(d.get("chunks_count", 0) for d in documents)
non_indexes = sum(1 for d in documents if not d.get("chunks_count"))
couvertes = sum(1 for nom in CATEGORY_NAMES if categories.get(nom, {}).get("nb_documents", 0) > 0)
moyenne = round(total_chunks / total_docs) if total_docs else 0

theme.section("Statistiques générales", "données de l'API")
theme.stat_cards(
    [
        {"label": "Documents", "value": total_docs, "delta": f"{couvertes} / 5 catégories couvertes", "tone": "indigo"},
        {"label": "Chunks indexés", "value": total_chunks, "delta": f"moy. {moyenne} / document", "muted": True, "tone": "blue"},
        {
            "label": "Non indexés",
            "value": non_indexes,
            "delta": "à indexer" if non_indexes else "tout est indexé",
            "muted": not non_indexes,
            "tone": "orange" if non_indexes else "green",
        },
        {"label": "Modèle", "value": health.get("modele_llm", "—") if health else "—", "delta": "Ollama (local)", "muted": True, "tone": "teal"},
    ]
)

# ---------------------------------------------------------------------------
# Répartition par catégorie
# ---------------------------------------------------------------------------
theme.section("Répartition par catégorie", f"{total_chunks} chunks indexés")
chunks_par_cat = {nom: 0 for nom in CATEGORY_NAMES}
for doc in documents:
    if doc.get("categorie") in chunks_par_cat:
        chunks_par_cat[doc["categorie"]] += doc.get("chunks_count", 0) or 0
df_cat = pd.DataFrame(
    [{"Catégorie": nom, "Chunks": chunks_par_cat[nom]} for nom in CATEGORY_NAMES]
)

col_chart, col_list = st.columns([1.25, 1], gap="medium")
with col_chart:
    bars = (
        alt.Chart(df_cat)
        .mark_bar(size=38, cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            color=alt.Color(
                "Catégorie:N",
                legend=None,
                scale=alt.Scale(
                    domain=CATEGORY_NAMES,
                    range=[theme.category_color(nom) for nom in CATEGORY_NAMES],
                ),
            ),
            x=alt.X(
                "Catégorie:N",
                sort=CATEGORY_NAMES,
                title=None,
                axis=alt.Axis(labelAngle=0, labelColor=theme.MUTED, labelFontSize=11, ticks=False, domainOpacity=0, labelLimit=140),
            ),
            y=alt.Y(
                "Chunks:Q",
                title=None,
                axis=alt.Axis(grid=True, gridColor="#f0f0f0", domainOpacity=0, ticks=False, labelColor=theme.FAINT, labelFontSize=10),
            ),
            tooltip=["Catégorie", "Chunks"],
        )
        .properties(height=260)
        .configure_view(stroke=None)
        .configure(background="white")
    )
    theme.chart(bars)

with col_list:
    nombres = {nom: categories.get(nom, {}).get("nb_documents", 0) for nom in CATEGORY_NAMES}
    maxi = max(nombres.values()) or 1
    lignes = "".join(
        '<div style="margin-bottom:.7rem">'
        '<div class="dc-rowline" style="padding:.1rem 0">'
        f'<span style="font-size:.83rem;color:{theme.INK};display:flex;align-items:center;gap:.45rem">'
        f'<i style="width:8px;height:8px;border-radius:99px;background:{theme.category_color(nom)};display:inline-block"></i>{nom}</span>'
        f'<b style="font-size:.8rem">{nombres[nom]}</b></div>'
        '<div style="height:5px;border-radius:99px;background:#f1f1f1;overflow:hidden">'
        f'<div style="height:5px;width:{round(nombres[nom] / maxi * 100)}%;background:{theme.category_color(nom)};border-radius:99px"></div>'
        "</div></div>"
        for nom in CATEGORY_NAMES
    )
    theme.html(f'<div class="dc-card"><h5>Documents par catégorie</h5>{lignes}</div>')

# ---------------------------------------------------------------------------
# Documents récents + qualité du système
# ---------------------------------------------------------------------------
col_docs, col_sante = st.columns([1.5, 1], gap="medium")
with col_docs:
    theme.section("Documents récemment ajoutés", f"{min(total_docs, 8)} derniers")
    recents = sorted(documents, key=lambda d: d.get("date_ajout", ""), reverse=True)[:8]
    if recents:
        theme.dataframe(
            [
                {
                    "Fichier": d["filename"],
                    "Catégorie": d["categorie"],
                    "Format": d.get("type_original", ""),
                    "Chunks": d.get("chunks_count", 0),
                    "Ajouté le": d.get("date_ajout", ""),
                }
                for d in recents
            ],
            hide_index=True,
            height=280,
        )
    else:
        theme.html('<div class="dc-empty">Aucun document confirmé pour le moment.</div>')

with col_sante:
    theme.section("Qualité du système", "API")
    if health:
        etat = theme.badge("API connectée")
    else:
        etat = theme.badge("API hors ligne", error=True)
    theme.html(
        f'<div class="dc-card" style="margin-bottom:.6rem">{etat}</div>'
        '<div class="dc-card">'
        f'<div class="dc-rowline"><span>Modèle de langue</span><b>{health.get("modele_llm", "—") if health else "—"}</b></div>'
        f'<div class="dc-rowline"><span>Modèle d\'embedding</span><b>{health.get("modele_embedding", "—") if health else "—"}</b></div>'
        f'<div class="dc-rowline"><span>Documents non indexés</span><b>{non_indexes}</b></div>'
        f'<div class="dc-rowline"><span>Catégories couvertes</span><b>{couvertes} / {len(CATEGORY_NAMES)}</b></div>'
        "</div>"
    )

st.caption(
    "Sources : /api/health, /api/categories et /api/documents. L'historique des questions "
    "et des classifications n'est pas exposé par l'API : il n'est pas affiché."
)

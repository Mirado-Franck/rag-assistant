"""
3_Dashboard.py — Tableau de bord (Jour 3, partie B1).

Statistiques simulées. Jour 6 : brancher les agrégats réels de ChromaDB / API.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # -> interface/

import pandas as pd
import streamlit as st

import nav
import theme
from data_mock import (
    CATEGORIES,
    DOCUMENTS,
    STATS,
    TOTAL_CHUNKS,
)

nav.setup("dashboard", "Tableau de bord", "◼")

INK, MUTED, FAINT = theme.INK, theme.MUTED, theme.FAINT

# ---------------------------------------------------------------------------
# En-tête
# ---------------------------------------------------------------------------
head_l, head_r = st.columns([3, 1], gap="small")
with head_l:
    theme.page_header(
        "Tableau de bord",
        "Vue d'ensemble de la base documentaire et de l'activité de l'assistant.",
        eyebrow="Étape 3",
    )
with head_r:
    st.write("")
    csv = pd.DataFrame(DOCUMENTS).to_csv(index=False).encode("utf-8")
    st.download_button(
        "Exporter (CSV)",
        data=csv,
        file_name="docuclassif_documents.csv",
        mime="text/csv",
        width="stretch",
    )

# ---------------------------------------------------------------------------
# Indicateurs clés
# ---------------------------------------------------------------------------
theme.section("Statistiques générales", "mise à jour en temps réel")
theme.stat_cards(
    [
        {"label": "Documents", "value": STATS["documents"], "delta": f"+{STATS['documents_delta']} cette semaine", "tone": "indigo"},
        {"label": "Chunks", "value": STATS["chunks"], "delta": "moy. 19 / document", "muted": True, "tone": "blue"},
        {"label": "Questions posées", "value": STATS["questions"], "delta": "7 derniers jours", "muted": True, "tone": "teal"},
        {"label": "Classifications", "value": STATS["classifications"], "delta": f"{STATS['confirmation_rate']} % confirmées", "tone": "orange"},
    ]
)

# ---------------------------------------------------------------------------
# Répartition par catégorie
# ---------------------------------------------------------------------------
theme.section("Répartition par catégorie", f"{TOTAL_CHUNKS} chunks indexés")
col_chart, col_list = st.columns([1.25, 1], gap="medium")

df_cat = pd.DataFrame(
    [{"Catégorie": c["label"], "Chunks": c["count"]} for c in CATEGORIES]
)

with col_chart:
    import altair as alt

    bars = (
        alt.Chart(df_cat)
        .mark_bar(size=38, cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            color=alt.Color(
                "Catégorie:N",
                legend=None,
                scale=alt.Scale(
                    domain=[c["label"] for c in CATEGORIES],
                    range=[theme.category_color(c["label"]) for c in CATEGORIES],
                ),
            ),
            x=alt.X(
                "Catégorie:N",
                sort=[c["label"] for c in CATEGORIES],
                title=None,
                axis=alt.Axis(labelAngle=0, labelColor=MUTED, labelFontSize=11, ticks=False, domainOpacity=0),
            ),
            y=alt.Y(
                "Chunks:Q",
                title=None,
                axis=alt.Axis(grid=True, gridColor="#f0f0f0", domainOpacity=0, ticks=False, labelColor=FAINT, labelFontSize=10),
            ),
            tooltip=["Catégorie", "Chunks"],
        )
        .properties(height=250)
        .configure_view(stroke=None)
        .configure(background="white")
    )
    theme.chart(bars)

with col_list:
    maxi = max(c["count"] for c in CATEGORIES)
    rows = "".join(
        f'<div style="margin-bottom:.7rem">'
        f'<div class="dc-rowline" style="padding:.1rem 0">'
        f'<span style="font-size:.83rem;color:{theme.INK};display:flex;align-items:center;gap:.45rem">'
        f'<i style="width:8px;height:8px;border-radius:99px;background:{theme.category_color(c["label"])};display:inline-block"></i>{c["label"]}</span>'
        f'<b style="font-size:.8rem">{c["count"]}</b></div>'
        f'<div style="height:5px;border-radius:99px;background:#f1f1f1;overflow:hidden">'
        f'<div style="height:5px;width:{round(c["count"] / maxi * 100)}%;background:{theme.category_color(c["label"])};border-radius:99px"></div>'
        f"</div></div>"
        for c in CATEGORIES
    )
    theme.html(f'<div class="dc-card"><h5>Volume par catégorie</h5>{rows}</div>')

# ---------------------------------------------------------------------------
# Activité
# ---------------------------------------------------------------------------
theme.section("Activité des 7 derniers jours", "questions posées / jour")
activite = pd.DataFrame(
    {
        "Jour": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
        "Questions": [3, 7, 5, 9, 6, 11, 6],
    }
)
import altair as alt

area = (
    alt.Chart(activite)
    .mark_area(
        line={"color": theme.ACCENT, "strokeWidth": 2.5},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(79,70,229,0.22)", offset=0),
                alt.GradientStop(color="rgba(79,70,229,0.01)", offset=1),
            ],
            x1=1, x2=1, y1=1, y2=0,
        ),
        interpolate="monotone",
    )
    .encode(
        x=alt.X(
            "Jour:N",
            sort=["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
            title=None,
            axis=alt.Axis(labelAngle=0, labelColor=MUTED, labelFontSize=11, ticks=False, domainOpacity=0),
        ),
        y=alt.Y("Questions:Q", title=None, axis=alt.Axis(grid=True, gridColor="#f0f0f0", domainOpacity=0, ticks=False, labelColor=FAINT, labelFontSize=10)),
        tooltip=["Jour", "Questions"],
    )
    .properties(height=190)
    .configure_view(stroke=None)
)
theme.chart(area)

# ---------------------------------------------------------------------------
# Documents récents + santé du système
# ---------------------------------------------------------------------------
col_docs, col_sante = st.columns([1.5, 1], gap="medium")

with col_docs:
    theme.section("Documents récemment ajoutés", "6 derniers")
    recents = [
        {
            "Fichier": d["fichier"],
            "Catégorie": d["categorie"],
            "Chunks": d["chunks"],
            "Confiance": f"{round(d['confiance'] * 100)} %",
            "Statut": d["statut"],
        }
        for d in DOCUMENTS[:6]
    ]
    theme.dataframe(recents, hide_index=True, height=250)

with col_sante:
    theme.section("Qualité du système", "Jour 3")
    theme.html(
        f'<div class="dc-card">'
        f'<div class="dc-rowline"><span>Classifications confirmées</span><b>{STATS["confirmation_rate"]} %</b></div>'
        f'<div class="dc-rowline"><span>Confiance moyenne</span><b>{STATS["avg_confidence"]} %</b></div>'
        f'<div class="dc-rowline"><span>Latence moyenne (RAG)</span><b>{STATS["avg_latency"]}</b></div>'
        f'<div class="dc-rowline"><span>Catégories couvertes</span><b>{len(CATEGORIES)} / 5</b></div>'
        f'<div class="dc-rowline"><span>Documents non indexés</span><b>0</b></div>'
        f"</div>"
    )

st.caption(
    "Maquette — chiffres simulés. Au Jour 6, ces indicateurs seront calculés "
    "à partir de ChromaDB et des journaux de l'API."
)

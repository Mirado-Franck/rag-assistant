"""
1_Upload.py — Upload & Classification (Jour 3, partie B1).

Classification SIMULÉE : aucune dépendance au classifieur de A1.
Jour 4 : remplacer `predict_category(...)` par l'appel à l'API de A2.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # -> interface/

import streamlit as st

import nav
import theme
from data_mock import CATEGORY_LABELS, RECENT_CLASSIFICATIONS, predict_category

nav.setup("upload", "Upload & Classification", "◼")

USAGE = """<div class="dc-card">
<h5>Comment ça marche</h5>
<p>1. Déposez un PDF ou un DOCX (ou collez un extrait de texte).<br>
2. Le modèle zero-shot propose une catégorie et un score de confiance.<br>
3. Vous confirmez, ou vous corrigez dans la liste des 5 catégories.<br>
Le document n'est indexé qu'après votre validation.</p>
</div>"""


def confidence_meter(value: float) -> str:
    """Barre de confiance + libellé coloré."""
    pct = round(value * 100)
    color = theme.GREEN if pct >= 75 else (theme.AMBER if pct >= 55 else theme.RED)
    label = "Confiance élevée" if pct >= 75 else ("Confiance moyenne" if pct >= 55 else "Confiance faible")
    return (
        f'<div style="display:flex;justify-content:space-between;font-size:.78rem;'
        f'color:{theme.MUTED};margin:.55rem 0 .25rem 0">'
        f"<span>{label}</span><b style=\"color:{theme.INK}\">{pct} %</b></div>"
        f'<div style="height:6px;border-radius:99px;background:#efefef;overflow:hidden">'
        f'<div style="height:6px;width:{pct}%;background:{color};border-radius:99px"></div></div>'
    )


# ---------------------------------------------------------------------------
# En-tête
# ---------------------------------------------------------------------------
theme.page_header(
    "Upload & Classification",
    "Déposez un document : il est classé automatiquement, puis validé par vous.",
    eyebrow="Étape 1",
)

# ---------------------------------------------------------------------------
# Zone d'upload + rappel
# ---------------------------------------------------------------------------
col_main, col_side = st.columns([1.45, 1], gap="medium")

with col_main:
    uploaded = st.file_uploader("Fichier à analyser", type=["pdf", "docx", "txt"])
    st.caption("Formats acceptés : PDF, DOCX, TXT — 20 Mo maximum.")
    extrait = st.text_area(
        "Extrait de texte (optionnel)",
        placeholder="Collez ici un extrait si vous voulez tester la classification sans fichier…",
        height=96,
    )

    c1, c2 = st.columns([1.1, 1], gap="small")
    with c1:
        analyser = theme.button("Analyser le document", primary=True, full=True)
    with c2:
        exemple = theme.button("Charger un exemple", full=True)

with col_side:
    theme.html(USAGE)
    st.caption("Astuce : « Charger un exemple » simule l'analyse de 02_guide_bourses.docx.")

# ---------------------------------------------------------------------------
# Traitement (simulation)
# ---------------------------------------------------------------------------
if exemple:
    st.session_state["analyse"] = predict_category(
        "02_guide_bourses.docx",
        "guide des bourses conditions de candidature dossier",
    )
    st.session_state["analyse_nom"] = "02_guide_bourses.docx"
    st.session_state["analyse_etat"] = "en_attente"

if analyser:
    nom = uploaded.name if uploaded else "document_sans_nom.txt"
    texte = extrait or ""
    if uploaded is not None:
        try:  # extraction réelle si le backend de A2 n'est pas encore là
            texte += "\n" + (
                uploaded.read().decode("utf-8", errors="ignore")
                if uploaded.name.lower().endswith(".txt")
                else ""
            )
        except Exception:  # noqa: BLE001
            pass
    if not uploaded and not extrait.strip():
        st.warning("Déposez un fichier ou collez un extrait de texte avant d'analyser.")
    else:
        with st.spinner("Analyse du document…"):
            st.session_state["analyse"] = predict_category(nom, texte)
            st.session_state["analyse_nom"] = nom
            st.session_state["analyse_etat"] = "en_attente"

# ---------------------------------------------------------------------------
# Résultat
# ---------------------------------------------------------------------------
theme.section("Résultat de la classification", "Données simulées")

analyse = st.session_state.get("analyse")
nom_fichier = st.session_state.get("analyse_nom", "")
etat = st.session_state.get("analyse_etat", "vide")

if not analyse:
    theme.html(
        '<div class="dc-empty">Aucun document analysé pour le moment.<br>'
        "Déposez un fichier ou cliquez sur « Charger un exemple ».</div>"
    )
else:
    if etat == "confirme":
        theme.html(
            f'<div style="display:flex;gap:.4rem;align-items:center;margin-bottom:.5rem">'
            f'{theme.badge("Classification confirmée")}'
            f'<span style="font-size:.8rem;color:{theme.MUTED}">Document indexé dans ChromaDB (simulation)</span>'
            f"</div>"
        )

    res_col, opt_col = st.columns([1.15, 1], gap="medium")

    with res_col:
        theme.html(
            f'<div class="dc-card">'
            f'<div style="display:flex;align-items:center;gap:.45rem;font-size:.76rem;color:{theme.MUTED}">'
            f'{theme.icon("file", 14, theme.MUTED)} {nom_fichier}</div>'
            f'<div style="font-size:1.35rem;font-weight:640;letter-spacing:-.02em;margin:.45rem 0 .1rem 0">'
            f'{analyse["categorie"]}</div>'
            f'<p style="margin:0;font-size:.82rem;color:{theme.MUTED}">Catégorie proposée par le modèle</p>'
            f"{confidence_meter(analyse['confiance'])}"
            f'<div style="display:flex;gap:1.2rem;margin-top:.8rem;font-size:.78rem;color:{theme.MUTED}">'
            f'<span>Chunks estimés <b style="color:{theme.INK}">{analyse["chunks_estimes"]}</b></span>'
            f'<span>Latence <b style="color:{theme.INK}">1,8 s</b></span>'
            f'<span>Modèle <b style="color:{theme.INK}">Llama 3.2 3B</b></span>'
            f"</div></div>"
        )

    with opt_col:
        alternatives = analyse.get("alternatives", [])
        alt_html = "".join(
            f'<div class="dc-rowline"><span>{a["label"]}</span><b>{round(a["score"] * 100)} %</b></div>'
            for a in alternatives
        )
        titre = "Autres hypothèses" if analyse["fiable"] else "Confiance faible — vérifiez"
        theme.html(
            f'<div class="dc-card"><h5>{titre}</h5>'
            f'<p style="margin-bottom:.4rem">Classement des catégories suivantes selon le score du modèle.</p>'
            f"{alt_html}</div>"
        )
        if not analyse["fiable"]:
            st.info(
                "Le score est inférieur à 75 % : choisissez la bonne catégorie ci-dessous "
                "avant de valider.",
                icon="⚠️",
            )

    st.write("")
    if etat != "confirme":
        c1, c2, c3 = st.columns([1.2, 1.6, 1], gap="small")
        with c1:
            if theme.button("Confirmer la catégorie", primary=True, full=True):
                st.session_state["analyse_etat"] = "confirme"
                st.rerun()
        with c2:
            correction = st.selectbox(
                "Corriger la catégorie",
                CATEGORY_LABELS,
                index=CATEGORY_LABELS.index(analyse["categorie"]),
                label_visibility="collapsed",
            )
        with c3:
            if theme.button("Rejeter", full=True):
                st.session_state["analyse"] = None
                st.session_state["analyse_etat"] = "vide"
                st.rerun()

        if correction != analyse["categorie"]:
            st.caption(
                f"La validation enregistrera **{correction}** au lieu de "
                f"**{analyse['categorie']}** (écart consigné pour l'évaluation)."
            )
    else:
        c1, c2, _ = st.columns([1, 1, 2], gap="small")
        with c1:
            if theme.button("Poser une question", primary=True, full=True):
                st.switch_page("pages/2_Questions.py")
        with c2:
            if theme.button("Analyser un autre document", full=True):
                st.session_state["analyse"] = None
                st.session_state["analyse_etat"] = "vide"
                st.rerun()

# ---------------------------------------------------------------------------
# Historique
# ---------------------------------------------------------------------------
theme.section("Classifications récentes", "4 dernières")
theme.dataframe(
    RECENT_CLASSIFICATIONS,
    width="stretch",
    hide_index=True,
)
st.caption(
    "Tableau de démonstration. Au Jour 4, ces lignes viendront de l'API de A2 "
    "(POST /classify) et de ChromaDB."
)

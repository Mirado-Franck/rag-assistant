"""
1_Upload.py — Upload & Classification en 4 étapes (partie B1, Jour 4 rattrapage + Jour 6).

Étapes : dépôt → extraction → proposition de catégorie → confirmation.
Routes API : POST /api/upload (extraction + classification), POST /api/confirm (indexation).

Cas d'affichage selon la confiance (score entre 0 et 1) :
  - > 80 %          : catégorie proposée, boutons Confirmer / Changer ;
  - 60 % à 80 %     : alternatives avec probabilités, choix dans la liste ;
  - < 60 %          : sélection manuelle obligatoire (aucune catégorie préchoisie).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # -> interface/

import streamlit as st

import api_client
import nav
import theme
from config import CATEGORY_LABELS, EXEMPLE_TEXTE

health, _erreur_api = nav.setup("upload", "Upload & Classification", "◼")

ETAPES = ["Dépôt", "Extraction", "Proposition", "Confirmation"]
PLACEHOLDER = "— Choisissez une catégorie —"

# --- État de la page -------------------------------------------------------
st.session_state.setdefault("up_step", 0)
st.session_state.setdefault("up_result", None)     # réponse de /api/upload
st.session_state.setdefault("up_nom", "")
st.session_state.setdefault("up_done", None)       # réponse de /api/confirm
st.session_state.setdefault("up_changer", False)   # cas confiance haute : sélection ouverte
st.session_state.setdefault("up_historique", [])   # classifications confirmées (session)


def reinitialiser() -> None:
    st.session_state["up_step"] = 0
    st.session_state["up_result"] = None
    st.session_state["up_done"] = None
    st.session_state["up_changer"] = False


def charger_exemple() -> None:
    st.session_state["extrait"] = EXEMPLE_TEXTE


def pourcentage(valeur: float) -> int:
    return round(valeur * 100)


def jauge_confiance(valeur: float) -> str:
    pct = pourcentage(valeur)
    couleur = theme.GREEN if pct > 80 else (theme.AMBER if pct >= 60 else theme.RED)
    libelle = "Confiance élevée" if pct > 80 else ("Confiance moyenne" if pct >= 60 else "Confiance faible")
    return (
        f'<div style="display:flex;justify-content:space-between;font-size:.78rem;'
        f'color:{theme.MUTED};margin:.55rem 0 .25rem 0">'
        f'<span>{libelle}</span><b style="color:{theme.INK}">{pct} %</b></div>'
        f'<div style="height:6px;border-radius:99px;background:#efefef;overflow:hidden">'
        f'<div style="height:6px;width:{pct}%;background:{couleur};border-radius:99px"></div></div>'
    )


def barres_alternatives(items: list[dict]) -> str:
    lignes = []
    for item in items:
        couleur = theme.category_color(item["categorie"])
        pct = pourcentage(item["probabilite"])
        lignes.append(
            f'<div class="dc-alt-row"><span class="name">{item["categorie"]}</span>'
            f'<span class="bar"><i style="width:{pct}%;background:{couleur}"></i></span>'
            f'<span class="pct">{pct} %</span></div>'
        )
    return "".join(lignes)


# ---------------------------------------------------------------------------
# En-tête + étapes
# ---------------------------------------------------------------------------
theme.page_header(
    "Upload & Classification",
    "Déposez un document : il est classé automatiquement, puis validé par vous.",
    eyebrow="Étape 1",
)
theme.stepper(ETAPES, st.session_state["up_step"])

if health is None:
    theme.error_box(_erreur_api or api_client.MESSAGE_API_DOWN)

# ---------------------------------------------------------------------------
# Étape 1 — Dépôt
# ---------------------------------------------------------------------------
if st.session_state["up_step"] == 0:
    col_main, col_side = st.columns([1.45, 1], gap="medium")
    with col_main:
        uploaded = st.file_uploader("Fichier à analyser", type=["pdf", "docx", "txt"])
        st.caption("Formats acceptés : PDF, DOCX, TXT — 20 Mo maximum.")
        extrait = st.text_area(
            "Extrait de texte (optionnel)",
            placeholder="Collez ici un texte si vous voulez tester la classification sans fichier…",
            height=110,
            key="extrait",
        )
        c1, c2 = st.columns([1.1, 1], gap="small")
        with c1:
            analyser = theme.button("Analyser le document", primary=True, full=True)
        with c2:
            theme.button("Charger un exemple", full=True, on_click=charger_exemple)

    with col_side:
        theme.html(
            '<div class="dc-card"><h5>Comment ça marche</h5>'
            "<p>1. Vous déposez un fichier ou collez un texte.<br>"
            "2. Le texte est extrait, puis le modèle propose une catégorie.<br>"
            "3. Vous confirmez, ou vous choisissez une autre catégorie.<br>"
            "Le document n'est indexé qu'après votre validation.</p></div>"
        )
        st.caption("« Charger un exemple » insère un extrait réel du guide des bourses.")

    if analyser:
        if uploaded is not None:
            nom, contenu = uploaded.name, uploaded.getvalue()
        elif extrait.strip():
            nom, contenu = "extrait_saisi.txt", extrait.encode("utf-8")
        else:
            nom, contenu = "", None
            st.warning("Déposez un fichier ou collez un extrait de texte avant d'analyser.")
        if contenu is not None:
            try:
                with st.spinner("Extraction et classification en cours (le modèle local peut prendre un moment)…"):
                    resultat = api_client.upload(nom, contenu)
            except api_client.ApiError as exc:
                theme.error_box(exc.message)
            else:
                st.session_state["up_result"] = resultat
                st.session_state["up_nom"] = nom
                st.session_state["up_changer"] = False
                st.session_state["up_step"] = 1
                st.rerun()

# ---------------------------------------------------------------------------
# Étape 2 — Extraction
# ---------------------------------------------------------------------------
elif st.session_state["up_step"] == 1:
    res = st.session_state["up_result"]
    theme.html(
        '<div class="dc-card">'
        f'<div style="font-size:.8rem;color:{theme.MUTED};margin-bottom:.4rem">'
        f'{theme.icon("file", 14, theme.MUTED)} Fichier : <b style="color:{theme.INK}">{res["filename"]}</b></div>'
        f'<h5>Texte extrait (aperçu)</h5>'
        f'<div style="white-space:pre-wrap;font-size:.8rem;color:{theme.MUTED};'
        f'background:{theme.BG_SOFT};border:1px solid {theme.BORDER};border-radius:10px;'
        f'padding:.7rem .85rem;max-height:260px;overflow:auto">{res.get("text_preview", "")}</div>'
        "</div>"
    )
    c1, c2, _ = st.columns([1.2, 1, 2], gap="small")
    with c1:
        if theme.button("Continuer vers la proposition", primary=True, full=True):
            st.session_state["up_step"] = 2
            st.rerun()
    with c2:
        if theme.button("Recommencer", full=True):
            reinitialiser()
            st.rerun()

# ---------------------------------------------------------------------------
# Étape 3 — Proposition (3 cas selon la confiance)
# ---------------------------------------------------------------------------
elif st.session_state["up_step"] == 2:
    res = st.session_state["up_result"]
    proposee = res["categorie"]
    confiance = float(res["confiance"])
    cas = api_client.confidence_band(confiance)
    alternatives = api_client.normalize_alternatives(res.get("alternatives"))
    file_id = res["file_id"]
    nom = st.session_state["up_nom"]

    couleur = theme.category_color(proposee)
    justification = res.get("justification", "")
    res_col, opt_col = st.columns([1.15, 1], gap="medium")
    with res_col:
        theme.html(
            f'<div class="dc-card" style="border-top:3px solid {couleur}">'
            f'<div style="display:flex;align-items:center;gap:.45rem;font-size:.76rem;color:{theme.MUTED}">'
            f'{theme.icon("file", 14, theme.MUTED)} {nom}</div>'
            f'<div style="font-size:1.35rem;font-weight:640;letter-spacing:-.02em;margin:.45rem 0 .1rem 0;color:{couleur}">'
            f"{proposee}</div>"
            f'<p style="margin:0;font-size:.82rem;color:{theme.MUTED}">Catégorie proposée par le modèle</p>'
            f"{jauge_confiance(confiance)}"
            f'<p style="margin:.7rem 0 0 0;font-size:.78rem;color:{theme.MUTED}">{justification}</p>'
            "</div>"
        )
        if justification.startswith("[Fallback"):
            theme.html(
                '<div class="dc-note">Classification de secours : le modèle local n\'a pas répondu. '
                "La proposition est indicative, vérifiez-la avant de confirmer.</div>"
            )

    with opt_col:
        if cas == "haute":
            theme.html(
                '<div class="dc-card"><h5>Confiance élevée</h5>'
                '<p style="margin-bottom:0">La catégorie proposée est très probable. '
                "Confirmez-la, ou changez-la si elle ne convient pas.</p></div>"
            )
        elif cas == "moyenne":
            liste = [{"categorie": proposee, "probabilite": confiance}] + [
                a for a in alternatives if a["categorie"] != proposee
            ]
            liste.sort(key=lambda a: a["probabilite"], reverse=True)
            theme.html(
                '<div class="dc-card"><h5>Plusieurs catégories possibles</h5>'
                '<p style="margin-bottom:.5rem">Choisissez la catégorie la plus juste.</p>'
                f"{barres_alternatives(liste)}</div>"
            )
        else:
            hypothese = pourcentage(confiance)
            theme.html(
                '<div class="dc-card" style="border-color:#fecaca"><h5 style="color:#991b1b">'
                "Confiance trop faible</h5>"
                '<p style="margin-bottom:0">Le modèle ne peut pas trancher '
                f"(hypothèse : {proposee}, {hypothese} %). Vous devez choisir la catégorie "
                "vous-même.</p></div>"
            )

    st.write("")

    # --- Actions selon le cas ---------------------------------------------
    if cas == "haute":
        if not st.session_state["up_changer"]:
            c1, c2, c3 = st.columns([1.3, 1.3, 1], gap="small")
            with c1:
                confirmer = theme.button("Confirmer la catégorie", primary=True, full=True)
            with c2:
                if theme.button("Changer de catégorie", full=True):
                    st.session_state["up_changer"] = True
                    st.rerun()
            with c3:
                rejeter = theme.button("Rejeter", full=True)
            choix = proposee if confirmer else None
        else:
            c1, c2, c3 = st.columns([1.6, 1.3, 1], gap="small")
            with c1:
                choix_liste = st.selectbox(
                    "Catégorie",
                    CATEGORY_LABELS,
                    index=CATEGORY_LABELS.index(proposee),
                )
            with c2:
                confirmer = theme.button("Confirmer ma sélection", primary=True, full=True)
            with c3:
                rejeter = theme.button("Rejeter", full=True)
            choix = choix_liste if confirmer else None

    elif cas == "moyenne":
        c1, c2, c3 = st.columns([1.6, 1.3, 1], gap="small")
        with c1:
            choix_liste = st.selectbox(
                "Catégorie",
                CATEGORY_LABELS,
                index=CATEGORY_LABELS.index(proposee),
            )
        with c2:
            confirmer = theme.button("Valider ce choix", primary=True, full=True)
        with c3:
            rejeter = theme.button("Rejeter", full=True)
        choix = choix_liste if confirmer else None

    else:  # faible : sélection manuelle obligatoire
        c1, c2, c3 = st.columns([1.6, 1.3, 1], gap="small")
        with c1:
            choix_liste = st.selectbox(
                "Catégorie (obligatoire)",
                [PLACEHOLDER] + CATEGORY_LABELS,
                index=0,
            )
        choisie = choix_liste != PLACEHOLDER
        with c2:
            confirmer = theme.button(
                "Confirmer ma sélection", primary=True, full=True, disabled=not choisie,
                help=None if choisie else "Choisissez une catégorie pour activer la confirmation.",
            )
        with c3:
            rejeter = theme.button("Rejeter", full=True)
        choix = choix_liste if (confirmer and choisie) else None

    if rejeter:
        reinitialiser()
        st.rerun()

    if choix:
        try:
            with st.spinner("Indexation du document…"):
                reponse = api_client.confirm(file_id, choix)
        except api_client.ApiError as exc:
            theme.error_box(exc.message)
        else:
            st.session_state["up_done"] = reponse
            st.session_state["up_step"] = 3
            indexe = bool(reponse.get("indexe", False))
            st.session_state["up_historique"].insert(0, {
                "Fichier": nom,
                "Catégorie": choix,
                "Confiance": f"{pourcentage(confiance)} %",
                "Statut": "Indexé" if indexe else "Confirmé, non indexé",
            })
            st.rerun()

# ---------------------------------------------------------------------------
# Étape 4 — Confirmation
# ---------------------------------------------------------------------------
elif st.session_state["up_step"] == 3:
    done = st.session_state["up_done"]
    indexe = bool(done.get("indexe", False))
    nb_chunks = done.get("nb_chunks", done.get("chunks_count", 0))
    theme.html(
        f'<div style="display:flex;gap:.4rem;align-items:center;margin-bottom:.5rem">'
        f'{theme.badge("Classification confirmée")}'
        f'<span style="font-size:.8rem;color:{theme.MUTED}">{done.get("message", "")}</span></div>'
    )
    theme.html(
        '<div class="dc-card">'
        f'<div style="font-size:.76rem;color:{theme.MUTED}">Fichier indexé sous</div>'
        f'<div style="font-weight:600;margin:.2rem 0 .6rem 0">{done.get("source_file", "")}</div>'
        f'<div class="dc-kv"><span>Catégorie <b>{done.get("categorie", "")}</b></span>'
        f"<span>Chunks indexés <b>{nb_chunks}</b></span></div></div>"
    )
    if not indexe:
        theme.html(
            '<div class="dc-note">Le document est confirmé mais pas indexé : vérifiez que ChromaDB '
            "et le modèle d'embedding sont disponibles (voir logs/app.log).</div>"
        )
    st.write("")
    c1, c2, _ = st.columns([1, 1.2, 2], gap="small")
    with c1:
        if theme.button("Poser une question", primary=True, full=True):
            st.switch_page("pages/2_Questions.py")
    with c2:
        if theme.button("Analyser un autre document", full=True):
            reinitialiser()
            st.rerun()

# ---------------------------------------------------------------------------
# Historique de la session
# ---------------------------------------------------------------------------
theme.section("Classifications confirmées", "cette session")
if st.session_state["up_historique"]:
    theme.dataframe(st.session_state["up_historique"], hide_index=True)
else:
    theme.html(
        '<div class="dc-empty">Aucune classification confirmée pour le moment.</div>'
    )

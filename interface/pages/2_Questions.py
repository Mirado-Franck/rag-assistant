"""
2_Questions.py — Assistant Questions & Réponses (Jour 3, partie B1).

RAG SIMULÉ : la réponse et les sources sont factices.
Jour 5 : remplacer `answer_question(...)` par l'appel à l'API de A2 (POST /ask).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # -> interface/

import time

import streamlit as st

import nav
import theme
from data_mock import (
    CATEGORY_LABELS,
    DOCUMENT_NAMES,
    INITIAL_CHAT,
    answer_question,
)

nav.setup("questions", "Questions & Réponses", "◼")

AVATARS = {"user": ":material/person:", "assistant": ":material/auto_awesome:"}

SUGGESTIONS = [
    "Conditions pour obtenir une bourse ?",
    "Comment se déroule l'inscription ?",
    "Pièces pour une demande de stage ?",
]

if "chat" not in st.session_state:
    st.session_state["chat"] = list(INITIAL_CHAT)

# ---------------------------------------------------------------------------
# En-tête
# ---------------------------------------------------------------------------
theme.page_header(
    "Questions & Réponses",
    "Interrogez votre base documentaire. Chaque réponse est sourcée et vérifiable.",
    eyebrow="Étape 2",
)

# ---------------------------------------------------------------------------
# Filtres
# ---------------------------------------------------------------------------
f1, f2, f3, f4 = st.columns([1.2, 1.3, 1, 0.9], gap="small")

with f1:
    portee = st.selectbox(
        "Périmètre",
        ["Tous les documents", "Par catégorie", "Par fichier"],
    )
with f2:
    if portee == "Par catégorie":
        cible = st.selectbox("Catégorie", CATEGORY_LABELS)
        scope = cible
    elif portee == "Par fichier":
        cible = st.selectbox("Fichier", DOCUMENT_NAMES)
        scope = cible
    else:
        st.selectbox("Catégorie", ["—"], disabled=True)
        scope = "Tous"
with f3:
    n_sources = st.slider("Sources affichées", 1, 5, 3)
with f4:
    st.markdown(
        '<div style="font-size:.78rem;font-weight:550;color:#5d5d6b;margin-bottom:.35rem">Session</div>',
        unsafe_allow_html=True,
    )
    if theme.button("Réinitialiser", full=True):
        st.session_state["chat"] = list(INITIAL_CHAT)
        st.rerun()

label_filtre = "Tous les documents" if scope == "Tous" else scope
theme.html(
    f'<div style="display:flex;align-items:center;gap:.45rem;font-size:.78rem;color:{theme.MUTED};'
    f'margin:.15rem 0 .3rem 0">{theme.icon("search", 14, theme.MUTED)}'
    f"Recherche limitée à <b style=\"color:{theme.INK}\">{label_filtre}</b></div>"
)
theme.divider()

# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------
def render_message(msg: dict) -> None:
    with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
        st.markdown(msg["content"])

        if msg.get("sources"):
            with st.expander(f"Sources · {len(msg['sources'])}", expanded=False):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(
                        f"**{i}. {src['fichier']}**  \n"
                        f"{src['categorie']} · {src['ref']} · score {src['score']:.2f}"
                    )
                    if i < len(msg["sources"]):
                        st.markdown(
                            '<div style="border-top:1px solid #ececec;margin:.45rem 0"></div>',
                            unsafe_allow_html=True,
                        )
        if msg.get("meta"):
            m = msg["meta"]
            theme.kv(
                [
                    ("Latence", m.get("latence", "—")),
                    ("Pertinence", m.get("pertinence", "—")),
                    ("Périmètre", m.get("filtre", "—")),
                ]
            )


for message in st.session_state["chat"]:
    render_message(message)

# Suggestions affichées uniquement au démarrage de la conversation
if len(st.session_state["chat"]) <= 1:
    st.markdown(
        '<div style="font-size:.78rem;font-weight:550;color:#5d5d6b;margin:.2rem 0 .1rem 0">'
        "Exemples de questions</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3, gap="small")
    for col, suggestion in zip(cols, SUGGESTIONS):
        with col:
            if theme.button(suggestion, full=True):
                st.session_state["pending"] = suggestion
                st.rerun()

# Une suggestion cliquée est rejouée au tour suivant via `pending`
pending = st.session_state.pop("pending", None)
question = st.chat_input("Posez votre question sur les documents…") or pending

if question:
    st.session_state["chat"].append({"role": "user", "content": question, "sources": [], "meta": {}})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(question)

    resultat = answer_question(question, scope=scope, n_sources=n_sources)

    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        with st.spinner("Recherche dans les documents…"):
            time.sleep(0.4)
        placeholder = st.empty()
        texte = ""
        for mot in resultat["content"].split(" "):
            texte += mot + " "
            placeholder.markdown(texte + "▌")
            time.sleep(0.012)
        placeholder.markdown(resultat["content"])

        with st.expander(f"Sources · {len(resultat['sources'])}", expanded=True):
            for i, src in enumerate(resultat["sources"], 1):
                st.markdown(
                    f"**{i}. {src['fichier']}**  \n"
                    f"{src['categorie']} · {src['ref']} · score {src['score']:.2f}"
                )
        theme.kv(
            [
                ("Latence", resultat["meta"]["latence"]),
                ("Pertinence", resultat["meta"]["pertinence"]),
                ("Périmètre", label_filtre),
            ]
        )

    st.session_state["chat"].append(
        {
            "role": "assistant",
            "content": resultat["content"],
            "sources": resultat["sources"],
            "meta": resultat["meta"],
        }
    )

st.caption(
    "Maquette — réponses simulées. Au Jour 5, le pipeline RAG de A1 répondra "
    "réellement avec les filtres de métadonnées de ChromaDB (A2)."
)

"""
2_Questions.py — Assistant Questions & Réponses (partie B1, Jour 5 rattrapage + Jour 6).

Route API : POST /api/query avec question, n_results, category et source_file facultatifs.
Le fichier filtré est le nom stocké (ex. 'a1b2c3d4_guide.txt'), tel que renvoyé par /api/documents.
Une panne de l'API s'affiche dans la conversation : la page ne plante pas.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # -> interface/

import streamlit as st

import api_client
import nav
import theme
from config import CATEGORY_LABELS

health, _erreur_api = nav.setup("questions", "Questions & Réponses", "◼")

PORTEES = ["Tous les documents", "Par catégorie", "Par fichier"]
AUCUN_FICHIER = "— Aucun fichier confirmé —"
AVATARS = {"user": ":material/person:", "assistant": ":material/auto_awesome:"}
SUGGESTIONS = [
    "Conditions pour obtenir une bourse ?",
    "Comment se déroule l'inscription ?",
    "Pièces pour une demande de stage ?",
]
MESSAGE_ACCUEIL = {
    "role": "assistant",
    "content": (
        "Je réponds à vos questions **uniquement à partir des documents de la base**. "
        "Utilisez les filtres ci-dessus pour restreindre la recherche à une catégorie "
        "ou à un fichier précis. Les réponses citent toujours leurs sources."
    ),
    "sources": [],
    "meta": None,
}

st.session_state.setdefault("chat", [dict(MESSAGE_ACCUEIL)])
st.session_state.setdefault("pending", None)

# Liste des fichiers confirmés (pour le filtre « Par fichier »)
fichiers: list[str] = []
erreur_fichiers = None
try:
    fichiers = sorted(doc["filename"] for doc in api_client.documents())
except api_client.ApiError as exc:
    erreur_fichiers = exc.message

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
    portee = st.selectbox("Périmètre", PORTEES)
with f2:
    if portee == "Par catégorie":
        cible = st.selectbox("Catégorie", CATEGORY_LABELS)
        filtre_categorie, filtre_fichier = cible, None
        libelle = cible
    elif portee == "Par fichier":
        options = fichiers or [AUCUN_FICHIER]
        cible = st.selectbox("Fichier", options, disabled=not fichiers)
        filtre_categorie = None
        filtre_fichier = cible if fichiers else None
        libelle = cible if fichiers else "aucun fichier"
    else:
        st.selectbox("Catégorie", ["—"], disabled=True)
        filtre_categorie, filtre_fichier = None, None
        libelle = "Tous les documents"
with f3:
    n_sources = st.slider("Sources affichées", 1, 20, 4)
with f4:
    st.markdown(
        f'<div style="font-size:.78rem;font-weight:550;color:{theme.MUTED};margin-bottom:.35rem">Session</div>',
        unsafe_allow_html=True,
    )
    if theme.button("Réinitialiser", full=True):
        st.session_state["chat"] = [dict(MESSAGE_ACCUEIL)]
        st.rerun()

theme.html(
    f'<div style="display:flex;align-items:center;gap:.45rem;font-size:.78rem;color:{theme.MUTED};'
    f'margin:.15rem 0 .3rem 0">{theme.icon("search", 14, theme.MUTED)}'
    f'Recherche limitée à <b style="color:{theme.INK}">{libelle}</b></div>'
)
if erreur_fichiers:
    theme.error_box(erreur_fichiers)
theme.divider()


# ---------------------------------------------------------------------------
# Rendu d'un message
# ---------------------------------------------------------------------------
def afficher_message(msg: dict) -> None:
    with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
        if msg.get("erreur"):
            theme.error_box(msg["content"])
            return
        st.markdown(msg["content"])
        if msg.get("mode_degrade"):
            theme.html(
                '<div class="dc-note">Mode dégradé : le moteur RAG n\'est pas disponible. '
                "Les extraits ci-dessous sont proposés sans rédaction de réponse.</div>"
            )
        if msg.get("sources"):
            with st.expander(f"Sources · {len(msg['sources'])}", expanded=msg.get("ouvert", False)):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(f"**{i}. {src['fichier']}**  \n{src['categorie']}")
                    st.caption(src["extrait"])
        if msg.get("meta"):
            m = msg["meta"]
            theme.kv(
                [
                    ("Latence", f"{m['temps_ms'] / 1000:.1f} s"),
                    ("Extraits trouvés", str(m["nb_chunks_trouves"])),
                    ("Périmètre", m["filtre"]),
                ]
            )


# ---------------------------------------------------------------------------
# Question : suggestion cliquée ou saisie
# ---------------------------------------------------------------------------
pending = st.session_state.pop("pending", None)
saisie = st.chat_input("Posez votre question sur les documents…")
question = saisie or pending

if question:
    st.session_state["chat"].append({"role": "user", "content": question})
    if portee == "Par fichier" and not fichiers:
        st.session_state["chat"].append({
            "role": "assistant", "erreur": True,
            "content": "Aucun fichier confirmé n'est disponible. Uploadez et confirmez un document d'abord.",
        })
    else:
        try:
            with st.spinner("Recherche dans les documents et rédaction de la réponse…"):
                resultat = api_client.query(
                    question,
                    n_results=n_sources,
                    category=filtre_categorie,
                    source_file=filtre_fichier,
                )
        except api_client.ApiError as exc:
            st.session_state["chat"].append({"role": "assistant", "erreur": True, "content": exc.message})
        else:
            reponse = resultat.get("reponse", "")
            st.session_state["chat"].append({
                "role": "assistant",
                "content": reponse,
                "mode_degrade": reponse.startswith("[MOCK]"),
                "sources": resultat.get("sources", []),
                "ouvert": True,
                "meta": {
                    "temps_ms": float(resultat.get("temps_ms", 0.0)),
                    "nb_chunks_trouves": resultat.get("nb_chunks_trouves", 0),
                    "filtre": resultat.get("filtre", libelle),
                },
            })

for message in st.session_state["chat"]:
    afficher_message(message)

# Suggestions : seulement au début de la conversation
if len(st.session_state["chat"]) <= 1:
    st.markdown(
        f'<div style="font-size:.78rem;font-weight:550;color:{theme.MUTED};margin:.2rem 0 .1rem 0">'
        "Exemples de questions</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3, gap="small")
    for col, suggestion in zip(cols, SUGGESTIONS):
        with col:
            if theme.button(suggestion, full=True):
                st.session_state["pending"] = suggestion
                st.rerun()

st.caption(
    "Les réponses sont générées par le modèle local à partir des extraits des documents "
    "confirmés. Vérifiez toujours les sources citées."
)

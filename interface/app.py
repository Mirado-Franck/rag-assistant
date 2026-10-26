import streamlit as st
import time

# Configuration de la page
st.set_page_config(
    page_title="Assistant RAG",
    page_icon="📚",
    layout="wide"
)

# Titre
st.title("📚 Assistant Questions-Réponses")
st.caption("IA locale — Aucune donnée envoyée à l'extérieur")
st.divider()

# Barre latérale
with st.sidebar:
    st.header("⚙️ Configuration")
    st.text("Modèle : Llama 3.2 3B")
    st.text("Moteur : Ollama (local)")
    st.text("Base : ChromaDB")
    st.divider()
    st.header("📊 Statistiques")
    st.text("Documents : 15")
    st.text("Chunks : 281")
    st.divider()
    st.caption("🔒 Souveraineté des données")
    st.caption("Toutes les données restent sur votre machine.")

# Zone de question
question = st.text_input(
    "💬 Posez votre question :",
    placeholder="Ex : Quelles sont les conditions pour obtenir une bourse ?"
)

if question:
    # Simuler le temps de traitement (sera remplacé par le vrai RAG)
    with st.spinner("🔍 Recherche dans les documents..."):
        time.sleep(2)  # Simulation
    
    # Réponse simulée (sera remplacée par le vrai RAG)
    st.subheader("📝 Réponse")
    st.info(
        "Ceci est une réponse simulée. Le vrai RAG sera connecté au Jour 4.\n\n"
        "La réponse finale s'affichera ici, basée sur les documents "
        "du corpus institutionnel."
    )
    
    # Sources simulées
    with st.expander("📎 Sources utilisées (3 documents)"):
        st.write("- 📄 01_reglement_interieur.txt (page 12)")
        st.write("- 📄 02_guide_bourses.txt (page 3)")
        st.write("- 📄 05_procedures.txt (page 7)")
    
    # Métadonnées
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏱️ Temps", "2.3s")
    with col2:
        st.metric("📄 Sources", "3")
    with col3:
        st.metric("🎯 Confiance", "87%")

# Historique des questions
st.divider()
st.subheader("📜 Historique")
st.caption("L'historique des questions sera affiché ici.")
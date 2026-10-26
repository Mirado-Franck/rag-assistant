import streamlit as st

st.title("🤖 Mon premier Streamlit")
st.write("Bonjour, ceci est un test pour le projet RAG !")

question = st.text_input("Posez une question :")
if question:
    st.success(f"Vous avez demandé : {question}")
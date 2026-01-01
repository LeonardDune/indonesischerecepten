import streamlit as st

st.set_page_config(
    page_title="Indonesische Recepten",
    page_icon="🍛",
    layout="wide"
)

st.title("Selamat Makan! 🍛")

st.markdown("""
Welkom bij de Indonesische Recepten App.

Gebruik het menu aan de linkerkant om:
- **Recepten** te zoeken en filteren
- **Categorieën** te verkennen (per regio, ingrediënt, etc.)
- De **Chatbot** te vragen om inspiratie
""")

from components.sidebar import render_sidebar

render_sidebar()

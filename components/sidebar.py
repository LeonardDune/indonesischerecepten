import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.page_link("app.py", label="Home", icon="🏠")
        
        # Custom Navigation Logic
        # Standard st.page_link disables the link if it points to the current page.
        # To allow "Resetting" the view (clearing ID) by clicking "Recepten" again,
        # we route through a proxy page if we are currently deep-linked.
        
        if "id" in st.query_params:
             # Route through proxy to force reload/reset
             st.page_link("pages/reset_recepten.py", label="Recepten", icon="🍳")
        else:
             # Standard link (highlighted)
             st.page_link("pages/1_Recepten.py", label="Recepten", icon="🍳")

        st.page_link("pages/2_Categorieën.py", label="Categorieën", icon="📂")
        st.page_link("pages/3_Chat.py", label="Chatbot", icon="💬")
        
        st.divider()
        st.markdown("### Info")
        st.info("Indonesische Recepten App v1.0")

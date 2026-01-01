import streamlit as st
import plotly.express as px
from services.category_queries import get_category_counts

st.set_page_config(page_title="Categorieën", page_icon="📂", layout="wide")

from components.sidebar import render_sidebar
render_sidebar()

st.title("Verken Categorieën 🏷️")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Regio's", "Landen", "Kookmethoden", "Ingrediënten", "Hoofdingrediënten"])

def render_category_chart(data, title, param_name):
    if not data:
        st.info("Geen data beschikbaar.")
        return
        
    names = [d['name'] for d in data][:20]  # Top 20
    counts = [d['recipeCount'] for d in data][:20]
    
    fig = px.bar(
        x=names, 
        y=counts, 
        labels={'x': title, 'y': 'Aantal recepten'},
        title=f"Populaire {title}"
    )
    st.plotly_chart(fig, width="stretch")
    
    # List view for interaction
    st.subheader("Details")
    cols = st.columns(4)
    for idx, item in enumerate(data):
        with cols[idx % 4]:
            if st.button(f"{item['name']} ({item['recipeCount']})", key=f"{param_name}_{idx}"):
                # Reset pagination state
                st.session_state.page = 1
                # Redirect to recipes page with filter
                st.query_params[param_name] = item['name']
                # Fallback session state to ensure transfer
                st.session_state[f"filter_{param_name}"] = [item['name']]
                st.switch_page("pages/1_Recepten.py")

with tab1:
    data = get_category_counts("Region")
    render_category_chart(data, "Regio's", "region")

with tab2:
    data = get_category_counts("Country")
    render_category_chart(data, "Landen", "country")
    
with tab3:
    data = get_category_counts("CookingMethod")
    render_category_chart(data, "Kookmethoden", "method")

with tab4:
    data = get_category_counts("Ingredient")
    render_category_chart(data, "Ingrediënten", "ingredient")
    
with tab5:
    data = get_category_counts("PrimaryIngredient")
    render_category_chart(data, "Hoofdingrediënten", "main_ingredient")


import streamlit as st
from services.recipe_queries import (
    get_all_countries, get_all_regions, get_all_methods, 
    get_all_ingredients, get_all_main_ingredients
)

def get_filter_default(param_name):
    ss_key = f"filter_{param_name}"
    if ss_key in st.session_state:
        return st.session_state.pop(ss_key)
    return st.query_params.get_all(param_name)

def render_checkbox_group(label, options, param_name):
    st.markdown(f"**{label}**")
    defaults = get_filter_default(param_name)
    selected = []
    
    def reset_page():
        st.session_state.page = 1

    for opt in options:
        key = f"cb_{param_name}_{opt}"
        # Initialize from defaults if not already in session state
        if opt in defaults and key not in st.session_state:
            st.session_state[key] = True
            
        if st.checkbox(opt, key=key, on_change=reset_page):
            selected.append(opt)
    return selected

def render_filters():
    st.sidebar.header("Filters")
    
    with st.sidebar:
        with st.expander("🌍 Locatie", expanded=True):
            selected_countries = render_checkbox_group("Land", get_all_countries(), "country")
            st.markdown("---")
            selected_regions = render_checkbox_group("Regio", get_all_regions(), "region")

        with st.expander("🍳 Bereiding", expanded=True):
            selected_methods = render_checkbox_group("Kookmethode", get_all_methods(), "method")

        with st.expander("🦴 Hoofdingrediënt", expanded=True):
            selected_main_ingredients = render_checkbox_group("Kies hoofdingrediënt", get_all_main_ingredients(), "main_ingredient")

        with st.expander("🥕 Alle Ingrediënten", expanded=False):
            # Keep as multiselect for the large list
            selected_ingredients = st.multiselect(
                "Ingrediënt", 
                options=get_all_ingredients(),
                default=get_filter_default("ingredient")
            )
            
    return {
        "countries": selected_countries,
        "regions": selected_regions,
        "methods": selected_methods,
        "ingredients": selected_ingredients,
        "main_ingredients": selected_main_ingredients
    }

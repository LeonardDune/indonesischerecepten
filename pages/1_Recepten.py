import streamlit as st

st.set_page_config(page_title="Recepten", page_icon="🥘", layout="wide")

from services.recipe_queries import search_recipes, get_recipe_details, get_related_recipes
from components.filters import render_filters
from components.recipe_card import render_recipe_card, render_recipe_detail

from components.sidebar import render_sidebar

render_sidebar()

# Check if we are in detail mode
recipe_id = st.query_params.get("id")

if recipe_id:
    # Detail View
    from streamlit_scroll_to_top import scroll_to_here
    import time
    
    # Force scroll to top using robust component
    scroll_to_here(0, key="scroll_to_top")

    start_details = time.time()
    recipe_data = get_recipe_details(recipe_id)
    print(f"Details fetch took: {time.time() - start_details:.4f}s")
    
    if recipe_data:
        render_recipe_detail(recipe_data)
        
        st.subheader("Gerelateerde Recepten")
        start_related = time.time()
        related = get_related_recipes(recipe_id)
        print(f"Related fetch took: {time.time() - start_related:.4f}s")
        cols = st.columns(3)
        for idx, r in enumerate(related):
            with cols[idx % 3]:
                render_recipe_card(r['recipe'])
    else:
        st.error("Recept niet gevonden.")
        if st.button("Terug naar overzicht"):
            st.query_params.clear()
            st.rerun()

else:
    # List View
    st.title("Alle Recepten 🥘")
    
    filters = render_filters()
    
    # Pagination state
    if 'page' not in st.session_state:
        st.session_state.page = 1
        
    ALL_LIMIT = 24
    
    with st.spinner("Recepten laden..."):
        import time
        start_time = time.time()
        
        # Calculate pagination
        skip = (st.session_state.page - 1) * ALL_LIMIT
        
        recipes, total_count = search_recipes(
            countries=filters['countries'],
            regions=filters['regions'],
            methods=filters['methods'],
            ingredients=filters.get('ingredients', []),
            main_ingredients=filters.get('main_ingredients', []),
            limit=ALL_LIMIT,
            skip=skip
        )
        end_time = time.time()
        print(f"Search took: {end_time - start_time:.4f}s")
    
    if 'start_time' in locals():
        st.caption(f"Search executed in {end_time - start_time:.4f}s")
    
    st.success(f"{total_count} recepten gevonden (Pagina {st.session_state.page} van {max(1, (total_count + ALL_LIMIT - 1) // ALL_LIMIT)})")
    
    # Grid display
    cols = st.columns(3)
    for idx, recipe in enumerate(recipes):
        with cols[idx % 3]:
            render_recipe_card(recipe)
            
    # Pagination Controls
    if total_count > ALL_LIMIT:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.session_state.page > 1:
                if st.button("⬅️ Vorige"):
                    st.session_state.page -= 1
                    st.rerun()
        with col3:
            if st.session_state.page * ALL_LIMIT < total_count:
                if st.button("Volgende ➡️"):
                    st.session_state.page += 1
                    st.rerun()

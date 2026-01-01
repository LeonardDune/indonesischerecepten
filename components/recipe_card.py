import streamlit as st

def render_recipe_card(recipe):
    """
    Renders a recipe card (summary view).
    """
    rec_id = recipe.get('id', recipe.get('uri'))
    
    with st.container(border=True):
        # Clickable title (HTML link without underline)
        st.markdown(
            f"""
            <a href="?id={rec_id}" target="_self" style="text-decoration: none; color: inherit;">
                <h3 style="margin: 0; padding-bottom: 10px; cursor: pointer;">{recipe['name']}</h3>
            </a>
            """, 
            unsafe_allow_html=True
        )

        # Meta info row (compact join)
        meta_items = []
        if recipe.get('prepTime'): meta_items.append(f"⏱️ {recipe['prepTime']}")
        if recipe.get('cookTime'): meta_items.append(f"🔥 {recipe['cookTime']}")
        if recipe.get('yield'): meta_items.append(f"🍽️ {recipe['yield']}")
        
        if meta_items:
            st.caption(" • ".join(meta_items))

        if recipe.get('image'):
            try:
                st.image(recipe['image'], width="stretch")
            except Exception:
                pass # Hide image completely on failure
            
        # Helper for filter links
        def get_filter_link(param_name, value, icon):
            return f'<a href="?id=&{param_name}={value}" target="_self" style="text-decoration: none; color: inherit; cursor: pointer;">{icon} {value}</a>'

        # Labels for Country, Region, Method
        badges = []
        if recipe.get('countries'):
            badges.extend([get_filter_link("country", c, "📍") for c in recipe['countries']])
        if recipe.get('regions'):
            badges.extend([get_filter_link("region", r, "🗺️") for r in recipe['regions']])
        if recipe.get('methods'):
            badges.extend([get_filter_link("method", m, "👩‍🍳") for m in recipe['methods']])
            
        if badges:
            st.markdown(
                f'<div style="font-size: 0.85rem; color: #666; margin-bottom: 5px;">' + 
                " • ".join(badges) + 
                '</div>', 
                unsafe_allow_html=True
            )

        if recipe.get('mainIngredient'):
            st.markdown(
                f'<div style="font-size: 0.85rem; color: #666; margin-bottom: 5px;">' + 
                get_filter_link("main_ingredient", recipe['mainIngredient'], "🦴") + 
                '</div>',
                unsafe_allow_html=True
            )

            
        if recipe.get('description'):
            desc = recipe['description'].strip()
            if desc and desc != "Geen beschrijving beschikbaar.":
                st.write(desc[:150] + "..." if len(desc) > 150 else desc)



def render_recipe_detail(recipe):
    """
    Renders the full recipe detail view.
    """
    if st.button("← Terug naar overzicht"):
        st.query_params.clear()
        st.rerun()
        
    st.title(recipe['recipe']['name'])
    
    if recipe['recipe'].get('image'):
        try:
            st.image(recipe['recipe']['image'], width="stretch")
        except Exception:
            pass # Hide image completely on failure
    
    if recipe['recipe'].get('description'):
        st.info(recipe['recipe']['description'])
        
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Ingrediënten")
        for ing in recipe['ingredients']:
            # Format: Value Unit Name
            parts = []
            if ing.get('value'):
                parts.append(str(ing['value']))
            if ing.get('unit'):
                parts.append(ing['unit'])
            if ing.get('name'):
                parts.append(ing['name'])
            
            if parts:
                st.write(f"- {' '.join(parts)}")
            
        st.divider()
        
        st.subheader("Details")
        if recipe['countries']:
            st.write(f"**Land:** {', '.join(recipe['countries'])}")
        if recipe['regions']:
            st.write(f"**Regio:** {', '.join(recipe['regions'])}")
        if recipe['methods']:
            st.write(f"**Methode:** {', '.join(recipe['methods'])}")
            
    with col2:
        st.subheader("Bereiding")
        # Assuming instructions are not yet fully parsed into steps in the query provided in plan,
        # but if we had them or if they are in description/another field.
        # For now, we rely on what's in the node. Note: schema.org/Recipe often has recipeInstructions.
        # The current query returns `r {.*}` so it might be there.
        
        if recipe['recipe'].get('instructions'):
            instructions = recipe['recipe']['instructions']
            if isinstance(instructions, list):
                for idx, step in enumerate(instructions, 1):
                    st.write(f"**{idx}.** {step}")
            else:
                 st.write(instructions)
        else:
            st.write("Geen bereidingswijze beschikbaar.")

    st.divider()
    
    # Related recipes section could go here if passed in

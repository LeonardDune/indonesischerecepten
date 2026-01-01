import streamlit as st
from services.neo4j import get_neo4j_service

@st.cache_data(ttl=3600)
def get_category_counts(category_type):
    neo4j = get_neo4j_service()
    
    # Map category types to specific queries
    # Country: schema__DefinedTerm {kb__categoryType: 'cuisine'} <-[:schema__recipeCuisine]- (r:schema__Recipe)
    # Region: (c)<-[:kb__hasCuisineRegion]-(r:schema__Recipe)  <-- Region nodes seem to be Resources or specific nodes, let's check label from debug
    # CookingMethod: schema__DefinedTerm {kb__categoryType: 'cooking_method'} <-[:kb__usesCookingMethod]- (r:schema__Recipe)
    # Ingredient: kb__Ingredient <-[:kb__ingredient]- (usage) <-[:kb__hasIngredientUsage]- (r:schema__Recipe)

    if category_type == "Country":
        query = """
        MATCH (c:schema__DefinedTerm {kb__categoryType: 'cuisine'})<-[:schema__recipeCuisine]-(r:schema__Recipe)
        RETURN c.schema__name AS name, count(r) AS recipeCount
        ORDER BY recipeCount DESC
        """
    elif category_type == "Region":
        query = """
        MATCH (c)<-[:kb__hasCuisineRegion]-(r:schema__Recipe)
        RETURN coalesce(c.rdfs__label, last(split(c.uri, '/'))) AS name, count(r) AS recipeCount
        ORDER BY recipeCount DESC
        """
    elif category_type == "CookingMethod":
        query = """
        MATCH (c:schema__DefinedTerm {kb__categoryType: 'cooking_method'})<-[:kb__usesCookingMethod]-(r:schema__Recipe)
        RETURN c.schema__name AS name, count(r) AS recipeCount
        ORDER BY recipeCount DESC
        """
    elif category_type == "Ingredient":
        query = """
        MATCH (c:kb__Ingredient)<-[:kb__ingredient]-(:kb__IngredientUsage)<-[:kb__hasIngredientUsage]-(r:schema__Recipe)
        RETURN c.rdfs__label AS name, count(r) AS recipeCount
        ORDER BY recipeCount DESC
        """
    elif category_type == "PrimaryIngredient":
        query = """
        MATCH (c:schema__DefinedTerm)<-[:kb__hasPrimaryIngredient]-(r:schema__Recipe)
        RETURN c.schema__name AS name, count(r) AS recipeCount
        ORDER BY recipeCount DESC
        """

    else:
        return []
    
    try:
        return neo4j.query(query)
    except Exception as e:
        print(f"Error getting category counts for {category_type}: {e}")
        return []

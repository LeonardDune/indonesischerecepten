from .neo4j import get_neo4j_service

def get_category_counts(category_type):
    neo4j = get_neo4j_service()
    
    # Map frontend keys to backend logic
    category_type = category_type.lower()
    
    if category_type == "country":
        query = """
        MATCH (c:schema__DefinedTerm {kb__categoryType: 'cuisine'})<-[:schema__recipeCuisine]-(r:schema__Recipe)
        WITH c, count(r) AS recipeCount, collect(r) as recipes
        // Get first recipe with an image for the category thumbnail
        WITH c, recipeCount, [r in recipes WHERE r.schema__image IS NOT NULL][0] as sample
        RETURN c.schema__name AS name, recipeCount, sample.schema__image AS image
        ORDER BY recipeCount DESC
        """
    elif category_type == "region":
        query = """
        MATCH (c)<-[:kb__hasCuisineRegion]-(r:schema__Recipe)
        WITH c, count(r) AS recipeCount, collect(r) as recipes
        WITH c, recipeCount, [r in recipes WHERE r.schema__image IS NOT NULL][0] as sample
        RETURN coalesce(c.rdfs__label, last(split(c.uri, '/'))) AS name, recipeCount, sample.schema__image AS image
        ORDER BY recipeCount DESC
        """
    elif category_type == "method":
        query = """
        MATCH (c:schema__DefinedTerm {kb__categoryType: 'cooking_method'})<-[:kb__usesCookingMethod]-(r:schema__Recipe)
        WITH c, count(r) AS recipeCount, collect(r) as recipes
        WITH c, recipeCount, [r in recipes WHERE r.schema__image IS NOT NULL][0] as sample
        RETURN c.schema__name AS name, recipeCount, sample.schema__image AS image
        ORDER BY recipeCount DESC
        """
    elif category_type == "main_ingredient":
        query = """
        MATCH (c:schema__DefinedTerm)<-[:kb__hasPrimaryIngredient]-(r:schema__Recipe)
        WITH c, count(r) AS recipeCount, collect(r) as recipes
        WITH c, recipeCount, [r in recipes WHERE r.schema__image IS NOT NULL][0] as sample
        RETURN c.schema__name AS name, recipeCount, sample.schema__image AS image
        ORDER BY recipeCount DESC
        """
    elif category_type == "ingredient":
        # For the discovery page, we might want top ingredients with images
        query = """
        MATCH (c:kb__Ingredient)<-[:kb__ingredient]-(:kb__IngredientUsage)<-[:kb__hasIngredientUsage]-(r:schema__Recipe)
        WITH c.rdfs__label AS name, count(r) AS recipeCount, collect(r) as recipes
        WITH name, recipeCount, [r in recipes WHERE r.schema__image IS NOT NULL][0] as sample
        RETURN name, recipeCount, sample.schema__image AS image
        ORDER BY recipeCount DESC
        LIMIT 50
        """
    else:
        return []
    
    try:
        return neo4j.query(query)
    except Exception as e:
        print(f"Error getting category counts for {category_type}: {e}")
        return []

def get_ingredients_az(letter=None):
    neo4j = get_neo4j_service()
    
    where_clause = ""
    params = {}
    if letter:
        where_clause = "WHERE i.rdfs__label STARTS WITH $letter"
        params["letter"] = letter.lower()
        
    query = f"""
    MATCH (i:kb__Ingredient)<-[:kb__ingredient]-(:kb__IngredientUsage)<-[:kb__hasIngredientUsage]-(r:schema__Recipe)
    {where_clause}
    WITH i.rdfs__label AS name, count(r) AS recipeCount
    RETURN name, sum(recipeCount) as recipeCount
    ORDER BY name ASC
    """
    return neo4j.query(query, params)

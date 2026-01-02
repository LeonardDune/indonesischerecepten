from .neo4j import get_neo4j_service

def search_recipes(countries=None, regions=None, methods=None, ingredients=None, limit=24, skip=0, **kwargs):
    neo4j = get_neo4j_service()
    
    match_parts = ["(r:schema__Recipe)"]
    where_clauses = []
    params = {"limit": limit, "skip": skip}
    
    if countries:
        match_parts.append("(r)-[:schema__recipeCuisine]->(c:schema__DefinedTerm)")
        where_clauses.append("c.schema__name IN $countries")
        params["countries"] = tuple(countries)
        
    if regions:
        match_parts.append("(r)-[:kb__hasCuisineRegion]->(rg)")
        where_clauses.append("coalesce(rg.rdfs__label, last(split(rg.uri, '/'))) IN $regions")
        params["regions"] = tuple(regions)
        
    if methods:
        match_parts.append("(r)-[:kb__usesCookingMethod]->(m:schema__DefinedTerm)")
        where_clauses.append("m.schema__name IN $methods")
        params["methods"] = tuple(methods)
        
    if ingredients:
        match_parts.append("(r)-[:kb__hasIngredientUsage]->(:kb__IngredientUsage)-[:kb__ingredient]->(i:kb__Ingredient)")
        where_clauses.append("i.rdfs__label IN $ingredients")
        params["ingredients"] = tuple(ingredients)
        
    if kwargs.get('main_ingredients'):
        match_parts.append("(r)-[:kb__hasPrimaryIngredient]->(mi:schema__DefinedTerm)")
        where_clauses.append("mi.schema__name IN $main_ingredients")
        params["main_ingredients"] = tuple(kwargs.get('main_ingredients'))

    match_cypher = " MATCH ".join(match_parts)
    where_cypher = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    count_query = f"""
    MATCH {match_cypher}
    {where_cypher}
    RETURN count(DISTINCT r) as total
    """
    
    data_query = f"""
    MATCH {match_cypher}
    {where_cypher}
    WITH DISTINCT r
    ORDER BY r.schema__name
    SKIP $skip LIMIT $limit
    OPTIONAL MATCH (r)-[:kb__hasPrimaryIngredient]->(mi:schema__DefinedTerm)
    OPTIONAL MATCH (r)-[:schema__recipeCuisine]->(c:schema__DefinedTerm)
    OPTIONAL MATCH (r)-[:kb__hasCuisineRegion]->(rg)
    OPTIONAL MATCH (r)-[:kb__usesCookingMethod]->(m:schema__DefinedTerm)
    WITH r,
         collect(DISTINCT mi.schema__name) as mis,
         collect(DISTINCT c.schema__name) as cs,
         collect(DISTINCT coalesce(rg.rdfs__label, last(split(rg.uri, '/')))) as rs,
         collect(DISTINCT m.schema__name) as ms
    RETURN r {{
      id: r.uri,
      name: r.schema__name,
      image: r.schema__image,
      yield: r.schema__recipeYield,
      instructions: r.schema__recipeInstructions,
      description: r.schema__description,
      mainIngredient: head(mis),
      countries: cs,
      regions: rs,
      methods: ms
    }} AS recipe
    """
    
    try:
        total_res = neo4j.query(count_query, params)
        total = total_res[0]['total'] if total_res else 0
        
        results = neo4j.query(data_query, params)
        recipes = [r['recipe'] for r in results]
        
        return recipes, total
    except Exception as e:
        print(f"Error searching recipes: {e}")
        return [], 0

def get_recipe_details(recipe_id):
    neo4j = get_neo4j_service()
    
    query = """
    MATCH (r:schema__Recipe {uri: $id})
    OPTIONAL MATCH (r)-[:kb__hasIngredientUsage]->(iu:kb__IngredientUsage)
    OPTIONAL MATCH (iu)-[:kb__ingredient]->(i:kb__Ingredient)
    OPTIONAL MATCH (iu)-[:kb__unit]->(u:kb__Unit)
    OPTIONAL MATCH (r)-[:kb__usesCookingMethod]->(m:schema__DefinedTerm)
    OPTIONAL MATCH (r)-[:kb__hasCuisineRegion]->(rg)
    OPTIONAL MATCH (r)-[:schema__recipeCuisine]->(c:schema__DefinedTerm)
    OPTIONAL MATCH (r)-[:kb__hasPrimaryIngredient]->(mi:schema__DefinedTerm)
    WITH r, mi,
         collect(DISTINCT {
             name: i.rdfs__label,
             value: iu.schema__value,
             unit: u.rdfs__label
         }) AS ingredients,
         collect(DISTINCT m.schema__name) AS methods,
         collect(DISTINCT coalesce(rg.rdfs__label, last(split(rg.uri, '/')))) AS regions,
         collect(DISTINCT c.schema__name) AS countries
    RETURN r {
             id: r.uri,
             name: r.schema__name,
             image: r.schema__image,
             yield: r.schema__recipeYield,
             description: r.schema__description,
             instructions: r.schema__recipeInstructions,
             mainIngredient: mi.schema__name,
             countries: countries,
             regions: regions,
             methods: methods
           } AS recipe,
           [ing IN ingredients WHERE ing.name IS NOT NULL] AS ingredients
    """
    
    try:
        results = neo4j.query(query, {"id": recipe_id})
        return results[0] if results else None
    except Exception as e:
        print(f"Error getting recipe details: {e}")
        return None

def get_related_recipes(recipe_id, limit=6):
    neo4j = get_neo4j_service()
    
    query = """
    MATCH (source:schema__Recipe {uri: $id})
    WHERE source.hasVectorEmbedding IS NOT NULL
    CALL db.index.vector.queryNodes('recipes', $limit + 1, source.hasVectorEmbedding) 
    YIELD node AS candidate, score
    WHERE candidate.uri <> $id
    OPTIONAL MATCH (candidate)-[:kb__hasPrimaryIngredient]->(mi:schema__DefinedTerm)
    OPTIONAL MATCH (candidate)-[:schema__recipeCuisine]->(c:schema__DefinedTerm)
    OPTIONAL MATCH (candidate)-[:kb__hasCuisineRegion]->(rg)
    OPTIONAL MATCH (candidate)-[:kb__usesCookingMethod]->(m:schema__DefinedTerm)
    WITH candidate, score, mi.schema__name as mainIngredient,
         collect(DISTINCT c.schema__name) as countries,
         collect(DISTINCT coalesce(rg.rdfs__label, last(split(rg.uri, '/')))) as regions,
         collect(DISTINCT m.schema__name) as methods
    RETURN candidate { 
        id: candidate.uri, 
        name: candidate.schema__name, 
        image: candidate.schema__image,
        yield: candidate.schema__recipeYield,
        mainIngredient: mainIngredient,
        countries: countries,
        regions: regions,
        methods: methods
    } AS recipe, score AS similarity
    """
    
    try:
        results = neo4j.query(query, {"id": recipe_id, "limit": limit})
        for r in results:
            r['sharedIngredients'] = f"{int(r['similarity'] * 100)}% match" 
        return results
    except Exception as e:
        print(f"Error getting related recipes: {e}")
        return []

def get_all_countries():
    neo4j = get_neo4j_service()
    query = "MATCH (c:schema__DefinedTerm {kb__categoryType: 'cuisine'}) RETURN DISTINCT c.schema__name AS name ORDER BY name"
    return [r['name'] for r in neo4j.query(query)]

def get_all_regions():
    neo4j = get_neo4j_service()
    query = "MATCH (r:schema__Recipe)-[:kb__hasCuisineRegion]->(rg) RETURN DISTINCT coalesce(rg.rdfs__label, last(split(rg.uri, '/'))) AS name ORDER BY name"
    return [r['name'] for r in neo4j.query(query)]

def get_all_methods():
    neo4j = get_neo4j_service()
    query = "MATCH (m:schema__DefinedTerm {kb__categoryType: 'cooking_method'}) RETURN DISTINCT m.schema__name AS name ORDER BY name"
    return [r['name'] for r in neo4j.query(query)]

def get_all_ingredients():
    neo4j = get_neo4j_service()
    query = "MATCH (i:kb__Ingredient) RETURN DISTINCT i.rdfs__label AS name ORDER BY name"
    return [r['name'] for r in neo4j.query(query)]

def get_all_main_ingredients():
    neo4j = get_neo4j_service()
    query = """
    MATCH (m:schema__DefinedTerm)
    WHERE EXISTS { MATCH (:schema__Recipe)-[:kb__hasPrimaryIngredient]->(m) }
    RETURN DISTINCT m.schema__name AS name ORDER BY name
    """
    return [r['name'] for r in neo4j.query(query)]

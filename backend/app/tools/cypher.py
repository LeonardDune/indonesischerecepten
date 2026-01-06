from ..llm import llm
from ..services.neo4j import get_neo4j_service
from langchain_neo4j import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate

def cypher_qa(input_question):
    neo4j_service = get_neo4j_service()
    if not neo4j_service.graph:
        return "Sorry, I cannot connect to the database right now."

    CYPHER_GENERATION_TEMPLATE = """
    You are an expert Neo4j Developer translating user questions into Cypher to answer questions about recipes and provide recommendations.
    Convert the user's question based on the schema.

    IMPORTANT: Do not use the automatically inferred schema. Use only the manually provided schema below.

    Schema:
    - Recipes are nodes with label :schema__Recipe
    - Recipes have a property schema__name (string) for the recipe name
    - Cuisine relationships: (:schema__Recipe)-[:schema__recipeCuisine]->(cuisine_node)
      Where cuisine_node has schema__name property: 'indonesian', 'thai', 'chinese', 'filipino', 'korean'
    - Region relationships: (:schema__Recipe)-[:schema__recipeRegion]->(region_node)
      Where region_node has schema__name property: 'bali', 'java', 'sumatra', etc.
    - Cooking method relationships: (:schema__Recipe)-[:schema__cookingMethod]->(method_node)
      Where method_node has schema__name property: 'frituren', 'stoven', 'bakken', etc.

    IMPORTANT: Cuisine/region/method nodes are nodes with schema__name properties, NOT IRI strings!

    For cuisine queries:
    - "Indonesian recipes" -> MATCH (r:schema__Recipe)-[:schema__recipeCuisine]->(c) WHERE c.schema__name = 'indonesian' RETURN r.schema__name AS RecipeName LIMIT 3
    - "Thai recipes" -> MATCH (r:schema__Recipe)-[:schema__recipeCuisine]->(c) WHERE c.schema__name = 'thai' RETURN r.schema__name AS RecipeName LIMIT 3

    For region queries:
    - "Bali recipes" -> MATCH (r:schema__Recipe)-[:schema__recipeRegion]->(reg) WHERE reg.schema__name = 'bali' RETURN r.schema__name AS RecipeName LIMIT 3

    Always return recipe names with: RETURN r.schema__name AS RecipeName LIMIT 3

    Question:
    {question}

    Cypher Query:
    """
    
    cypher_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)
    
    chain = GraphCypherQAChain.from_llm(
        llm,
        graph=neo4j_service.graph,
        verbose=True,
        cypher_prompt=cypher_prompt,
        allow_dangerous_requests=True,
        return_direct=True  # Return raw Cypher results
    )
    
    return chain.invoke(input_question)

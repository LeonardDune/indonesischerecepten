
# vector.py
from ..llm import get_llm, embed_query
from ..services.neo4j import get_neo4j_service
from langchain_neo4j import Neo4jVector
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# Adapter voor lazy MPNet
class QueryEmbeddings:
    def embed_query(self, text):
        return embed_query(text)
    
    def embed_documents(self, texts):
        return [embed_query(t) for t in texts]

def get_recipe(input_text):
    print(f"DEBUG: get_recipe called with: {input_text}")
    neo4j_service = get_neo4j_service()
    if not neo4j_service.graph:
        print("DEBUG: No Neo4j connection")
        return "Sorry, I cannot connect to the database right now."

    try:
        print("DEBUG: Creating Neo4jVector...")
        neo4jvector = Neo4jVector.from_existing_index(
            QueryEmbeddings(),
            graph=neo4j_service.graph,
            index_name="recipes",
            node_label="schema__Recipe",
            text_node_property="schema__recipeInstructions",
            embedding_node_property="hasVectorEmbedding",
            retrieval_query=""" 
            WITH node, score
            OPTIONAL MATCH (node)-[:kb__hasIngredientUsage]->(usage)-[:kb__ingredient]->(ing)
            OPTIONAL MATCH (node)-[:kb__hasDishType]->(dt)
            OPTIONAL MATCH (node)-[:kb__usesCookingMethod]->(method)
            OPTIONAL MATCH (node)-[:kb__hasCuisineRegion]->(reg)
            OPTIONAL MATCH (node)-[:schema__recipeCuisine]->(cuisine)
            OPTIONAL MATCH (node)-[:schema__url]->(urlNode)
            WITH node, score, urlNode, cuisine,
                collect(DISTINCT ing.rdfs__label) AS ingredients,
                collect(DISTINCT dt.schema__name) AS dishes,
                collect(DISTINCT method.schema__name) AS methods,
                collect(DISTINCT last(split(reg.uri, "/"))) AS regions
                RETURN "RECEPT: " + node.schema__name + "\n" + "LAND: " + coalesce(cuisine.schema__name, "Onbekend") + "\n" + "TYPE: " + reduce(s = "", d IN dishes | s + CASE WHEN s = "" THEN "" ELSE ", " END + d) + "\n" + "METHODE: " + reduce(s = "", m IN methods | s + CASE WHEN s = "" THEN "" ELSE ", " END + m) + "\n" + "REGIO: " + reduce(s = "", r IN regions | s + CASE WHEN s = "" THEN "" ELSE ", " END + r) + "\n" + "INGREDIËNTEN: " + reduce(s = "", i IN ingredients | s + CASE WHEN s = "" THEN "" ELSE ", " END + i) + "\n" + "URL: " + coalesce(urlNode.uri, "Geen URL") AS text, score, { name: node.schema__name, url: urlNode.uri, score: score, cuisine: cuisine.schema__name, regions: regions } AS metadata
            """
        )

        print("DEBUG: Neo4jVector created, creating retriever...")
        retriever = neo4jvector.as_retriever(search_kwargs={'k': 15})

        instructions = (
            "Gebruik de gegeven context om een antwoord op de vraag te geven."
            "Als je het niet weet, zeg dan dat je het niet weet."
            "Context: {context}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", instructions),
            ("human", "{input}"),
        ])

        print("DEBUG: Creating question answer chain...")
        llm_instance = get_llm()  # <-- Pas hier de factory toe
        question_answer_chain = create_stuff_documents_chain(llm_instance, prompt)

        plot_retriever = create_retrieval_chain(
            retriever,
            question_answer_chain
        )

        print("DEBUG: Invoking retriever...")
        result = plot_retriever.invoke({"input": input_text})
        print(f"DEBUG: Retriever result: {str(result)[:200]}...")
        return result

    except Exception as e:
        print(f"DEBUG: Exception in get_recipe: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Sorry, er is een fout opgetreden bij het zoeken: {str(e)}"

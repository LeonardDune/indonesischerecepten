from ..llm import llm, embeddings
from ..services.neo4j import get_neo4j_service
from langchain_neo4j import Neo4jVector
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

def get_recipe(input_text):
    neo4j_service = get_neo4j_service()
    if not neo4j_service.graph:
        return "Sorry, I cannot connect to the database right now."

    neo4jvector = Neo4jVector.from_existing_index(
        embeddings,
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

    RETURN
        "RECEPT: " + node.schema__name + "\n" +
        "LAND: " + coalesce(cuisine.schema__name, "Onbekend") + "\n" +
        "TYPE: " + apoc.text.join(dishes, ", ") + "\n" +
        "METHODE: " + apoc.text.join(methods, ", ") + "\n" +
        "REGIO: " + apoc.text.join(regions, ", ") + "\n" +
        "INGREDIËNTEN: " + apoc.text.join(ingredients, ", ") + "\n" +
        "URL: " + coalesce(urlNode.uri, "Geen URL") AS text,
        score,
        {
            name: node.schema__name,
            url: urlNode.uri,
            score: score,
            cuisine: cuisine.schema__name,
            regions: regions
        } AS metadata
    """
    )
    
    retriever = neo4jvector.as_retriever(search_kwargs={'k': 15})
    
    instructions = (
        "Gebruik de gegeven context om een antwoord op de vraag te geven."
        "Als je het niet weet, zeg dan dat je het niet weet."
        "Context: {context}"
    )
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", instructions),
            ("human", "{input}"),
        ]
    )
    
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    plot_retriever = create_retrieval_chain(
        retriever, 
        question_answer_chain
    )
    
    return plot_retriever.invoke({"input": input_text})

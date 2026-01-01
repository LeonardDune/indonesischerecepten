from neo4j import GraphDatabase
from neo4j_graphrag.generation import RagTemplate, GraphRAG
from dotenv import load_dotenv
import os

load_dotenv()

#Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


query_text = "Geef me 5 indonesische recepten met kokos en kip."

# Embeddings model
MODEL_NAME = os.getenv("EMBED_MODEL")

from neo4j_graphrag.embeddings.sentence_transformers import SentenceTransformerEmbeddings
embedder = SentenceTransformerEmbeddings(model=MODEL_NAME)

# LLM Model
from neo4j_graphrag.llm import OpenAILLM
llm=OpenAILLM(
   model_name="gpt-4o",
   model_params={
       #"response_format": {"type": "json_object"}, # use json_object formatting for best results
       "temperature": 0 # turning temperature down for more deterministic results
   },
   api_key=os.getenv('OPENAI_API_KEY')
)

# Vector Retriever
from neo4j_graphrag.retrievers import VectorCypherRetriever

retrieval_query = """
WITH node, score
MATCH (node)-[:kb__hasIngredientUsage]->(usage)-[:kb__ingredient]->(ing)
OPTIONAL MATCH (node)-[:kb__hasDishType]->(dt)
OPTIONAL MATCH (node)-[:kb__usesCookingMethod]->(method)
OPTIONAL MATCH (node)-[:kb__hasCuisineRegion]->(reg)
OPTIONAL MATCH (node)-[:schema__url]->(urlNode)

WITH node, score, urlNode,
     collect(DISTINCT ing.rdfs__label) AS ingredients,
     collect(DISTINCT dt.schema__name) AS dishes,
     collect(DISTINCT method.schema__name) AS methods,
     collect(DISTINCT reg.schema__name) AS regions

RETURN
    "RECEPT: " + node.schema__name + "\n" +
    "TYPE: " + apoc.text.join(dishes, ", ") + "\n" +
    "METHODE: " + apoc.text.join(methods, ", ") + "\n" +
    "REGIO: " + apoc.text.join(regions, ", ") + "\n" +
    "INGREDIËNTEN: " + apoc.text.join(ingredients, ", ") + "\n" +
    "URL: " + coalesce(urlNode.uri, "Geen URL") AS text,
    {
        name: node.schema__name,
        url: urlNode.uri,
        score: score
    } AS metadata
"""

vector_retriever = VectorCypherRetriever(
   driver,
   index_name="recipes",
   embedder=embedder,
   retrieval_query=retrieval_query,
)

#retrieved = vector_retriever.search(
#    query_text=query_text,
#    top_k=15
#)

#print(retrieved)

#Graph RAG setup

prompt_template = RagTemplate(
    system_instructions="""Beantwoord de vraag {query_text} zo volledig mogelijk gebruik makend van de {context}. 
    
    Instructies:
    1. Gebruik uitsluitend de aangeleverde context.
    2. Als de context relevante informatie bevat, vat deze dan samen tot een antwoord, ook als dit geen uitputtende opsomming is.
    3. Benadruk wat er WEL in de tekst staat.
    4. Wees volledig, verwerk alle relevante informatie die in de context staat.
    5. Alleen als er GEEN enkele relevante informatie in de bronnen staat, antwoord dan met 'niet te bepalen op basis van de gegeven bronnen'.""",
    expected_inputs=["context", "query_text"]
)

vector_rag  = GraphRAG(llm=llm, retriever=vector_retriever, prompt_template=prompt_template)

#graph_rag = GraphRAG(llm=llm, retriever=graph_retriever, prompt_template=rag_template)

response = vector_rag.search(query_text=query_text, retriever_config={'top_k':15})
print(response.answer)

#graph_rag.search(q, retriever_config={'top_k':5}).answer
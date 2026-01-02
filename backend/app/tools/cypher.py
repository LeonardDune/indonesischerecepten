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
    
    Use only the provided relationship types and properties in the schema.
    Do not use any other relationship types or properties that are not provided.
    
    Do not return entire nodes or embedding properties.
    
    Schema:
    {schema}
    
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
        allow_dangerous_requests=True
    )
    
    return chain.invoke(input_question)

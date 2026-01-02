import os
from langchain_neo4j import Neo4jGraph
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the backend directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_graph_connection():
    try:
        return Neo4jGraph(
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
        )
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        return None

class Neo4jService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jService, cls).__new__(cls)
            cls._instance.graph = get_graph_connection()
        return cls._instance

    def query(self, query, params=None):
        if self.graph:
            return self.graph.query(query, params)
        return []

def get_neo4j_service():
    return Neo4jService()

import streamlit as st
from langchain_neo4j import Neo4jGraph

@st.cache_resource
def get_graph_connection():
    try:
        return Neo4jGraph(
            url=st.secrets["NEO4J_URI"],
            username=st.secrets["NEO4J_USERNAME"],
            password=st.secrets["NEO4J_PASSWORD"],
            database=st.secrets["NEO4J_DATABASE"],
        )
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {e}")
        return None

class Neo4jService:
    def __init__(self):
        self.graph = get_graph_connection()

    def query(self, query, params=None):
        if self.graph:
            return self.graph.query(query, params)
        return []

def get_neo4j_service():
    return Neo4jService()

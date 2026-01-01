from rdflib_neo4j import Neo4jStoreConfig
from rdflib_neo4j import HANDLE_VOCAB_URI_STRATEGY
from rdflib_neo4j import Neo4jStore
from rdflib import Graph, Namespace
from dotenv import load_dotenv
import os

load_dotenv()

# --- Connection configuration -------------------------------------------------
auth_data = {
    'uri': os.getenv('NEO4J_URI'),
    'database': os.getenv('NEO4J_DATABASE', 'neo4j'),
    'user': os.getenv('NEO4J_USERNAME'),
    'pwd': os.getenv('NEO4J_PASSWORD')
}

# --- Recipe KG Prefixes -------------------------------------------------------
prefixes = {
    'kb': Namespace('https://purl.archive.org/purl/recipes/kokkieblanda/kg/'),
    'kbr': Namespace('https://purl.archive.org/purl/recipes/kokkieblanda/kg/recipe/'),
    'schema': Namespace('https://schema.org/'),
    'ing': Namespace('https://purl.archive.org/purl/recipes/kokkieblanda/kg/ingredient/'),
    'cuisine': Namespace('https://purl.archive.org/purl/recipes/kokkieblanda/kg/category/cuisine/'),
    'unit': Namespace('https://purl.archive.org/purl/recipes/kokkieblanda/kg/unit/'),
    'dt': Namespace('https://purl.archive.org/purl/recipes/kokkieblanda/kg/category/dish-type/'),
    'method': Namespace('https://purl.archive.org/purl/recipes/kokkieblanda/kg/category/cooking-method/'),
    'reg': Namespace('https://purl.archive.org/purl/recipes/kokkieblanda/kg/category/region/'),
    'emb': Namespace('https://purl.archive.org/purl/recipes/kokkieblanda/kg/embedding#'),
    'rdf': Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
    'rdfs': Namespace('http://www.w3.org/2000/01/rdf-schema#'),
    'skos': Namespace('http://www.w3.org/2004/02/skos/core#'),
}

# --- Import Configuration -----------------------------------------------------
config = Neo4jStoreConfig(
    auth_data=auth_data,
    custom_prefixes=prefixes,
    handle_vocab_uri_strategy=HANDLE_VOCAB_URI_STRATEGY.SHORTEN, # Use prefixes in Neo4j
    batching=True
)

# Files to import sequentially
import_files = [
    './kokkieblanda.ttl'
]

# --- Execution ----------------------------------------------------------------
try:
    graph_store = Graph(store=Neo4jStore(config=config))
    
    for file_path in import_files:
        if os.path.exists(file_path):
            print(f"Importing {file_path} into Neo4j...")
            graph_store.parse(file_path, format="ttl")
        else:
            print(f"Warning: File {file_path} not found. Skipping.")
            
    graph_store.close(True)
    print("Import completed successfully.")
except Exception as e:
    print(f"Error during import: {e}")
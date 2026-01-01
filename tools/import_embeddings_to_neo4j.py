from rdflib import Graph, Namespace
from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv

load_dotenv()

# --- Neo4j connectie ---
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USERNAME")
pwd = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, pwd))

# --- Namespaces ---
EMB_NS = Namespace("https://purl.archive.org/purl/recipes/kokkieblanda/kg/embedding#")
HAS_VEC = EMB_NS.hasVectorEmbedding

# --- TTL met embeddings ---
ttl_file = "./kokkieblanda_with_embeddings.ttl"

if not os.path.exists(ttl_file):
    print(f"Error: {ttl_file} not found.")
    exit(1)

print(f"Loading embeddings from {ttl_file}...")
g = Graph()
g.parse(ttl_file, format="ttl")

# --- Parameters ---
BATCH_SIZE = 100

def parse_embedding(embedding_str):
    """Zet JSON string van embedding om naar lijst van floats"""
    return [float(x) for x in json.loads(embedding_str)]

def update_batch(tx, batch):
    """
    Update een batch van nodes met vector embedding.
    MATCH op 'uri' property (standaard voor rdflib-neo4j)
    """
    query = """
    UNWIND $batch AS row
    MATCH (n {uri: row.uri})
    SET n.hasVectorEmbedding = row.embedding
    """
    tx.run(query, batch=batch)

# --- Batch verwerking ---
batch = []
count = 0

print("Starting ingestion into Neo4j...")
with driver.session() as session:
    for s, p, o in g.triples((None, HAS_VEC, None)):
        recipe_uri = str(s)
        try:
            embedding = parse_embedding(str(o))
            batch.append({"uri": recipe_uri, "embedding": embedding})
            count += 1
            
            if len(batch) >= BATCH_SIZE:
                session.execute_write(update_batch, batch)
                print(f"Ingested {count} embeddings...")
                batch = []
        except Exception as e:
            print(f"Skipping {recipe_uri} due to error: {e}")

    # laatste batch
    if batch:
        session.execute_write(update_batch, batch)
        print(f"Ingested {count} total embeddings.")

driver.close()
print("Done.")

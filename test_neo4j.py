#!/usr/bin/env python3

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

# Load environment
env_path = Path("backend/.env")
load_dotenv(dotenv_path=env_path)

# Connect to Neo4j
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE", "neo4j"),
)

# Test queries
print("=== Sample recipes ===")
result = graph.query("MATCH (r:schema__Recipe) RETURN r.schema__name AS name LIMIT 5")
for row in result:
    print(row)

print("\n=== Cuisine relationships ===")
result = graph.query("MATCH (r:schema__Recipe)-[:schema__recipeCuisine]->(c) RETURN r.schema__name AS recipe, c AS cuisine LIMIT 5")
for row in result:
    print(row)

print("\n=== Thai recipes ===")
result = graph.query("MATCH (r:schema__Recipe)-[:schema__recipeCuisine]->(c) WHERE c = 'cuisine__thai' RETURN r.schema__name AS recipe LIMIT 3")
for row in result:
    print(row)

print("\n=== Indonesian recipes ===")
result = graph.query("MATCH (r:schema__Recipe)-[:schema__recipeCuisine]->(c) WHERE c = 'cuisine__indonesian' RETURN r.schema__name AS recipe LIMIT 3")
for row in result:
    print(row)

print("\n=== Correct query ===")
result = graph.query("MATCH (r:schema__Recipe)-[:schema__recipeCuisine]->(c) WHERE c.schema__name = 'thai' RETURN r.schema__name AS recipe LIMIT 3")
for row in result:
    print(row)

print("\n=== Wrong query (old way) ===")
result = graph.query("MATCH (r:schema__Recipe)-[:schema__recipeCuisine]->(c:schema__DefinedTerm) WHERE c.schema__name = 'Thailand' RETURN r.schema__name AS RecipeName LIMIT 3")
for row in result:
    print(row)

graph.close()

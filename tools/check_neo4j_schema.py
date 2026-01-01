from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USERNAME")
pwd = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, pwd))

def get_schema(tx):
    print("--- Labels ---")
    result = tx.run("CALL db.labels()")
    for record in result:
        print(record[0])
        
    print("\n--- Relationship Types ---")
    result = tx.run("CALL db.relationshipTypes()")
    for record in result:
        print(record[0])
        
    print("\n--- Property Keys ---")
    result = tx.run("CALL db.propertyKeys()")
    for record in result:
        print(record[0])

    print("\n--- Example Recipe Node ---")
    result = tx.run("MATCH (n:Resource) WHERE n.uri CONTAINS 'ampela-ayam-peteh' RETURN labels(n) as labels, keys(n) as keys LIMIT 1")
    for record in result:
        print(f"Labels: {record['labels']}")
        print(f"Keys: {record['keys']}")

with driver.session() as session:
    session.execute_read(get_schema)

driver.close()

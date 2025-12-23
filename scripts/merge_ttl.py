from rdflib import Graph
import sys

def merge(files, output):
    g = Graph()
    for f in files:
        print(f"Parsing {f}...")
        g.parse(f, format="turtle")
    
    print(f"Serializing to {output}...")
    g.serialize(destination=output, format="turtle")
    print("Done.")

if __name__ == "__main__":
    files = ["kokkieblanda_indonesian_v1.ttl", "kokkieblanda_others_v1.ttl"]
    merge(files, "kokkieblanda_full_v1.ttl")

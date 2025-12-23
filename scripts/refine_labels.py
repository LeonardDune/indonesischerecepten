import re
from rdflib import Graph, RDFS, Namespace, Literal, RDF

def clean_label(text):
    if not text: return ""
    text = text.lower().strip()
    
    # 1. Remove obvious noise at start/end (punctuation, stars)
    text = re.sub(r'^[\s,.*\\/]+', '', text)
    text = re.sub(r'[\s,.*\\/]+$', '', text)
    
    # 2. Cleanup internal noise (replace with single space)
    text = text.replace(',', ' ').replace('*', ' ').replace('\\', ' ').replace('/', ' ')
    text = text.replace('(', ' ').replace(')', ' ')
    
    # 3. Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 4. Remove missed fractions or quantities at start (since this is an ontology label)
    text = re.sub(r'^[½⅓¼¾\d\.\,/]+', '', text).strip()
    
    return text

def refine_ttl(input_file, output_file):
    g = Graph()
    print(f"Loading {input_file}...")
    g.parse(input_file, format="turtle")
    
    KB = Namespace("https://www.kokkieblanda.nl/kg/")
    
    print("Identifying labels to clean...")
    to_remove = []
    to_add = []
    
    # Process all RDFS.label triples
    for s, p, o in g.triples((None, RDFS.label, None)):
        # Only clean labels for Ingredients and Units
        types = list(g.objects(s, RDF.type))
        if KB.Ingredient in types or KB.Unit in types:
            raw_val = str(o)
            cleaned_val = clean_label(raw_val)
            if cleaned_val != raw_val:
                to_remove.append((s, p, o))
                # Add cleaned version if not empty
                if cleaned_val:
                    to_add.append((s, p, Literal(cleaned_val)))
                else:
                    # If empty, maybe use the slug as fallback or just remove
                    pass

    print(f"Applying {len(to_remove)} removals and {len(to_add)} additions...")
    for t in to_remove:
        g.remove(t)
    for t in to_add:
        g.add(t)
        
    print(f"Saving to {output_file}...")
    g.serialize(destination=output_file, format="turtle")
    print("Done.")

if __name__ == "__main__":
    refine_ttl("kokkieblanda_full_v1.ttl", "kokkieblanda_full_v2.ttl")

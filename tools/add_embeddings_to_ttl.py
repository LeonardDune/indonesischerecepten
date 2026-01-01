import os
import json
import sys
import re
from dotenv import load_dotenv

load_dotenv()

# --- dependencies -------------------------------------------------------------

try:
    from rdflib import Graph, Namespace, Literal, URIRef
    from rdflib.namespace import RDF, RDFS, XSD
except Exception:
    print("Missing dependency: rdflib. Install with: python3 -m pip install rdflib", file=sys.stderr)
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    print("Missing dependency: sentence-transformers. Install with: python3 -m pip install sentence-transformers", file=sys.stderr)
    sys.exit(1)

# --- configuration ------------------------------------------------------------

INPUT_TTL = os.getenv("INPUT_TTL_PATH", "./kokkieblanda.ttl")
OUTPUT_TTL = os.getenv("OUTPUT_TTL_PATH", "./kokkieblanda_with_embeddings.ttl")

MODEL_NAME = os.getenv(
    "EMBED_MODEL",
    "sentence-transformers/all-mpnet-base-v2"
)

# --- namespaces ---------------------------------------------------------------    

SCHEMA = Namespace("https://schema.org/")
KB = Namespace("https://purl.archive.org/purl/recipes/kokkieblanda/kg/")
EMB = Namespace("https://purl.archive.org/purl/recipes/kokkieblanda/kg/embedding#")

# --- load graph ---------------------------------------------------------------

print(f"Loading graph from {INPUT_TTL}...")
g = Graph()
g.parse(INPUT_TTL, format="turtle")

g_out = Graph()
# Standard bindings for consistency
g_out.bind("emb", EMB)
g_out.bind("kb", KB)
g_out.bind("schema", SCHEMA)

# --- load embedding model -----------------------------------------------------

print(f"Loading model {MODEL_NAME}...")
sbert = SentenceTransformer(MODEL_NAME)

# --- helper functions ---------------------------------------------------------

def normalize_label(text: str) -> str:
    """
    Normalize ingredient labels:
    - lowercase
    - trim whitespace
    - strip leading/trailing punctuation
    """
    text = text.strip().lower()
    text = re.sub(r"^[^\w]+|[^\w]+$", "", text)
    return text.strip()


def ingredient_name(graph: Graph, node: URIRef) -> str:
    """
    Prefer normalized rdfs:label from kb:Ingredient node.
    Fallback to URI fragment if no usable label exists.
    """
    labels = []

    for o in graph.objects(node, RDFS.label):
        norm = normalize_label(str(o))
        if norm:
            labels.append(norm)

    if labels:
        # deterministic: shortest first, then lexicographically
        return sorted(set(labels), key=lambda x: (len(x), x))[0]

    # fallback: URI fragment
    if isinstance(node, URIRef):
        local = str(node).split("/")[-1].split("#")[-1]
        return local.replace("-", " ").lower()

    return str(node).lower()

# --- embedding loop (Batched) -------------------------------------------------

recipes = sorted(
    {s for s in g.subjects(RDF.type, SCHEMA.Recipe)},
    key=lambda n: str(n)
)

print(f"Found {len(recipes)} recipes to process.")

texts = []
subjects = []

for recipe in recipes:
    # skip if embedding already exists in source graph
    if (recipe, EMB.hasVectorEmbedding, None) in g:
        continue

    parts = []
    
    # --- TITEL (Crucial for relevance) ----------------------------------------
    title = g.value(recipe, SCHEMA.name)
    if title:
        parts.append(f"TITEL: {str(title)}")

    # --- INGREDIENTEN (genormaliseerd) ----------------------------------------
    ingredient_nodes = set()

    for usage in g.objects(recipe, KB.hasIngredientUsage):
        for ing in g.objects(usage, KB.ingredient):
            ingredient_nodes.add(ing)

    ingredient_labels = sorted(
        ingredient_name(g, ing) for ing in ingredient_nodes
    )

    if ingredient_labels:
        parts.append("INGREDIENTEN:")
        parts.extend(ingredient_labels)

    # --- BEREIDING -------------------------------------------------------------
    instructions = sorted(
        str(o) for o in g.objects(recipe, SCHEMA.recipeInstructions)
    )

    if instructions:
        parts.append("BEREIDING:")
        parts.extend(instructions)

    # --- KEUKEN / CUISINE ------------------------------------------------------
    cuisines = sorted(
        str(o).split("/")[-1].replace("-", " ").lower()
        for o in g.objects(recipe, SCHEMA.recipeCuisine)
    )

    if cuisines:
        parts.append("KEUKEN:")
        parts.extend(cuisines)

    # --- PRIMAIRE INGREDIËNTEN -------------------------------------------------
    primary_ingredients = sorted(
        ingredient_name(g, o)
        for o in g.objects(recipe, KB.hasPrimaryIngredient)
    )

    if primary_ingredients:
        parts.append("PRIMAIRE INGREDIËNTEN:")
        parts.extend(primary_ingredients)

    # --- final text ------------------------------------------------------------
    text = "\n".join(p for p in parts if p and p.strip())
    if text.strip():
        texts.append(text)
        subjects.append(recipe)

print(f"Collected {len(texts)} recipe contexts. Starting batched embedding...")

# Process in batches
BATCH_SIZE = 64
all_embeddings = []

for i in range(0, len(texts), BATCH_SIZE):
    batch_texts = texts[i:i + BATCH_SIZE]
    print(f"Processing batch {i//BATCH_SIZE + 1} ({i} to {min(i+BATCH_SIZE, len(texts))})...")
    batch_emb = sbert.encode(batch_texts, convert_to_numpy=True)
    all_embeddings.extend(batch_emb)

# Add to graph
for recipe, emb in zip(subjects, all_embeddings):
    emb_list = emb.tolist()
    g_out.add((
        recipe,
        EMB.hasVectorEmbedding,
        Literal(json.dumps(emb_list), datatype=XSD.string)
    ))

# --- serialize result ---------------------------------------------------------

print(f"Serializing result to {OUTPUT_TTL}...")
g_out.serialize(destination=OUTPUT_TTL, format="turtle")
print(f"Wrote {len(subjects)} embeddings to {OUTPUT_TTL}")

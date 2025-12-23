import os
import json
import sys
from dotenv import load_dotenv
load_dotenv()

try:
    from rdflib import Graph, Namespace, Literal
    from rdflib.namespace import DCTERMS, XSD, RDFS
except Exception:
    print("Missing dependency: rdflib. Install with: python3 -m pip install rdflib", file=sys.stderr)
    sys.exit(1)

# use sentence-transformers + specified HF model for embeddings
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    print("Missing dependency: sentence-transformers. Install with: python3 -m pip install sentence-transformers", file=sys.stderr)
    sys.exit(1)

INPUT_TTL = os.getenv("INPUT_TTL_PATH", "legal-agent/data/wetboek.ttl")
OUTPUT_TTL = os.getenv("OUTPUT_TTL_PATH", "legal-agent/data/wetboek_with_embeddings.ttl")

# Namespaces
EMB = Namespace("https://purl.org/strafrechtketen/nwvs/embedding#")

g = Graph()
g.parse(INPUT_TTL, format="turtle")

# Create a separate graph for output
g_out = Graph()
g_out.bind("emb", EMB)


# load HF model (default to the requested Dutch model)
MODEL_NAME = os.getenv("EMBED_MODEL", "textgain/allnli-GroNLP-bert-base-dutch-cased")
sbert = SentenceTransformer(MODEL_NAME)

count = 0

# build deterministic list of subjects to consider
subjects = sorted({s for s in g.subjects()}, key=lambda n: str(n))
for s in subjects:
    # skip if embedding already present
    if (s, EMB.hasVectorEmbedding, None) in g:
        continue

    # required fields: identifier AND label
    identifiers = sorted({str(o) for o in g.objects(s, DCTERMS.identifier)})
    labels = sorted({str(o) for o in g.objects(s, RDFS.label)})
    if not identifiers or not labels:
        continue

    parts = []
    parts.extend(identifiers)
    parts.extend(labels)

    # optional description(s)
    descriptions = sorted({str(o) for o in g.objects(s, DCTERMS.description)})
    parts.extend(descriptions)

    # optional references (could be literals or URIs)
    references = sorted({str(o) for o in g.objects(s, DCTERMS.references)})
    parts.extend(references)

    # optional hasPart: try rdfs:label, then dcterms:description, else fallback to str(part)
    hasparts = sorted({o for o in g.objects(s, DCTERMS.hasPart)}, key=lambda n: str(n))
    haspart_texts = []
    for part in hasparts:
        part_labels = sorted({str(o) for o in g.objects(part, RDFS.label)})
        if part_labels:
            haspart_texts.extend(part_labels)
            continue
        part_descs = sorted({str(o) for o in g.objects(part, DCTERMS.description)})
        if part_descs:
            haspart_texts.extend(part_descs)
            continue
        haspart_texts.append(str(part))

    parts.extend(haspart_texts)

    # deterministic concatenation
    text = "\n".join([p for p in parts if p and p.strip()])
    if not text.strip():
        continue

    # compute embedding and normalize to Python list
    emb = sbert.encode(text)
    try:
        emb_list = emb.tolist()
    except Exception:
        emb_list = list(emb) if not isinstance(emb, list) else emb

    # store only the JSON array literal on the subject in the NEW graph
    g_out.add((s, EMB.hasVectorEmbedding, Literal(json.dumps(emb_list), datatype=XSD.string)))

    count += 1
    print(f"Embedded {count}: {s}")

# Serialize ONLY the new graph to the output path
g_out.serialize(destination=OUTPUT_TTL, format="turtle")
print(f"Wrote {count} embeddings to {OUTPUT_TTL}")
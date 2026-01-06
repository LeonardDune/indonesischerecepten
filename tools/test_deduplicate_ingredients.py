#!/usr/bin/env python3

import os, json
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT = """Je bent een expert in culinaire ontologie voor recepten.

Ontleed het volgende ingrediënt.

BELANGRIJKE REGELS:
- Gebruik uitsluitend Nederlandse termen.
- base_ingredient is het meest gangbare zelfstandige CULINAIRE ingrediënt zoals gebruikt in recepten.
- Ga NIET terug naar botanische, biologische of chemische oorsprong.
- Variant is een specifieke soort, culturele benaming of subvorm.
- Bewerking (snijden, malen, persen) komt in preparation.
- Vorm (vloeibaar, vast, poeder) komt in form.
- base_ingredient mag GEEN generieke categorie zijn (zoals vlees, suiker, olie, melk, kokos).
- Als een ingrediënt als zelfstandig product in de supermarkt voorkomt en in recepten direct wordt gebruikt, dan is DAT het base_ingredient.

Ingrediënt:
"{label}"

Geef uitsluitend geldige JSON met:
- base_ingredient
- variant
- form
- preparation (lijst)

"""

QUERY = """
MATCH (i:kb__Ingredient)
WHERE i.rdfs__label IN $labels
RETURN i.rdfs__label AS label
"""

labels = [
    "sjalotten gesnipperd",
    "ui fijngesneden",
    "dun gesneden runderlappen",
    "rundvlees",
    "kipfilet in blokjes",
    "kokosmelk",
    "santen",
    "gula jawa",
    "palmsuiker"
]

with driver.session() as s:
    rows = s.run(QUERY, labels=labels).data()

for r in rows:
    label = r["label"]
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": PROMPT.format(label=label)}],
    )

    parsed = json.loads(response.choices[0].message.content)

    print("\n==============================")
    print("INPUT :", label)
    print("OUTPUT:", json.dumps(parsed, indent=2, ensure_ascii=False))

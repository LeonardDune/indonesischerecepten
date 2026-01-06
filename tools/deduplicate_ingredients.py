#!/usr/bin/env python3
"""
Test-script voor canonicalisatie van ingrediënten.

- Leest willekeurige kb__Ingredient nodes uit Neo4j
- Laat LLM base_ingredient / variant / form / preparation bepalen
- Maakt of hergebruikt kb__CanonicalIngredient
- Legt :kb__CANONICALIZES_TO relatie
- GEEN destructieve merges
"""

import os
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_LIMIT = 10
BATCH_SIZE = 5
RATE_LIMIT_SECONDS = 0.8
MAX_RETRIES = 3

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if not ENV_PATH.exists():
    raise RuntimeError(f".env not found at {ENV_PATH}")

load_dotenv(dotenv_path=ENV_PATH, override=True)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

missing = [k for k, v in {
    "NEO4J_URI": NEO4J_URI,
    "NEO4J_USERNAME": NEO4J_USER,
    "NEO4J_PASSWORD": NEO4J_PASSWORD,
    "OPENAI_API_KEY": OPENAI_API_KEY,
}.items() if not v]

if missing:
    raise RuntimeError(f"Missing environment variables: {missing}")

# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

client = OpenAI(api_key=OPENAI_API_KEY)

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    filename="ingredient_canonical_test.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

# ---------------------------------------------------------------------------
# Cypher
# ---------------------------------------------------------------------------

FETCH_INGREDIENTS = """
MATCH (i:kb__Ingredient)
WITH i, rand() AS r
RETURN i.uri AS uri,
       i.rdfs__label AS label
ORDER BY r
LIMIT $limit
"""

MERGE_CANONICAL = """
MATCH (i:kb__Ingredient {uri: $uri})
MERGE (c:kb__CanonicalIngredient {
    base_ingredient: $base,
    form: $form
})
ON CREATE SET
    c.uri = $canon_uri
MERGE (i)-[:kb__CANONICALIZES_TO]->(c)
"""

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """
Je bent een culinair ontologie-expert.

Je krijgt één ingrediënt zoals die letterlijk in een recept voorkomt.

Doel:
Bepaal het meest specifieke, zelfstandige ingrediënt dat als canonieke node kan bestaan,
zonder te generaliseren naar categorieën.

Geef exact één JSON-object terug met deze velden:

- base_ingredient (verplicht):
  Het meest specifieke ingrediënt dat logisch kan worden gekocht of benoemd.
  NOOIT abstraheren naar hogere categorieën.
  FOUT: vlees, vis, lap, groente
  GOED: runderlap, ikan teri, kipfilet, habanero peper
  Gebruik enkelvoudsvorm.

- variant (optioneel, anders null):
  Alleen gebruiken voor:
  - botanische soort of cultivar
  - dierlijke soort
  - anatomisch deel
  NIET gebruiken voor:
  - kwaliteit (mals, jong)
  - kleur (groen, rood)
  - grootte of hoeveelheid

- form (verplicht):
  Kies exact één uit:
  vast | vloeibaar | poeder | pasta

- preparation (verplicht, lijst):
  Een lijst van echte handelingen:
  snijden, hakken, drogen, koken, fermenteren, etc.
  Leeg indien niet van toepassing.

Speciale regels:
- Samengestelde, erkende producten NIET splitsen:
  bakso ikan, petis udang, sambal, kimchi, acar, tofu, tempeh.
- Verwijder hoeveelheden, maten en kwaliteitsaanduidingen volledig.
- Generaliseer NOOIT naar een hypernym.
- Output moet geldige JSON zijn, zonder extra tekst.

Ingrediënt:
"{label}"

"""

# ---------------------------------------------------------------------------
# GPT Call
# ---------------------------------------------------------------------------

def call_gpt(label: str) -> Dict[str, Any]:
    prompt = PROMPT_TEMPLATE.format(label=label)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content
            logging.info("Raw GPT output for '%s': %s", label, raw)

            return json.loads(raw)

        except Exception as exc:
            wait = 2 ** attempt
            logging.warning(
                "GPT failed for '%s' (attempt %s): %s – retry in %ss",
                label, attempt, exc, wait
            )
            time.sleep(wait)

    raise RuntimeError(f"GPT failed after {MAX_RETRIES} retries for '{label}'")

# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def process(session, records: List[Dict[str, Any]], dry_run: bool):
    for r in records:
        label = r["label"]
        uri = r["uri"]

        logging.info("Processing ingredient: %s", label)

        result = call_gpt(label)

        base = result["base_ingredient"]
        form = result.get("form")

        canon_uri = (
            f"https://purl.archive.org/purl/recipes/kokkieblanda/kg/canonical/"
            f"{base.replace(' ', '-')}"
        )

        logging.info(
            "Parsed: base=%s variant=%s form=%s prep=%s",
            base,
            result.get("variant"),
            form,
            result.get("preparation"),
        )

        if dry_run:
            logging.info(
                "[DRY-RUN] Would link %s -> (%s | %s)",
                label, base, form
            )
            continue

        session.run(
            MERGE_CANONICAL,
            uri=uri,
            base=base,
            form=form,
            canon_uri=canon_uri,
        )

        time.sleep(RATE_LIMIT_SECONDS)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                        help="Aantal willekeurige ingrediënten")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with driver.session() as session:
        records = session.run(
            FETCH_INGREDIENTS,
            limit=args.limit
        ).data()

        logging.info("Fetched %s ingredients", len(records))
        process(session, records, dry_run=args.dry_run)

    driver.close()
    logging.info("Finished test canonicalisation")

if __name__ == "__main__":
    main()

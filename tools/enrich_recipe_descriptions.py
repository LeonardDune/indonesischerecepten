#!/usr/bin/env python3
"""
Enrich schema__Recipe nodes by:
- Converting free-text recipeInstructions into numbered steps
- Generating a short description mentioning recipe name and main ingredient
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
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_BATCH_SIZE = 10
RATE_LIMIT_SECONDS = 0.8
MAX_RETRIES = 3

# ---------------------------------------------------------------------------
# Environment loading
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

missing = [
    k for k, v in {
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USERNAME": NEO4J_USER,
        "NEO4J_PASSWORD": NEO4J_PASSWORD,
        "OPENAI_API_KEY": OPENAI_API_KEY,
    }.items() if not v
]

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
    filename="enrich_full.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

# ---------------------------------------------------------------------------
# Cypher Queries
# ---------------------------------------------------------------------------

FETCH_QUERY = """
MATCH (r:schema__Recipe)
OPTIONAL MATCH (r)-[:kb__hasPrimaryIngredient]->(mi:schema__DefinedTerm)
WITH r,
     collect(DISTINCT mi.schema__name) AS mainIng
RETURN r.uri AS id,
       r.schema__name AS name,
       r.schema__recipeInstructions AS rawInstr,
       mainIng,
       coalesce(r.description, "") AS existingDesc
ORDER BY name
SKIP $skip
LIMIT $limit
"""

UPDATE_QUERY = """
MATCH (r:schema__Recipe {uri: $id})
SET r.schema__recipeInstructions = $instructions,
    r.description = $short_description
"""

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """Je bent een wereldberoemde chef.

Gebruik de informatie hieronder en maak:
1. Een genummerde lijst van duidelijke kookstappen in Nederlands (beginnend bij 1, geen extra uitleg of commentaar).
2. Een korte, aantrekkelijke beschrijving (max twee zinnen) in Nederlands waarin de naam van het recept en het hoofdingrediënt genoemd worden.

Zorg dat de instructies genummerd zijn als "1. ...", "2. ...", enzovoort.

Receptnaam: {name}
Hoofdingrediënt: {main_ing}
Originele instructies:
{raw_instr}

BELANGRIJK: Retourneer ALLEEN geldige JSON met keys "instructions" en "short_description".
"""


# ---------------------------------------------------------------------------
# GPT Call
# ---------------------------------------------------------------------------

def call_gpt(prompt: str) -> Dict[str, Any]:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            raw_content = response.choices[0].message.content
            logging.info("Raw GPT output: %s", raw_content)

            if not raw_content or not raw_content.strip():
                raise ValueError("Empty response from GPT")

            result = json.loads(raw_content.strip())
            return result

        except Exception as exc:
            last_error = exc
            wait = 2 ** attempt
            logging.warning(
                "GPT call failed (attempt %s/%s): %s – retrying in %ss",
                attempt,
                MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)

    raise RuntimeError(f"GPT call failed after {MAX_RETRIES} retries: {last_error}")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def should_skip(record: Dict[str, Any], force: bool) -> bool:
    if force:
        return False
    if not record.get("rawInstr"):
        logging.info("Skipping %s: geen instructies", record.get("name"))
        return True
    if record.get("existingDesc"):
        return True
    return False

# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

def process_batch(
    session,
    records: List[Dict[str, Any]],
    dry_run: bool,
    force: bool,
):
    updates = []

    for r in records:
        if should_skip(r, force):
            continue

        main_ing = r["mainIng"][0] if isinstance(r.get("mainIng"), list) and r["mainIng"] else "onbekend"

        prompt = PROMPT_TEMPLATE.format(
            name=r.get("name", "onbekend"),
            main_ing=main_ing,
            raw_instr=r.get("rawInstr"),
        )

        logging.info("Enriching recipe: %s", r.get("name"))

        try:
            result = call_gpt(prompt)
            instructions = result.get("instructions")
            short_description = result.get("short_description")

            logging.info(
                "Parsed GPT output for '%s': instructions=%s, short_description=%s",
                r.get("name"),
                instructions,
                short_description,
            )

            if not instructions or not short_description:
                logging.warning("Incomplete GPT output for %s, skipping", r.get("name"))
                continue

            updates.append({
                "id": r["id"],
                "instructions": instructions,
                "short_description": short_description,
            })

            time.sleep(RATE_LIMIT_SECONDS)

        except Exception as exc:
            logging.error("GPT call failed for %s: %s", r.get("name"), exc)
            continue

    if dry_run:
        for u in updates:
            logging.info(
                "[DRY-RUN] Would update recipe %s: instructions=%s, description=%s",
                u["id"], u["instructions"], u["short_description"]
            )
        return

    if updates:
        logging.info("Writing %d recipes to Neo4j", len(updates))
        with session.begin_transaction() as tx:
            for u in updates:
                logging.info(
                    "Updating recipe %s", u["id"]
                )
                tx.run(
                    UPDATE_QUERY,
                    id=u["id"],
                    instructions=u["instructions"],
                    short_description=u["short_description"],
                )
            tx.commit()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-records", type=int, default=None,
                        help="Stop na maximaal N recepten")
    args = parser.parse_args()

    skip = 0
    processed = 0

    with driver.session() as session:
        while True:
            records = session.run(
                FETCH_QUERY,
                skip=skip,
                limit=args.batch_size,
            ).data()

            if not records:
                break

            logging.info("Processing batch: skip=%s limit=%s", skip, args.batch_size)
            process_batch(
                session=session,
                records=records,
                dry_run=args.dry_run,
                force=args.force,
            )

            batch_count = len(records)
            skip += batch_count
            processed += batch_count

            if args.max_records and processed >= args.max_records:
                logging.info("Reached max-records limit (%s), stopping.", args.max_records)
                break

    driver.close()
    logging.info("Finished enrichment")

if __name__ == "__main__":
    main()

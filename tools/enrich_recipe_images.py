import time
import requests
import datetime
import argparse
from services.neo4j import Neo4jService
import streamlit as st
import os

try:
    import tomllib  # Python 3.11+
except ImportError:
    import toml as tomllib # Fallback if toml is installed

# Configuration
# Assuming these are in .streamlit/secrets.toml
# NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE
# UNSPLASH_ACCESS_KEY

def get_unsplash_image(query, access_key):
    """Fetches a landscape image URL from Unsplash."""
    if not access_key:
        return None
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "orientation": "landscape",
        "content_filter": "high",
        "per_page": 1,
        "client_id": access_key
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 403:
            return "RATE_LIMIT"
        response.raise_for_status()
        data = response.json()
        if data["results"]:
            return data["results"][0]["urls"]["regular"]
    except Exception as e:
        print(f"Error fetching from Unsplash: {e}")
    return None

def get_pixabay_image(query, api_key):
    """Fetches a landscape image URL from Pixabay."""
    if not api_key:
        return None
    url = "https://pixabay.com/api/"
    params = {
        "key": api_key,
        "q": query,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "per_page": 3
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["hits"]:
            # Pick the largest available preview or webformat
            return data["hits"][0]["webformatURL"]
    except Exception as e:
        print(f"Error fetching from Pixabay: {e}")
    return None

def enrich_recipes(limit=None, force=False):
    # Attempt to read secrets
    secrets = {}
    try:
        # Try streamlit secrets first
        secrets = st.secrets
    except Exception:
        # Fallback: Read .streamlit/secrets.toml manually
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            with open(secrets_path, "rb") as f:
                try:
                    import tomllib
                    secrets = tomllib.load(f)
                except Exception:
                    # Very basic parser if no toml library
                    for line in f.read().decode().splitlines():
                        if "=" in line:
                            k, v = line.split("=", 1)
                            secrets[k.strip()] = v.strip().strip('"').strip("'")

    neo4j_uri = secrets.get("NEO4J_URI")
    neo4j_user = secrets.get("NEO4J_USERNAME")
    neo4j_password = secrets.get("NEO4J_PASSWORD")
    unsplash_key = secrets.get("UNSPLASH_ACCESS_KEY")
    pixabay_key = secrets.get("PIXABAY_API_KEY")

    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        print("Error: Required Neo4j secrets missing.")
        return
    
    if not unsplash_key and not pixabay_key:
        print("Error: No image provider keys found (UNSPLASH_ACCESS_KEY or PIXABAY_API_KEY).")
        return

    neo4j = Neo4jService()
    
    # Fetch recipes with their cuisine and primary ingredient
    # Skip recipes that already have an Unsplash image unless 'force' is True
    query = """
    MATCH (r:schema__Recipe)
    WHERE $force = True OR r.schema__image IS NULL OR NOT r.schema__image STARTS WITH 'https://images.unsplash.com'
    OPTIONAL MATCH (r)-[:schema__recipeCuisine]->(c:schema__DefinedTerm)
    OPTIONAL MATCH (r)-[:kb__hasPrimaryIngredient]->(mi:schema__DefinedTerm)
    RETURN r.uri as uri, r.schema__name as name, 
           c.schema__name as cuisine, 
           mi.schema__name as primary_ingredient
    """
    if limit:
        query += f" LIMIT {limit}"
    
    recipes = neo4j.query(query, {"force": force})
    
    print(f"Found {len(recipes)} recipes to process.")
    
    call_count = 0
    start_time = datetime.datetime.now()
    
    for i, recipe in enumerate(recipes):
        uri = recipe['uri']
        name = recipe['name']
        cuisine = recipe.get('cuisine') or "Indonesian"
        primary_ing = recipe.get('primary_ingredient')
        
        # Construct search query
        parts = [cuisine, name]
        if primary_ing:
            parts.append(primary_ing)
            
        search_query = " ".join(parts).replace("-", " ")
        print(f"[{i+1}/{len(recipes)}] Processing: {name} (Query: '{search_query}')")
        
        # Rate limiting: 50 calls per hour
        if call_count >= 50:
            wait_seconds = 3600 # 60 minutes
            next_run = datetime.datetime.now() + datetime.timedelta(seconds=wait_seconds)
            print(f"!!! Planned pause (50 calls). Sleeping for 60 minutes until {next_run.strftime('%H:%M:%S')}...")
            time.sleep(wait_seconds)
            call_count = 0 
            
        img_result = None
        
        # Try Unsplash first if key is available and not limited
        if unsplash_key and call_count < 50:
            img_result = get_unsplash_image(search_query, unsplash_key)
            call_count += 1
        
        # Fallback to Pixabay if Unsplash is limited or no key provided
        if (not img_result or img_result == "RATE_LIMIT") and pixabay_key:
            if img_result == "RATE_LIMIT":
                print("   Unsplash limit reached. Switching to Pixabay...")
            img_result = get_pixabay_image(search_query, pixabay_key)
        
        # If still rate limited (Unsplash 403) and no Pixabay fallback, wait
        if img_result == "RATE_LIMIT":
            wait_seconds = 3600 # 60 minutes
            next_run = datetime.datetime.now() + datetime.timedelta(seconds=wait_seconds)
            print(f"!!! Unsplash Rate Limit (403) and no fallback. Sleeping for 60 minutes until {next_run.strftime('%H:%M:%S')}...")
            time.sleep(wait_seconds)
            call_count = 0
            # Retry current recipe after sleep
            img_result = get_unsplash_image(search_query, unsplash_key)

        if img_result and img_result != "RATE_LIMIT":
            img_url = img_result
            update_query = """
            MATCH (r:schema__Recipe {uri: $uri})
            SET r.schema__image = $img_url
            RETURN r
            """
            neo4j.query(update_query, {"uri": uri, "img_url": img_url})
            print(f"   Done! Updated with: {img_url}")
        else:
            print(f"   Skipped: No image found for '{search_query}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich recipe nodes with Unsplash images.")
    parser.add_argument("--limit", type=int, help="Limit the number of recipes to process.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing Unsplash images.")
    args = parser.parse_args()
    
    enrich_recipes(limit=args.limit, force=args.force)

import sys
import os
import time
from unittest.mock import MagicMock

# Mock streamlit
sys.modules["streamlit"] = MagicMock()
def pass_through_decorator(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
        return args[0]
    def decorator(func):
        return func
    return decorator
sys.modules["streamlit"].cache_data = pass_through_decorator
sys.modules["streamlit"].cache_resource = pass_through_decorator
sys.modules["streamlit"].error = print

# import toml -> removed to avoid dependency issues
# Manually read secrets or use defaults
try:
    with open(".streamlit/secrets.toml", "r") as f:
        # Simple manual parse for keys we need
        content = f.read()
        secrets = {}
        for line in content.splitlines():
            if "=" in line and not line.strip().startswith("["):
                key, val = line.split("=", 1)
                secrets[key.strip()] = val.strip().strip('"').strip("'")
        sys.modules["streamlit"].secrets = secrets
except:
    sys.modules["streamlit"].secrets = {
        "NEO4J_URI": os.environ.get("NEO4J_URI", "neo4j+s://2fe4f7d3.databases.neo4j.io"),
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "..." 
    }

sys.path.append(os.getcwd())
# Removed try/except to see import errors
from services.recipe_queries import search_recipes, get_all_countries

def verify_filters():
    print("--- Verifying Filters ---")
    
    # 1. Total Count (No filters)
    print("Fetching ALL recipes...")
    all_recipes, total_all = search_recipes(limit=1)
    print(f"Total recipes: {total_all}")
    
    if total_all == 0:
        print("No recipes found at all. Aborting.")
        return

    # 2. Get a country to filter by
    countries = get_all_countries()
    if not countries:
        print("No countries found.")
        return
        
    test_country = countries[0] # Pick first one
    print(f"\nFiltering by Country: '{test_country}'")
    
    filtered_recipes, total_filtered = search_recipes(countries=[test_country], limit=1)
    print(f"Filtered count: {total_filtered}")
    
    if total_filtered == total_all:
        print("FAIL: Filtered count equals total count (Filters ignored!)")
    elif total_filtered == 0:
        print(f"WARNING: No recipes for {test_country}, possibly valid but suspicious if major country.")
    else:
        print(f"PASS: Filtered count {total_filtered} < {total_all}. Filters are working.")

if __name__ == "__main__":
    verify_filters()

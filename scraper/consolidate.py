from collections import Counter

class Consolidator:
    # Common typos and variations in Indonesian ingredients
    SYNONYM_MAP = {
        "jeruk perut": "jeruk purut",
        "jerur purut": "jeruk purut",
        "jerur purutblaadjes": "jeruk purut",
        "jeruk perutblaadjes": "jeruk purut",
        "jeruk purutblaadjes": "jeruk purut",
        "tjabe": "cabai",
        "lombok": "cabai",
        "jahe": "gember",
        "djahé": "gember",
        "djahe": "gember",
        "laos": "lengkuas",
        "sereh": "citroengras",
        "serai": "citroengras",
        "kunjit": "kurkuma",
        "kunyit": "kurkuma",
        "trassi": "terasi",
        "trasi": "terasi",
        "kencur": "kentjoer",
        "djinten": "jinten",
        "ketjap": "kecap",
        "ketjap manis": "kecap manis",
        "santen": "kokosmelk",
        "daun salam": "salam blad",
        "salamblaadjes": "salam blad",
        "hoofdbestanddeel": "ingrediënt",
    }

    def __init__(self, min_frequency=2):
        self.min_frequency = min_frequency # Threshold for promoting a tag to a category
        
    def process(self, recipes):
        """
        Consolidate categories across all recipes.
        recipes: list of recipe dicts (output of extract + detect)
        
        Returns:
            - enriched_recipes: recipes with final 'tags'
            - categories: dict of category vocabularies
        """
        
        # 1. Global Frequency Analysis
        cuisine_counts = Counter()
        main_ingr_counts = Counter()
        dish_counts = Counter()
        method_counts = Counter()
        region_counts = Counter()
        
        # New: Collect unique ingredients and units
        all_ingredients = set()
        all_units = set()
        
        for r in recipes:
            detected = r.get("detected", {})
            cuisine_counts.update(detected.get("cuisines", []))
            main_ingr_counts.update(detected.get("main_ingredients", []))
            dish_counts.update(detected.get("dish_types", []))
            method_counts.update(detected.get("cooking_methods", []))
            region_counts.update(detected.get("regions", []))
            
            # Extract ingredients/units for the ontology
            for ing in r.get("ingredients", []):
                prod = ing.get("product")
                if prod:
                    norm_prod = self._normalize_ingredient(prod)
                    all_ingredients.add(norm_prod)
                unit = ing.get("unit")
                if unit:
                    all_units.add(unit.strip().lower())
            
        # 2. Filter / Promotion
        valid_cuisines = {k for k, v in cuisine_counts.items() if v >= self.min_frequency}
        valid_main_ingrs = {k for k, v in main_ingr_counts.items() if v >= self.min_frequency}
        valid_dishes = {k for k, v in dish_counts.items() if v >= self.min_frequency}
        valid_methods = {k for k, v in method_counts.items() if v >= self.min_frequency}
        valid_regions = {k for k, v in region_counts.items() if v >= self.min_frequency}
        
        print(f"Consolidation Results:")
        print(f"  Cuisines Promoted: {len(valid_cuisines)} / {len(cuisine_counts)}")
        print(f"  Main Ingredients Promoted: {len(valid_main_ingrs)} / {len(main_ingr_counts)}")
        print(f"  Dish Types Promoted: {len(valid_dishes)} / {len(dish_counts)}")
        print(f"  Methods Promoted: {len(valid_methods)} / {len(method_counts)}")
        print(f"  Regions Promoted: {len(valid_regions)} / {len(region_counts)}")
        print(f"  Unique Ingredients Found: {len(all_ingredients)}")
        print(f"  Unique Units Found: {len(all_units)}")
        
        # 3. Back-propagate to recipes
        enriched_recipes = []
        for r in recipes:
            detected = r.get("detected", {})
            r["tags"] = {
                "cuisine": [x for x in detected.get("cuisines", []) if x in valid_cuisines],
                "main_ingredient": [x for x in detected.get("main_ingredients", []) if x in valid_main_ingrs],
                "dish_type": [x for x in detected.get("dish_types", []) if x in valid_dishes],
                "cooking_method": [x for x in detected.get("cooking_methods", []) if x in valid_methods],
                "region": [x for x in detected.get("regions", []) if x in valid_regions]
            }
            # Also normalize ingredients in the data
            for ing in r.get("ingredients", []):
                if ing.get("product"):
                    ing["product_norm"] = self._normalize_ingredient(ing["product"])
            
            enriched_recipes.append(r)
            
        categories = {
            "cuisine": list(valid_cuisines),
            "main_ingredient": list(valid_main_ingrs),
            "dish_type": list(valid_dishes),
            "cooking_method": list(valid_methods),
            "region": list(valid_regions),
            # Add ingredients and units to the registry
            "ingredient_ontology": sorted(list(all_ingredients)),
            "unit_ontology": sorted(list(all_units))
        }
        
        return enriched_recipes, categories

    def _normalize_ingredient(self, text):
        """Clean and normalize ingredient names based on synonym map."""
        import re
        if not text: return ""
        text = text.lower().strip()
        
        # 1. Remove obvious noise at start/end (punctuation, stars)
        text = re.sub(r'^[\s,.*\\/]+', '', text)
        text = re.sub(r'[\s,.*\\/]+$', '', text)
        
        # 2. Cleanup internal noise (replace with single space)
        # Handle commas, dots, stars, backslashes, and forward slashes
        text = text.replace(',', ' ').replace('*', ' ').replace('\\', ' ').replace('/', ' ')
        # Handle parentheses if they contain noise or are empty
        text = text.replace('(', ' ').replace(')', ' ')
        
        # 3. Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 4. Remove missed fractions or quantities at start
        text = re.sub(r'^[½⅓¼¾\d\.\,/]+', '', text).strip()
        
        # 5. Handle specific Indonesian noise
        text = text.replace("blad", "").replace("blaadjes", "").strip()
        
        # 6. Check synonym map
        # Sort keys by length descending to match longest phrases first
        for k in sorted(self.SYNONYM_MAP.keys(), key=len, reverse=True):
            if k in text:
                return self.SYNONYM_MAP[k]
        
        return text

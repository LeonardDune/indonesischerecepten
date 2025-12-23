from rdflib import Graph, Literal, BNode, Namespace, RDF, RDFS, XSD, URIRef
from rdflib.namespace import SDO # schema.org

class RDFWriter:
    def __init__(self):
        self.g = Graph()
        self.SCHEMA = Namespace("https://schema.org/")
        self.BASE = Namespace("https://www.kokkieblanda.nl/kg/")
        self.KB_RECIPE = Namespace("https://www.kokkieblanda.nl/kg/recipe/")
        
        # New structure structures
        self.CAT = Namespace("https://www.kokkieblanda.nl/kg/category/")
        self.CAT_CUISINE = Namespace("https://www.kokkieblanda.nl/kg/category/cuisine/")
        self.CAT_INGREDIENT = Namespace("https://www.kokkieblanda.nl/kg/category/ingredient/")
        self.CAT_REGION = Namespace("https://www.kokkieblanda.nl/kg/category/region/")
        self.CAT_DISH = Namespace("https://www.kokkieblanda.nl/kg/category/dish-type/")
        self.CAT_METHOD = Namespace("https://www.kokkieblanda.nl/kg/category/cooking-method/")
        
        # New Ontology namespaces
        self.ING = Namespace("https://www.kokkieblanda.nl/kg/ingredient/")
        self.UNIT = Namespace("https://www.kokkieblanda.nl/kg/unit/")
        self.SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

        self.g.bind("schema", self.SCHEMA)
        self.g.bind("kb", self.BASE)
        self.g.bind("kbr", self.KB_RECIPE)
        self.g.bind("cat", self.CAT)
        self.g.bind("cuisine", self.CAT_CUISINE)
        self.g.bind("ing_cat", self.CAT_INGREDIENT) # Renamed to avoid confusion with ING
        self.g.bind("reg", self.CAT_REGION)
        self.g.bind("dt", self.CAT_DISH)
        self.g.bind("method", self.CAT_METHOD)
        self.g.bind("ing", self.ING)
        self.g.bind("unit", self.UNIT)
        self.g.bind("skos", self.SKOS)

    def _get_category_uri(self, tag_type, slug):
        """Map tag type to specific namespace."""
        if tag_type == "cuisine":
            return self.CAT_CUISINE[slug]
        if tag_type == "main_ingredient":
            return self.CAT_INGREDIENT[slug]
        if tag_type == "region":
            return self.CAT_REGION[slug]
        if tag_type == "dish_type":
            return self.CAT_DISH[slug]
        if tag_type == "cooking_method":
            return self.CAT_METHOD[slug]
        return self.CAT[f"{tag_type}/{slug}"]

    def generate_graph(self, enriched_recipes, categories):
        """Build the full RDF graph."""
        for recipe in enriched_recipes:
            slug = recipe.get("slug")
            recipe_uri = self.KB_RECIPE[slug]
            
            self.g.add((recipe_uri, RDF.type, self.SCHEMA.Recipe))
            self.g.add((recipe_uri, self.SCHEMA.name, Literal(recipe["title"])))
            self.g.add((recipe_uri, self.SCHEMA.url, URIRef(recipe["url"])))
            
            if recipe.get("description"):
                self.g.add((recipe_uri, self.SCHEMA.description, Literal(recipe["description"])))
                
            if recipe.get("image"):
                self.g.add((recipe_uri, self.SCHEMA.image, Literal(recipe["image"])))
                
            if recipe.get("instructions"):
                self.g.add((recipe_uri, self.SCHEMA.recipeInstructions, Literal(recipe["instructions"])))

            if recipe.get("yield"):
                self.g.add((recipe_uri, self.SCHEMA.recipeYield, Literal(recipe["yield"])))

            # Tags mapping
            for c_slug in recipe["tags"].get("cuisine", []):
                self.g.add((recipe_uri, self.SCHEMA.recipeCuisine, self._get_category_uri("cuisine", c_slug)))
            
            for c_slug in recipe["tags"].get("main_ingredient", []):
                self.g.add((recipe_uri, self.BASE.hasPrimaryIngredient, self._get_category_uri("main_ingredient", c_slug)))
                
            for c_slug in recipe["tags"].get("dish_type", []):
                self.g.add((recipe_uri, self.BASE.hasDishType, self._get_category_uri("dish_type", c_slug)))
                
            for c_slug in recipe["tags"].get("cooking_method", []):
                self.g.add((recipe_uri, self.BASE.usesCookingMethod, self._get_category_uri("cooking_method", c_slug)))
                
            for c_slug in recipe["tags"].get("region", []):
                self.g.add((recipe_uri, self.BASE.hasCuisineRegion, self._get_category_uri("region", c_slug.lower())))

            # New: Ingredients via IngredientUsage bridge nodes
            for i, ing in enumerate(recipe.get("ingredients", [])):
                usage_node = BNode() # Recept-specifieke instantie
                self.g.add((usage_node, RDF.type, self.BASE.IngredientUsage))
                
                # Link based on normalized slug
                prod_name = ing.get("product_norm", ing["product"])
                ing_slug = self._slugify(prod_name)
                self.g.add((usage_node, self.BASE.ingredient, self.ING[ing_slug]))
                
                parts = []
                if ing.get("amount"):
                    self.g.add((usage_node, self.SCHEMA.value, Literal(ing["amount"])))
                    parts.append(ing["amount"])
                
                if ing.get("unit"):
                    unit_slug = self._slugify(ing["unit"])
                    self.g.add((usage_node, self.BASE.unit, self.UNIT[unit_slug]))
                    parts.append(ing["unit"])
                
                parts.append(ing["product"])
                ing_summary = " ".join(parts).strip()

                self.g.add((recipe_uri, self.BASE.hasIngredientUsage, usage_node))
                # Enriched recipeIngredient summary string
                self.g.add((recipe_uri, self.SCHEMA.recipeIngredient, Literal(ing_summary)))

        # 1. Add Category definitions
        for tag_type, slugs in categories.items():
            if tag_type in ["cuisine", "main_ingredient", "dish_type", "cooking_method", "region"]:
                for slug in slugs:
                    cat_uri = self._get_category_uri(tag_type, slug)
                    self.g.add((cat_uri, RDF.type, self.SCHEMA.DefinedTerm))
                    self.g.add((cat_uri, self.SCHEMA.name, Literal(slug.replace("-", " "))))
                    self.g.add((cat_uri, self.BASE.categoryType, Literal(tag_type)))

        # 2. Add Global Ingredient Ontology
        for ing_name in categories.get("ingredient_ontology", []):
            ing_slug = self._slugify(ing_name)
            ing_uri = self.ING[ing_slug]
            self.g.add((ing_uri, RDF.type, self.BASE.Ingredient))
            self.g.add((ing_uri, RDFS.label, Literal(ing_name)))
            # Placeholder for FoodOn mapping
            self.g.add((ing_uri, self.SKOS.exactMatch, Literal("TODO: Map to FoodOn")))

        # 3. Add Global Unit Ontology
        for unit_name in categories.get("unit_ontology", []):
            unit_slug = self._slugify(unit_name)
            unit_uri = self.UNIT[unit_slug]
            self.g.add((unit_uri, RDF.type, self.BASE.Unit))
            self.g.add((unit_uri, RDFS.label, Literal(unit_name)))
            # Placeholder for OM mapping
            self.g.add((unit_uri, self.SKOS.closeMatch, Literal("TODO: Map to OM/UO")))

        return self.g

    def _slugify(self, text):
        import re
        if not text: return ""
        text = text.lower()
        # strip common suffixes/prefixes if needed, but for now just slugify
        text = re.sub(r'[^a-z0-9]+', '-', text)
        return text.strip('-')

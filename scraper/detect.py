import re

class Detector:
    def __init__(self):
        self.rules = {
            "cuisine": [
                (r'(?i)/indonesian\b', 'indonesian'),
                (r'(?i)/thailand\b', 'thai'),
                (r'(?i)/china\b', 'chinese'),
                (r'(?i)/filipijnen\b', 'filipino'),
                (r'(?i)/korea\b', 'korean'),
                (r'(?i)/vietnam\b', 'vietnamese'),
            ],
            "dish_type": [
                (r'(?i)\bhoofdgerecht\b', 'hoofdgerecht'),
                (r'(?i)\bbijgerecht\b', 'bijgerecht'),
                (r'(?i)\bvoorgerecht\b', 'voorgerecht'),
                (r'(?i)\bnagerecht\b', 'nagerecht'),
                (r'(?i)\bsnack\b', 'snack'),
                (r'(?i)\batjar\b', 'bijgerecht'),
                (r'(?i)\bsambal\b', 'sambal'),
                (r'(?i)\bsop\b', 'soep'),
                (r'(?i)\bsoto\b', 'soep'),
                (r'(?i)\bsate\b', 'sate'),
                (r'(?i)\bsaté\b', 'sate'),
                (r'(?i)\bnasi\b', 'rijstgerecht'),
                (r'(?i)\bmie\b', 'noedelgerecht'),
                (r'(?i)\bbami\b', 'noedelgerecht'),
                (r'(?i)\brendang\b', 'stoofgerecht'),
                (r'(?i)\bsmoor\b', 'stoofgerecht'),
                (r'(?i)\bgulai\b', 'curry'),
                (r'(?i)\bkari\b', 'curry'),
            ],
            "main_ingredient": [
                (r'(?i)\b(rundvlees|daging|sapi)\b', 'daging-rundvlees'),
                (r'(?i)\b(varkensvlees|babi|spek)\b', 'varkensvlees'),
                (r'(?i)\b(kip|ayam|bebek|eend)\b', 'kip-ayam'),
                (r'(?i)\b(vis|ikan|mosselen|garnalen|udang|cumi|inktvis)\b', 'vis-vis-schelpdieren'),
                (r'(?i)\b(tahu|tempe|tahoe|tempeh)\b', 'vegetarisch-vega'),
                (r'(?i)\b(sayur|groente)\b', 'vegetarisch-vega'),
                (r'(?i)\b(ei|telur)\b', 'ei'),
            ],
            "cooking_method": [
                (r'(?i)\bbakken\b', 'bakken'),
                (r'(?i)\bbraden\b', 'braden'),
                (r'(?i)\bfrituren\b', 'frituren'),
                (r'(?i)\bgrillen\b', 'grillen'),
                (r'(?i)\broosteren\b', 'roosteren'),
                (r'(?i)\bstoven\b', 'stoven'),
                (r'(?i)\bkoken\b', 'koken'),
                (r'(?i)\bstomen\b', 'stomen'),
                (r'(?i)\bwokken\b', 'wokken'),
                (r'(?i)\broerbakken\b', 'wokken'),
            ],
            "region": [
                (r'(?i)\bjava\b', 'Java'),
                (r'(?i)\bjacaans\b', 'Java'),
                (r'(?i)\bsumatra\b', 'Sumatra'),
                (r'(?i)\bbali\b', 'Bali'),
                (r'(?i)\bbalinees\b', 'Bali'),
                (r'(?i)\bsulawesi\b', 'Sulawesi'),
                (r'(?i)\bcelebes\b', 'Sulawesi'),
                (r'(?i)\bkalimantan\b', 'Kalimantan'),
                (r'(?i)\bborneo\b', 'Kalimantan'),
                (r'(?i)\bpadang\b', 'Padang'),
                (r'(?i)\bbetawi\b', 'Jakarta'),
                (r'(?i)\bjakarta\b', 'Jakarta'),
                (r'(?i)\bsunda\b', 'Sunda'),
                (r'(?i)\baceh\b', 'Aceh'),
                (r'(?i)\bmanado\b', 'Manado'),
                (r'(?i)\bambon\b', 'Ambon'),
                (r'(?i)\bmolukken\b', 'Ambon'),
            ]
        }

    def detect(self, recipe_data):
        """
        Analyze recipe data (title, instructions, ingredients, metadata) to infer categories.
        Returns a dictionary with detected categories.
        """
        detected = {
            "cuisines": set(),
            "main_ingredients": set(),
            "dish_types": set(),
            "cooking_methods": set(),
            "regions": set(), 
        }
        
        url = recipe_data.get("url", "")
        title = recipe_data.get("title", "")
        description = recipe_data.get("description", "")
        instructions = recipe_data.get("instructions", "")
        ingredients_text = " ".join([i.get("product", "") for i in recipe_data.get("ingredients", [])])
        
        full_text = f"{title} {description} {instructions} {ingredients_text}"
        
        # 1. Cuisine (primarily from URL)
        for pattern, label in self.rules["cuisine"]:
            if re.search(pattern, url):
                detected["cuisines"].add(label)
        
        # 2. Dish Type (Title + Description are strongest)
        for pattern, label in self.rules["dish_type"]:
            if re.search(pattern, title) or re.search(pattern, description[:200]):
                detected["dish_types"].add(label)
        
        # 3. Main Ingredient (Title + Top of ingredients)
        # Note: we only take the first 3 ingredients as "main" candidates
        top_ingredients = " ".join([i.get("product", "") for i in recipe_data.get("ingredients", [])[:3]])
        for pattern, label in self.rules["main_ingredient"]:
            if re.search(pattern, title) or re.search(pattern, top_ingredients):
                detected["main_ingredients"].add(label)
        
        # 4. Cooking Method (Instructions)
        for pattern, label in self.rules["cooking_method"]:
            if re.search(pattern, instructions):
                detected["cooking_methods"].add(label)
                
        # 5. Region (Title + Description)
        for pattern, label in self.rules["region"]:
            if re.search(pattern, title) or re.search(pattern, description):
                detected["regions"].add(label)

        return {k: list(v) for k, v in detected.items()}

if __name__ == "__main__":
    # verification
    d = Detector()
    sample = {
        "title": "Rendang Padang",
        "instructions": "Het vlees stoven in kokosmelk.",
        "ingredients": [{"product": "rundvlees"}, {"product": "kokosmelk"}]
    }
    print(d.detect(sample))

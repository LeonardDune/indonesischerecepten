import re
from bs4 import BeautifulSoup

class Extractor:
    def parse_html(self, html_content, url=None):
        """
        Parse HTML content and return a dictionary with recipe data.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Determine slug from URL if possible
        slug = ""
        if url:
             # Determine slug from URL if possible
             # Strip fragment and query
             clean_url = url.split('#')[0].split('?')[0].strip('/')
             last_seg = clean_url.split('/')[-1]
             # split off the id if it exists (digits followed by dash)
             match = re.match(r'^(\d+)-(.*)$', last_seg)
             if match:
                 slug = match.group(2)
             else:
                 slug = last_seg

        data = {
            "url": url,
            "slug": slug,
            "title": self._extract_title(soup),
            "ingredients": [],
            "instructions": "",
            "image": self._extract_image(soup),
            "yield": "4 personen", # Default as requested
            "raw_text": ""
        }
        
        # Locate main content
        article = soup.find('div', class_='item-page') or soup.find('div', class_='com-content-article')
        if not article:
            article = soup.find('div', itemprop='articleBody')
            
        if article:
            # Clean up garbage
            for garbage in article.select('.content_rating, .form-inline, .page-header, .article-info, .pagenavigation, .item-image, script, style'):
                garbage.decompose()
                
            data["raw_text"] = article.get_text(separator="\n").strip()
            self._extract_content_sections(article, data)
            
        return data

    def _extract_title(self, soup):
        h1 = soup.find('h1')
        return h1.get_text(strip=True) if h1 else ""

    def _extract_image(self, soup):
        # Try to find a main image
        img = soup.find('div', class_='item-page').find('img') if soup.find('div', class_='item-page') else None
        if img and img.get('src'):
            src = img['src']
            if not src.startswith('http'):
                # Assuming base url is handled by caller or we join it later.
                # For now just return the path.
                pass
            return src
        return None

    def _extract_content_sections(self, article_div, data):
        """
        Split content into ingredients and instructions based on keywords.
        Structure seems to be:
        <strong>Header</strong><br>content<br>
        """
        # Strategy: Iterate through children elements (mostly strings and br/strong tags)
        # But bs4 parsing of that unstructured div is tricky.
        # Let's try text partitioning first, or looking for specific headers.
        
        full_text = article_div.get_text(separator="\n", strip=True)
        
        # Identify sections by keywords
        # Use a more robust matching that can handle split words if they occur across lines
        # or just be more inclusive.
        markers = {
            "ingredients": ["ingrediënten", "bahan-bahan", "bahan"],
            "paste": ["haluskan", "bumbu", "boemboe", "pasta"],
            "instructions": ["bereiding", "cara membuat", "details"]
        }
        
        lines = full_text.splitlines()
        current_section = None
        
        ingredients_lines = []
        instructions_lines = []
        
        # Track where the FIRST section starts to define the intro/description
        first_marker_index = -1
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            lower_line = line.lower()
            
            # Special case for "i\nngrediënten" split
            if lower_line == "i" and i + 1 < len(lines) and lines[i+1].lower().strip().startswith("ngrediënten"):
                if first_marker_index == -1: first_marker_index = i
                current_section = "ingredients"
                # skip next line in next iteration? No, let's just mark it
                continue
            if lower_line.startswith("ngrediënten") and i > 0 and lines[i-1].lower().strip() == "i":
                continue

            # Check for regular markers
            found_section = None
            for section, keywords in markers.items():
                if any(k == lower_line.rstrip(':') for k in keywords):
                    found_section = section
                    break
            
            if found_section:
                if first_marker_index == -1: first_marker_index = i
                if found_section == "paste":
                    current_section = "ingredients"
                else:
                    current_section = found_section
                continue
            
            # Content accumulation
            if current_section == "ingredients":
                ingredients_lines.append(line)
            elif current_section == "instructions":
                # Clean up instructions noise
                if any(x in lower_line for x in ["copyright", "previous article", "next article", "details"]):
                    continue
                instructions_lines.append(line)
        
        # Description is everything before the first marker
        if first_marker_index != -1:
            description = " ".join(lines[:first_marker_index]).strip()
        else:
            # Fallback if no markers found, take first few lines
            description = " ".join(lines[:5]).strip()
        
        # Additional cleaning for description (remove multiple spaces/tabs)
        description = re.sub(r'\s+', ' ', description)
            
        data["raw_text"] = description
        data["instructions"] = "\n".join(instructions_lines)
        
        # Filter headers out of ingredient lines before parsing
        header_patterns = [
            r'^(ingrediënten|ingredienten|bahan-bahan|bahan-bahant|bahan|bahan-bahan saus|ingrediënten saus|taburan|garnering|saus|pelengkap|complementair|pelengkap|serveer|serveer suggestie|presentatie)\b.*[:;]?$',
            r'^(cara[- ]membuat|cara[- ]masak|bereiding|penyajian|methode)\b.*[:;]?$',
            r'^(i|ngrediënten|ngredienten)\b.*[:;]?$'
        ]
        
        filtered_ingredients = []
        for line in ingredients_lines:
            lower = line.lower().strip()
            # 1. Skip if it matches a header pattern
            is_header = False
            for pat in header_patterns:
                if re.match(pat, lower):
                    is_header = True
                    break
            if is_header:
                continue
                
            # 2. Skip if it's too long (likely instructions that bled in) or contains obvious instruction verbs
            # Ingredients are usually < 100 chars
            if len(line) > 120:
                continue
                
            instruction_verbs = ['snijd', 'verhit', 'bak ', 'kook ', 'voeg ', 'roer ', 'meng ', 'wrijf ']
            if any(verb in lower for verb in instruction_verbs):
                continue

            filtered_ingredients.append(line)

        data["ingredients"] = self._parse_ingredients(filtered_ingredients)

    # Whitelist of common units (singular and plural)
    UNIT_WHITELIST = {
        # Metric
        "gr", "g", "kg", "ml", "l", "cl", "dl", "cm", "gram", "kilo", "liter",
        # Culinary
        "tl", "el", "theel", "eetl", "theel.", "eetl.", "tsp", "tbsp", "cup", "cups",
        "theelepel", "theelepels", "eetlepel", "eetlepels", "cop", "theell",
        # Discrete/Containers
        "stuks", "stuk", "teentje", "teentjes", "blok", "blokken", "blik", "blikken", 
        "pakje", "pakjes", "zakje", "zakjes", "fles", "flessen", "pot", "potten", 
        "stengel", "stengels", "stokje", "stokjes", "blaadje", "blaadjes", "takje", "takjes",
        "kop", "koppen", "glazen", "glas", "kom", "kommen", "doosje", "doosjes", "tablet", "tabletten",
        "schijfje", "schijfjes", "plakje", "plakjes", "segment", "segmenten", "partje", "partjes",
        # Vague
        "snuf", "snufje", "snufjes", "handvol", "scheut", "scheutje", "scheutjes", "mespunt", "mespuntje",
        "naar smaak", "beetje"
    }

    def _parse_ingredients(self, lines):
        """
        Parse list of strings into structured objects.
        """
        structured = []
        for line in lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue
            
            # 1. Clean trailing amounts in parentheses (e.g. "bonito (1500 gr)")
            # but preserve it in raw for now
            clean_product = line
            amount_override = ""
            unit_override = ""
            
            trailing_match = re.search(r'\(([\d\.,/]+)\s*([a-zA-Z\.]+)?\)$', line)
            if trailing_match:
                clean_product = line[:trailing_match.start()].strip()
                amount_override = trailing_match.group(1)
                unit_override = trailing_match.group(2) if trailing_match.group(2) else ""

            # 2. Strict regex: must start with quantity (supporting spaces like "1 1/2")
            match = re.match(r'^([\d\.,/\s]+)\s+([a-zA-Z\.]+)?\s*(.*)$', clean_product)
            if match:
                qty, unit_candidate, product = match.groups()
                qty = qty.strip()
                
                # Check if unit_candidate is actually in our whitelist
                unit = ""
                actual_product = product
                
                if unit_candidate:
                    uc_clean = unit_candidate.lower().rstrip('.')
                    if uc_clean in self.UNIT_WHITELIST or unit_candidate.lower() in self.UNIT_WHITELIST:
                        unit = unit_candidate
                    else:
                        # It's probably part of the product (e.g. "rode")
                        actual_product = f"{unit_candidate} {product}"
                
                structured.append({
                    "raw": line,
                    "amount": qty,
                    "unit": unit,
                    "product": actual_product.strip()
                })
            elif amount_override:
                # If we had a trailing amount, use it as a fallback
                structured.append({
                    "raw": line,
                    "amount": amount_override,
                    "unit": unit_override,
                    "product": clean_product
                })
            else:
                # If it doesn't match the digit pattern, treat as bare ingredient
                structured.append({
                    "raw": line,
                    "product": line
                })
        return structured

if __name__ == "__main__":
    # Test on a file or snippet
    pass

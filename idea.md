# Voorstel: Dynamisch scrapen van recepten van kokkieblanda.nl naar een knowledge graph

## 1. Doel en scope

Dit document beschrijft een complete aanpak voor het scrapen van alle recepten van **[https://www.kokkieblanda.nl/](https://www.kokkieblanda.nl/)** en het opslaan ervan in een **knowledge graph** in de vorm van **RDF/Turtle (TTL)**, conform **schema.org/Recipe**.

Belangrijke uitgangspunten:

* Volledig respecteren van de bestaande categorisatiestructuur van de website
* Dynamische, data-gedreven categorievorming (geen hard-coded mappings)
* Categorieën als first-class nodes in de graph
* Uitbreidbaar en onderhoudsarm ontwerp

---

## 2. Analyse van de website

### 2.1 Structuur

Kokkieblanda.nl heeft een consistente URL-structuur:

```
/{cuisine}/{primary-ingredient}/{id}-{slug}
```

Voorbeeld:

```
/indonesian/daging-rundvlees/1909-rendang-rendang-van-rundvlees
```

Hieruit zijn direct af te leiden:

* Cuisine (keuken / land)
* Primary ingredient category (hoofdingrediënt)

Daarnaast bevatten receptpagina’s vrijwel altijd:

* Titel (h1)
* Ingrediëntenlijst
* Bereidingsinstructies
* Soms contextuele tekst met regio- of stijlverwijzingen

---

## 3. Categoriekader

### 3.1 Verplichte categorieën

Deze categorieën worden voor elk recept bepaald:

| Categorie                 | Herkomst           | Karakter        |
| ------------------------- | ------------------ | --------------- |
| Cuisine                   | URL-segment        | Deterministisch |
| PrimaryIngredientCategory | URL-segment        | Deterministisch |
| DishType                  | Tekstuele detectie | Classificerend  |

---

### 3.2 Uitbreidingscategorieën

Deze categorieën worden toegevoegd indien detecteerbaar:

| Categorie     | Herkomst             | Strategie            |
| ------------- | -------------------- | -------------------- |
| CuisineRegion | Titel / beschrijving | Emergent vocabulaire |
| CookingMethod | Instructies          | Corpus-analyse       |

Dieetlabels (vegetarisch, halal, etc.) worden **niet** gemodelleerd.

---

## 4. Dynamische categoriebepaling

### 4.1 Cuisine

* Afgeleid uit het eerste URL-segment
* Geen vooraf gedefinieerde mapping

Voorbeeld:

```
/indonesian/ → cat:cuisine/indonesian
```

Labelvorming:

* Slug → human-readable label ("indonesian" → "Indonesian")

---

### 4.2 PrimaryIngredientCategory

* Afgeleid uit het tweede URL-segment
* Volledige slug wordt hergebruikt als categorie

Voorbeeld:

```
/daging-rundvlees/ → cat:ingredient/daging-rundvlees
```

Hiermee wordt de bestaande taxonomie van de site volledig hergebruikt.

---

### 4.3 DishType

* Niet structureel aanwezig in URL
* Detectie via titel en tekst

Aanpak:

* Pattern-based detectie (regex)
* Vocabulaire groeit automatisch op basis van waarnemingen

Voorbeelden:

* soep
* hoofdgerecht
* bijgerecht
* dessert

DishType blijft een **classificatie**, geen absolute waarheid.

---

### 4.4 CuisineRegion

Regio’s zijn inhoudelijk waardevol, vooral binnen de Indonesische keuken.

Bronnen:

* Recepttitel
* Beschrijving
* Traditionele naamgeving

Aanpak:

1. Detectie van kandidaat-termen (bijv. hoofdletterwoorden)
2. Frequentie-analyse over het corpus
3. Promotie tot `CuisineRegion` indien:

   * term meerdere keren voorkomt
   * term consistent samenvalt met dezelfde cuisine

Dit resulteert in bottom-up ontologievorming.

---

### 4.5 CookingMethod

* Afgeleid uit werkwoorden in de instructietekst
* Corpus-gebaseerde detectie

Voorbeelden:

* bakken
* stoven
* frituren
* grillen

Alleen dominante patronen worden als categorie gepromoveerd.

---

## 5. Knowledge graph ontwerp

### 5.1 Namespaces

```ttl
@prefix schema: <http://schema.org/> .
@prefix kb: <https://www.kokkieblanda.nl/kg/> .
@prefix cat: <https://www.kokkieblanda.nl/kg/category/> .
```

---

### 5.2 Klassen

* `schema:Recipe`
* `kb:Cuisine`
* `kb:PrimaryIngredientCategory`
* `kb:DishType`
* `kb:CuisineRegion`
* `kb:CookingMethod`

---

### 5.3 Relaties

| Relatie                   | Beschrijving                       |
| ------------------------- | ---------------------------------- |
| `schema:recipeCuisine`    | Recipe → Cuisine                   |
| `kb:hasPrimaryIngredient` | Recipe → PrimaryIngredientCategory |
| `kb:hasDishType`          | Recipe → DishType                  |
| `kb:hasCuisineRegion`     | Recipe → CuisineRegion             |
| `kb:usesCookingMethod`    | Recipe → CookingMethod             |

Deze relaties zijn stabiel; alleen de nodes groeien.

---

## 6. URI-strategie

Categorieën:

```
cat:cuisine/indonesian
cat:ingredient/daging-rundvlees
cat:region/padang
cat:dish-type/hoofdgerecht
cat:cooking-method/stoven
```

Recepten:

```
kb:recipe/rendang-rendang-van-rundvlees
```

Slugs zijn identifiers, labels zijn presentatie.

---

## 7. Scraper-architectuur

### 7.1 Fasen

1. **Discovery**

   * Crawlen van categoriepagina’s
   * Verzamelen van alle recept-URL’s

2. **Extraction**

   * HTML ophalen
   * Ingrediënten en instructies extraheren
   * Ruwe categorie-detectie

3. **Consolidatie**

   * Frequentie-analyse
   * Promotie van categorie-kandidaten

4. **RDF-serialisatie**

   * Opslag als TTL
   * Per recept of als gebundelde graph

---

## 8. Resultaat

Het resultaat is een knowledge graph waarin:

* recepten consistent en herleidbaar geclassificeerd zijn
* categorieën herbruikbare en uitbreidbare nodes zijn
* regio’s expliciet gemodelleerd zijn
* schema.org optimaal wordt benut zonder semantische vervuiling

Deze graph is geschikt voor:

* faceted search
* inferentie
* hergebruik in andere food- of cultuur-domeinen

---

## 9. Architectuurkeuzes

### 9.1 Waarom een knowledge graph (RDF/TTL)

Gekozen is voor RDF/Turtle in plaats van JSON of relationele opslag om de volgende redenen:

* Expliciete semantiek: categorieën, regio’s en relaties zijn betekenisdragers, geen velden
* Uitbreidbaarheid: nieuwe categorieën kunnen worden toegevoegd zonder schemawijziging
* Inferentie: mogelijkheid om later regels of SHACL toe te passen
* Interoperabiliteit: aansluiting bij schema.org en andere ontologieën

TTL is gekozen vanwege:

* Leesbaarheid voor mensen
* Compactheid
* Goede ondersteuning in tooling (rdflib, Jena, GraphDB)

---

### 9.2 Dynamische categorieën versus vaste taxonomie

Er is bewust **niet** gekozen voor hard-coded mappings.

Architectuurkeuze:

* De website wordt beschouwd als primaire bron van taxonomie
* Nieuwe categorieën ontstaan data-gedreven
* Consolidatie gebeurt post-hoc, niet tijdens scraping

Voordeel:

* Lage onderhoudslast
* Hoge semantische flexibiliteit

Nadeel:

* Vereist een consolidatiefase
* Eerste runs leveren ruwe categorieën op

Deze trade-off is bewust geaccepteerd.

---

### 9.3 Twee-fasen architectuur

De scraper is logisch opgesplitst in twee fasen:

1. **Extractiefase**

   * Maximale recall
   * Weinig interpretatie

2. **Consolidatiefase**

   * Normalisatie
   * Frequentie-analyse
   * Promotie van categorieën

Dit voorkomt semantische verarming in een vroeg stadium.

---

### 9.4 URI-stabiliteit

URI’s worden gebaseerd op slugs en veranderen nooit.

Labels mogen veranderen.

Dit waarborgt:

* Historische herleidbaarheid
* Compatibiliteit bij her-scraping

---

## 10. Implementatie

### 10.1 Technische stack

* Python 3.11+
* requests
* BeautifulSoup4
* rdflib
* optioneel: spaCy (lemmatisatie)

Geen async of multithreading in eerste instantie, om de site niet te belasten.

---

### 10.2 Module-indeling

```text
scraper/
 ├─ discovery.py        # URL-verzameling
 ├─ extract.py          # HTML parsing
 ├─ detect.py           # Ruwe categoriedetectie
 ├─ consolidate.py      # Frequentie & normalisatie
 ├─ rdf_writer.py       # TTL-serialisatie
 └─ main.py
```

---

### 10.3 Discovery

* Startpunt: hoofdcategoriepagina’s
* Volg paginering
* Verzamel alleen URL’s die voldoen aan patroon `/{cuisine}/{ingredient}/{id}-...`

Deduplicatie gebeurt op URL-niveau.

---

### 10.4 Extractie

Per recept:

* Titel (h1)
* Ingrediënten (lijst of tekstblok)
* Instructies (paragraphs)
* Contexttekst (voor categoriedetectie)

Geen interpretatie in deze fase.

---

### 10.5 Detectie

Detectie levert **kandidaten**, geen definitieve categorieën:

* DishType: regex-patronen
* CuisineRegion: kandidaat-termen + telling
* CookingMethod: werkwoordextractie

Alle detecties worden met bronverwijzing opgeslagen.

---

### 10.6 Consolidatie

Consolidatieregels (voorbeeld):

* Term komt voor in ≥ N recepten
* Term is consistent binnen dezelfde cuisine

Pas daarna:

* promotie tot categorie-node
* toevoegen van relaties in RDF

---

### 10.7 RDF-output

Twee mogelijke outputs:

1. Per recept een TTL-bestand
2. Eén samengestelde graph

Aanbevolen:

* afzonderlijke `recipes.ttl` en `categories.ttl`

---

## 11. Mogelijke vervolgstappen

* SHACL-shapes voor validatie
* Versiebeheer van categorieën
* Koppeling aan externe ontologieën
* Indexering in graph database

---

## 12. Optimalisaties voor GraphRAG & Planning Agents

Om de knowledge graph optimaal in te zetten voor een "meal planning bot", worden de volgende verrijkingen toegevoegd aan het scraper- en modelleerproces.

### 12.1 Gestructureerde Ingrediënten

Voor kwantitatieve queries ("recepten met < 500g vlees" of boodschappenlijstjes) is tekstuele opslag onvoldoende.

*   **Actie:** Parsing van ingrediëntregels naar gestructureerde objecten (`Amount`, `Unit`, `Product`).
*   **Tooling:** Gebruik van een parser lib of LLM-stap tijdens extractie.
*   **RDF:** Modellering met `schema:Ingredient` of custom nodes voor maateenheden.

### 12.2 Plannings-Metadata

Cruciale data voor planningsbeslissingen wordt expliciet meegenomen:

*   **Yield:** Aantal personen (om hoeveelheden te schalen).
*   **Tijden:** `schema:prepTime`, `schema:cookTime`, `schema:totalTime`.
*   **Visueel:** `schema:image` (URL naar de foto) voor rijkere UI-presentatie.

### 12.3 Embeddings & Vector Search

Om vage zoekvragen ("iets lichts voor in de zomer") te ondersteunen die niet direct matchen op categorieën.

*   **Actie:** Genereren van vector embeddings op basis van: *Titel + Beschrijving + Ingrediëntenlijst*.
*   **Opslag:** Opslaan als property op de `kb:Recipe` node of in een gekoppelde vector store (met URI als key).

### 12.4 Cross-Recept Relaties

Expliciete koppelingen maken maaltijdsuggesties mogelijk (bijv. rijsttafels samenstellen).

*   **Detectie:** Scannen van "Serveer met..." of "Lekker bij..." links in de beschrijving.
*   **Relatie:** `kb:goesWellWith` of `schema:isRelatedTo`.

### 12.5 Robuustheid (Politeness)

*   **Rate Limiting:** `time.sleep(1)` tussen requests.
*   **User-Agent:** Identificatie als "ResearchBot/1.0 (+http://example.com)".
*   **Fouthantering:** 'Dead Letter Queue' voor URL's die falen, zodat de run niet crasht.


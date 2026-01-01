# MVP Receptenapp – Informatie-architectuur en Implementatie-instructie

## Doel van dit document

Dit document beschrijft de **informatie-architectuur**, **functionele scope** en een **concrete technische vertaling** naar een Streamlit-frontend met Neo4j als backend.  
Het doel is een **MVP** te realiseren voor een recepten-app waarin:

- Recepten primair worden ontsloten via **categorie-navigatie**
- Een **chatbot** fungeert als aanvullende query-interface
- Alle data afkomstig is uit een Neo4j-kennisgraaf gebaseerd op `schema.org/Recipe`

Dit document is bedoeld als **directe implementatie-instructie** voor een DevOps- of developmentteam.

---

## 1. Architectuur-overzicht

### 1.1 Kernprincipes

- Neo4j is de **enige bron van waarheid**
- Categorie-navigatie is de **primaire UX**
- Chatbot is een **alternatieve toegangsvorm**, geen vervanging
- Alle chatresultaten moeten herleidbaar zijn tot:
  - recepten
  - categorieën
- Geen gebruik van pre-trained LLM-kennis buiten de graph

---

### 1.2 Componenten

| Component | Technologie |
|--------|------------|
| Frontend | Streamlit |
| Backend data | Neo4j |
| Querylaag | Cypher |
| Chat | LangChain agent met tools |
| Semantisch zoeken | Vector search (optioneel, secundair) |

---

## 2. Informatie-architectuur (MVP)

### 2.1 Hoofdnavigatie

De applicatie bevat de volgende hoofdnavigatie-items:

1. Recepten
2. Categorieën
3. Chat

---

### 2.2 Pagina-overzicht

#### 2.2.1 Recepten – lijst en filters

**Doel:** browsen en filteren van recepten

**Functionaliteit:**
- Faceted filtering op:
  - Land
  - Regio
  - Keuken
  - Kookmethode
  - Ingrediënt
  - Gang
- Meerdere filters tegelijk (AND-logica)
- Resultaatlijst met klik naar detail

---

#### 2.2.2 Receptdetail

**Doel:** volledige weergave van één recept

**Toont:**
- Titel
- Beschrijving
- Ingrediënten
- Bereidingsstappen
- Kookmethode(n)
- Land en regio
- Klikbare categorieën
- Gerelateerde recepten (graph-based)

---

#### 2.2.3 Categorieën – index

**Doel:** alternatieve instap voor exploratie

**Categorie-typen:**
- Landen
- Regio’s
- Keukens
- Kookmethoden
- Ingrediënten

Per categorie wordt het aantal recepten getoond.

---

#### 2.2.4 Categorie-detail

**Doel:** overzicht van recepten binnen één categorie

**Toont:**
- Categorienaam
- Receptenlijst
- Eventueel gerelateerde categorieën

---

#### 2.2.5 Chat

**Doel:** natuurlijke taal als query-interface

**Gedrag:**
- Chat levert altijd:
  - een lijst van recepten, of
  - een verwijzing naar categorieën
- Geen vrije tekst zonder herleidbare data

---

## 3. Streamlit-implementatie

### 3.1 Bestandsstructuur

```text
app.py
pages/
 ├─ 1_Recepten.py
 ├─ 2_Categorieën.py
 ├─ 3_Chat.py
components/
 ├─ filters.py
 ├─ recipe_card.py
 ├─ category_list.py
services/
 ├─ neo4j.py
 ├─ recipe_queries.py
 ├─ category_queries.py
 ├─ chat_agent.py
3.2 Navigatieconfiguratie
python
Copy code
import streamlit as st

st.set_page_config(layout="wide")

st.sidebar.page_link("pages/1_Recepten.py", label="Recepten")
st.sidebar.page_link("pages/2_Categorieën.py", label="Categorieën")
st.sidebar.page_link("pages/3_Chat.py", label="Chat")
3.3 Receptenpagina
Filters
python
Copy code
selected_land = st.multiselect("Land", get_lands())
selected_region = st.multiselect("Regio", get_regions())
selected_method = st.multiselect("Kookmethode", get_methods())
selected_ingredient = st.multiselect("Ingrediënt", get_ingredients())
Query-aanroep
python
Copy code
recipes = search_recipes(
    land=selected_land,
    region=selected_region,
    method=selected_method,
    ingredient=selected_ingredient
)
Weergave
Resultaten worden weergegeven als cards

Klik op card opent receptdetail

3.4 Receptdetailpagina
Recept-ID via queryparameter of st.session_state

Toont volledige Recipe-node en gerelateerde nodes

Klik op categorie → terug naar Receptenpagina met preset filters

3.5 Chatpagina
De bestaande chatbot wordt hier geïntegreerd.

Belangrijke eis:
De chatbot-output moet gestructureerd zijn.

Voorbeeld:

python
Copy code
{
  "type": "recipes",
  "data": [ { "id": "...", "name": "..." } ]
}
De UI rendert deze data, geen vrije tekst.

4. Cypher-queries (MVP)
4.1 Recepten zoeken op filters
c
Copy code
MATCH (r:Recipe)
OPTIONAL MATCH (r)-[:HAS_COUNTRY]->(c:Country)
OPTIONAL MATCH (r)-[:HAS_REGION]->(rg:Region)
OPTIONAL MATCH (r)-[:HAS_METHOD]->(m:CookingMethod)
OPTIONAL MATCH (r)-[:HAS_INGREDIENT]->(i:Ingredient)
WHERE
  ($countries IS NULL OR c.name IN $countries)
  AND ($regions IS NULL OR rg.name IN $regions)
  AND ($methods IS NULL OR m.name IN $methods)
  AND ($ingredients IS NULL OR i.name IN $ingredients)
RETURN DISTINCT r {
  .id,
  .name,
  .description
} AS recipe
ORDER BY recipe.name
4.2 Receptdetail
cypher
Copy code
MATCH (r:Recipe {id: $id})
OPTIONAL MATCH (r)-[:HAS_INGREDIENT]->(i)
OPTIONAL MATCH (r)-[:HAS_METHOD]->(m)
OPTIONAL MATCH (r)-[:HAS_REGION]->(rg)
OPTIONAL MATCH (r)-[:HAS_COUNTRY]->(c)
RETURN r,
       collect(DISTINCT i) AS ingredients,
       collect(DISTINCT m) AS methods,
       rg,
       c
4.3 Gerelateerde recepten
cypher
Copy code
MATCH (r:Recipe {id: $id})-[:HAS_INGREDIENT]->(i)<-[:HAS_INGREDIENT]-(other:Recipe)
WHERE r <> other
RETURN other, count(i) AS sharedIngredients
ORDER BY sharedIngredients DESC
LIMIT 6
4.4 Categorie-index
cypher
Copy code
MATCH (c:Region)<-[:HAS_REGION]-(r:Recipe)
RETURN c.name AS name, count(r) AS recipeCount
ORDER BY recipeCount DESC
4.5 Complexe chatquery (voorbeeld)
cypher
Copy code
MATCH (rg:Region)<-[:HAS_REGION]-(r:Recipe)
WHERE rg.name IN ["bali", "java"]
WITH rg, r
ORDER BY r.name
WITH rg, collect(r)[0..2] AS recipes
RETURN rg.name AS region, recipes
5. Acceptatiecriteria MVP
Alle recepten zijn vindbaar via categorie-navigatie

Chat levert uitsluitend herleidbare data

Geen recepten buiten gevraagde landen of regio’s

Geen LLM-antwoord zonder Neo4j-context

UI en chat gebruiken dezelfde querylaag

6. Niet in scope (bewust)
Persoonlijke accounts

Aanbevelingsalgoritmen

Voedingswaarden

AI-gegenereerde recepten

Social features


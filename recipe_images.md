# Implementatieplan

## Automatische verrijking van recepten met bijpassende afbeeldingen

### Doelgroep

Dit document is bedoeld voor een DevOps- en ontwikkelteam dat verantwoordelijk is voor het implementeren, deployen en beheren van een data‑verrijkingspipeline op basis van RDF/Turtle.

---

## 1. Doel en context

Binnen de receptenkennisgraaf bevatten `schema:Recipe`-instanties momenteel `schema:image`‑verwijzingen naar lokale, niet‑meer‑geldige afbeeldingspaden. Dit document beschrijft een implementeerbare aanpak om deze recepten automatisch te verrijken met valide, externe afbeeldings‑URL’s.

De oplossing is opgezet in twee duidelijk gescheiden fasen:

1. **Fase 1 – Basisverrijking**: snel implementeerbaar, minimale complexiteit
2. **Fase 2 – Kwaliteitsverhogende uitbreidingen**: betere semantische juistheid en beheersbaarheid

Beide fasen zijn expliciet non‑destructief: de oorspronkelijke data blijft behouden.

---

## 2. Uitgangspunten en randvoorwaarden

* Inputdata is beschikbaar als Turtle (`.ttl`)
* Recepten volgen `schema.org/Recipe`
* Semantiek is beschikbaar via:

  * `schema:name`
  * `schema:recipeCuisine`
  * `kb:hasPrimaryIngredient` (optioneel)
* Afbeeldingen worden uitsluitend **gerefereerd**, niet gedownload of opgeslagen
* De verrijking schrijft naar een nieuwe Turtle‑output

---

## 3. Fase 1 – Basisverrijking

### 3.1 Doel

Voor elk recept exact één valide afbeeldings‑URL bepalen en opslaan in `schema:image`.

### 3.2 Scope

**In scope**

* RDF‑parsing en serialisatie
* Automatische zoekquery‑opbouw
* Gebruik van Unsplash Search API
* Overschrijven van bestaande `schema:image`

**Out of scope**

* Beeldinhoudelijke validatie
* Meerdere afbeeldingen per recept
* Culturele of ingredient‑specifieke filtering
* Caching of optimalisatie

---

### 3.3 Architectuuroverzicht

```
Input TTL
  ↓
RDF parsing (rdflib)
  ↓
Zoekquery-opbouw
  ↓
Unsplash Search API
  ↓
Afbeeldings-URL
  ↓
Output TTL
```

---

### 3.4 Functionele stappen

#### Stap 1 – Inlezen data

* Parse alle `schema:Recipe` instanties met `rdflib`

#### Stap 2 – Extractie semantiek

Per recept:

* `schema:name`
* `schema:recipeCuisine`
* `kb:hasPrimaryIngredient` (indien aanwezig)

#### Stap 3 – Constructie zoekquery

Regels:

* Combineer keuken + receptnaam
* Voeg primary ingredient toe indien beschikbaar
* Normaliseer URI‑fragmenten (`-` → spatie)

Voorbeeld:

```
indonesian abon daging rundvlees
```

#### Stap 4 – Afbeelding ophalen

* Gebruik Unsplash Search API
* Parameters:

  * `orientation = landscape`
  * `content_filter = high`
* Neem het eerste resultaat

#### Stap 5 – Verrijking en output

* Vervang bestaande `schema:image`
* Schrijf verrijkte data naar nieuwe `.ttl`

---

### 3.5 Deliverables (Fase 1)

* Python‑script voor batchverrijking
* Verrijkte Turtle‑output
* Console‑logging per recept (zoekquery + resultaat)

### 3.6 Acceptatiecriteria (Fase 1)

* Elk recept bevat exact één geldige `schema:image`
* Output is RDF‑valide
* Script is herhaalbaar uitvoerbaar
* Geen mutatie van originele inputdata

---

## 4. Fase 2 – Kwaliteitsverhogende uitbreidingen

### 4.1 Doel

Verbeteren van semantische correctheid, herhaalbaarheid en uitlegbaarheid van de beeldselectie.

---

### 4.2 Uitbreiding A – Meerdere kandidaten en ranking

**Beschrijving**

* Haal per recept meerdere afbeeldingen op (bijv. top 10)
* Selecteer lokaal de beste match

**Doel**

* Verminderen van generieke of onjuiste food‑afbeeldingen

---

### 4.3 Uitbreiding B – Embedding‑gebaseerde matching

**Beschrijving**

* Zet receptinformatie om naar tekst‑embeddings
* Zet afbeeldingsmetadata of beeld zelf om naar embeddings
* Rangschik op cosine similarity

**Indicatieve modellen (lokaal)**

* OpenCLIP (multimodaal)
* Alternatief: tekst‑embedding op Unsplash‑tags

---

### 4.4 Uitbreiding C – Ingredient‑consistentiecontrole

**Beschrijving**

* Gebruik `kb:hasPrimaryIngredient` als harde constraint
* Filter afbeeldingen met conflicterende eiwitten (kip vs rund)

---

### 4.5 Uitbreiding D – Bronmetadata opslaan

**Beschrijving**

* Leg herkomst en licentie expliciet vast

Voorbeeld:

```ttl
schema:image [
  schema:url "…" ;
  schema:creator "…" ;
  schema:license "https://unsplash.com/license"
] .
```

---

### 4.6 Uitbreiding E – Caching en idempotentie

**Beschrijving**

* Cache op basis van recept‑hash + zoekquery
* Vermijd herhaalde API‑calls

**Implementatieopties**

* JSON‑cache
* SQLite

---

### 4.7 Deliverables (Fase 2)

* Uitgebreide enrichment‑service
* Configureerbare ranking‑strategie
* Logging en kwaliteitsindicatoren
* Documentatie van uitbreidingspunten

### 4.8 Acceptatiecriteria (Fase 2)

* Afbeeldingen corresponderen met primary ingredient
* Idempotente uitvoering
* Fase 1 blijft zelfstandig bruikbaar

---

## 5. Niet‑functionele eisen

* Script moet batch‑uitvoerbaar zijn
* Geen vendor lock‑in buiten Unsplash API
* Heldere logging voor DevOps‑monitoring
* Configuratie via environment variables

---

## 6. Samenvatting

Dit plan biedt een pragmatische instap (Fase 1) met een duidelijk groeipad (Fase 2). De aanpak sluit aan op RDF‑gebaseerde architecturen en kan zonder structurele wijzigingen in de bestaande kennisgraaf worden geïmplementeerd.
@
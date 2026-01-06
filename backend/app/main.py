from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from .services.recipe_queries import (
    search_recipes, get_recipe_details, get_related_recipes,
    get_all_countries, get_all_regions, get_all_methods,
    get_all_ingredients, get_all_main_ingredients
)
from .services.category_queries import get_category_counts, get_ingredients_az
from .services.chat_agent import generate_response

app = FastAPI(title="Indonesische Recepten API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://world-recipes-h9o8i3qef-leonarddunes-projects.vercel.app",  # Jouw daadwerkelijke Vercel URL
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str

@app.get("/api/recipes")
async def api_search_recipes(
    countries: Optional[List[str]] = Query(None),
    regions: Optional[List[str]] = Query(None),
    methods: Optional[List[str]] = Query(None),
    ingredients: Optional[List[str]] = Query(None),
    main_ingredients: Optional[List[str]] = Query(None),
    limit: int = 24,
    skip: int = 0
):
    recipes, total = search_recipes(
        countries=countries,
        regions=regions,
        methods=methods,
        ingredients=ingredients,
        main_ingredients=main_ingredients,
        limit=limit,
        skip=skip
    )
    return {"recipes": recipes, "total": total}

@app.get("/api/recipes/{recipe_id:path}")
async def api_get_recipe_details(recipe_id: str):
    details = get_recipe_details(recipe_id)
    if not details:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    related = get_related_recipes(recipe_id)
    return {"recipe": details['recipe'], "ingredients": details['ingredients'], "related": related}

@app.get("/api/categories")
async def api_get_categories(type: str):
    counts = get_category_counts(type)
    return counts

@app.get("/api/ingredients/az")
async def api_get_ingredients_az(letter: Optional[str] = None):
    return get_ingredients_az(letter)

@app.get("/api/filters")
async def api_get_filters():
    return {
        "countries": get_all_countries(),
        "regions": get_all_regions(),
        "methods": get_all_methods(),
        "ingredients": get_all_ingredients(),
        "main_ingredients": get_all_main_ingredients()
    }

@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(request: ChatRequest):
    try:
        response = generate_response(request.message, request.session_id)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

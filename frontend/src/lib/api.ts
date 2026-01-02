import { SearchResponse, Recipe, CategoryCount, FilterOptions } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function fetchRecipes(params: Record<string, any> = {}): Promise<SearchResponse> {
    const queryParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
        if (value) {
            if (Array.isArray(value)) {
                value.forEach(v => queryParams.append(key, v));
            } else {
                queryParams.append(key, value.toString());
            }
        }
    });

    const res = await fetch(`${API_BASE_URL}/recipes?${queryParams.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch recipes');
    return res.json();
}

export async function fetchRecipeDetails(id: string): Promise<{ recipe: Recipe; ingredients: any[]; related: any[] }> {
    const res = await fetch(`${API_BASE_URL}/recipes/${encodeURIComponent(id)}`);
    if (!res.ok) throw new Error('Failed to fetch recipe details');
    return res.json();
}

export async function fetchCategories(type: string): Promise<CategoryCount[]> {
    const res = await fetch(`${API_BASE_URL}/categories?type=${type}`);
    if (!res.ok) throw new Error('Failed to fetch categories');
    return res.json();
}

export async function fetchIngredientsAZ(letter?: string): Promise<{ name: string; recipeCount: number }[]> {
    const url = letter ? `${API_BASE_URL}/ingredients/az?letter=${letter}` : `${API_BASE_URL}/ingredients/az`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch ingredients');
    return res.json();
}

export async function fetchFilters(): Promise<FilterOptions> {
    const res = await fetch(`${API_BASE_URL}/filters`);
    if (!res.ok) throw new Error('Failed to fetch filters');
    return res.json();
}

export async function sendChatMessage(message: string, sessionId: string): Promise<{ response: string }> {
    const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId }),
    });
    if (!res.ok) throw new Error('Failed to send message');
    return res.json();
}

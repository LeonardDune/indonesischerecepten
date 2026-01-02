export interface Recipe {
    id: string;
    name: string;
    image: string | null;
    description: string | null;
    yield: string | null;
    mainIngredient: string | null;
    countries: string[];
    regions: string[];
    methods: string[];
    instructions?: string;
}

export interface SearchResponse {
    recipes: Recipe[];
    total: number;
}

export interface CategoryCount {
    name: string;
    recipeCount: number;
    image: string | null;
}

export interface FilterOptions {
    countries: string[];
    regions: string[];
    methods: string[];
    ingredients: string[];
    main_ingredients: string[];
}

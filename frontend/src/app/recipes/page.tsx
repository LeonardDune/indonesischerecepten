'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { RecipeCard } from '@/components/RecipeCard';
import { Filters } from '@/components/Filters';
import { fetchRecipes, fetchFilters } from '@/lib/api';
import { Recipe, FilterOptions } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, ChevronLeft, ChevronRight, Search } from 'lucide-react';

const LIMIT = 24;

function RecipesContent() {
    const searchParams = useSearchParams();
    const router = useRouter();

    const [recipes, setRecipes] = useState<Recipe[]>([]);
    const [total, setTotal] = useState(0);
    const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);

    // Get current filters from search params
    const getActiveFilters = () => {
        const filters: Record<string, string[]> = {
            country: searchParams.getAll('country'),
            region: searchParams.getAll('region'),
            method: searchParams.getAll('method'),
            main_ingredient: searchParams.getAll('main_ingredient'),
            ingredients: searchParams.getAll('ingredients'),
        };
        return filters;
    };

    const activeFilters = getActiveFilters();

    useEffect(() => {
        async function loadOptions() {
            try {
                const options = await fetchFilters();
                setFilterOptions(options);
            } catch (err) {
                console.error("Error loading filter options:", err);
            }
        }
        loadOptions();
    }, []);

    useEffect(() => {
        async function loadRecipes() {
            setLoading(true);
            try {
                const params: any = {
                    limit: LIMIT,
                    skip: (page - 1) * LIMIT,
                };

                if (activeFilters.country.length > 0) params.countries = activeFilters.country;
                if (activeFilters.region.length > 0) params.regions = activeFilters.region;
                if (activeFilters.method.length > 0) params.methods = activeFilters.method;
                if (activeFilters.main_ingredient.length > 0) params.main_ingredients = activeFilters.main_ingredient;
                if (activeFilters.ingredients.length > 0) params.ingredients = activeFilters.ingredients;

                const res = await fetchRecipes(params);
                setRecipes(res.recipes);
                setTotal(res.total);
            } catch (err) {
                console.error("Error loading recipes:", err);
            } finally {
                setLoading(false);
            }
        }
        loadRecipes();
    }, [searchParams, page]);

    const handleFilterChange = (type: string, value: string) => {
        const current = new URLSearchParams(searchParams.toString());
        const values = current.getAll(type);

        if (values.includes(value)) {
            // Remove value
            const updated = values.filter(v => v !== value);
            current.delete(type);
            updated.forEach(v => current.append(type, v));
        } else {
            // Add value
            if (type === 'main_ingredient') {
                current.set(type, value); // Main ingredient is single select usually
            } else {
                current.append(type, value);
            }
        }

        current.delete('page'); // Reset to page 1 on filter change
        setPage(1);
        router.push(`/recipes?${current.toString()}`);
    };

    const handleReset = () => {
        router.push('/recipes');
        setPage(1);
    };

    const totalPages = Math.ceil(total / LIMIT);

    return (
        <div className="flex flex-col md:flex-row gap-8 items-start">
            {/* Mobile Filter Toggle */}
            <div className="md:hidden w-full mb-4">
                <details className="group">
                    <summary className="flex items-center justify-between p-4 glass rounded-xl list-none cursor-pointer text-white font-bold">
                        <span>Filters & Zoeken</span>
                        <ChevronRight className="transition-transform group-open:rotate-90" size={20} />
                    </summary>
                    <div className="mt-4">
                        {filterOptions ? (
                            <Filters
                                options={filterOptions}
                                selected={activeFilters}
                                onChange={handleFilterChange}
                                onReset={handleReset}
                            />
                        ) : (
                            <div className="glass h-40 rounded-xl animate-pulse" />
                        )}
                    </div>
                </details>
            </div>

            {/* Desktop Sidebar Filters */}
            <aside className="hidden md:block w-80 shrink-0 sticky top-24">
                {filterOptions ? (
                    <Filters
                        options={filterOptions}
                        selected={activeFilters}
                        onChange={handleFilterChange}
                        onReset={handleReset}
                    />
                ) : (
                    <div className="glass h-96 rounded-2xl animate-pulse" />
                )}
            </aside>

            {/* Main Content */}
            <div className="flex-1 space-y-8 w-full">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl md:text-3xl font-black text-white">Recepten</h1>
                        <p className="text-slate-500 text-sm mt-1">
                            {total} authentieke gerechten gevonden
                        </p>
                    </div>

                    <div className="flex items-center gap-2 self-end md:self-auto">
                        <button
                            disabled={page === 1}
                            onClick={() => setPage(p => p - 1)}
                            className="p-2 glass rounded-xl disabled:opacity-30 disabled:cursor-not-allowed hover:bg-white/10 transition-all"
                        >
                            <ChevronLeft size={20} />
                        </button>
                        <span className="text-sm font-bold text-slate-400 px-3">
                            Pagina {page} van {totalPages || 1}
                        </span>
                        <button
                            disabled={page >= totalPages}
                            onClick={() => setPage(p => p + 1)}
                            className="p-2 glass rounded-xl disabled:opacity-30 disabled:cursor-not-allowed hover:bg-white/10 transition-all"
                        >
                            <ChevronRight size={20} />
                        </button>
                    </div>
                </div>

                {/* Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                        {[1, 2, 3, 4, 5, 6].map(i => (
                            <div key={i} className="h-40 md:h-80 glass rounded-2xl animate-pulse" />
                        ))}
                    </div>
                ) : recipes.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                        {recipes.map((recipe) => (
                            <RecipeCard
                                key={recipe.id}
                                recipe={recipe}
                                onTagClick={(type, val) => handleFilterChange(type, val)}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20 glass rounded-3xl">
                        <Search size={48} className="mx-auto text-slate-700 mb-4" />
                        <h3 className="text-xl font-bold text-slate-400">Geen recepten gevonden</h3>
                        <p className="text-slate-500 mt-2">Probeer andere filters te gebruiken.</p>
                        <button
                            onClick={handleReset}
                            className="mt-6 px-6 py-2 bg-primary text-white font-bold rounded-xl"
                        >
                            Filters Wissen
                        </button>
                    </div>
                )}

                {/* Footer Pagination */}
                {totalPages > 1 && (
                    <div className="flex justify-center pt-10">
                        <div className="flex items-center gap-2">
                            <button
                                disabled={page === 1}
                                onClick={() => { setPage(1); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                                className="px-4 py-2 glass rounded-xl disabled:opacity-30 hover:bg-white/10"
                            >
                                Eerste
                            </button>
                            <button
                                disabled={page === 1}
                                onClick={() => { setPage(p => p - 1); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                                className="p-2 glass rounded-xl disabled:opacity-30 hover:bg-white/10"
                            >
                                <ChevronLeft size={20} />
                            </button>
                            <div className="hidden md:flex gap-1">
                                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                                    const p = page <= 3 ? i + 1 : (page >= totalPages - 2 ? totalPages - 4 + i : page - 2 + i);
                                    if (p <= 0 || p > totalPages) return null;
                                    return (
                                        <button
                                            key={p}
                                            onClick={() => { setPage(p); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                                            className={`w-10 h-10 rounded-xl font-bold text-sm transition-all ${p === page ? "bg-primary text-white" : "glass text-slate-400 hover:bg-white/10"
                                                }`}
                                        >
                                            {p}
                                        </button>
                                    );
                                })}
                            </div>
                            <button
                                disabled={page >= totalPages}
                                onClick={() => { setPage(p => p + 1); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                                className="p-2 glass rounded-xl disabled:opacity-30 hover:bg-white/10"
                            >
                                <ChevronRight size={20} />
                            </button>
                            <button
                                disabled={page >= totalPages}
                                onClick={() => { setPage(totalPages); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                                className="px-4 py-2 glass rounded-xl disabled:opacity-30 hover:bg-white/10"
                            >
                                Laatste
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function RecipesPage() {
    return (
        <Suspense fallback={<div className="flex items-center justify-center min-h-[50vh]"><Loader2 className="animate-spin text-primary" size={48} /></div>}>
            <RecipesContent />
        </Suspense>
    );
}

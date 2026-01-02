'use client';

import React, { useEffect, useState } from 'react';
import { fetchIngredientsAZ } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Search, ChefHat, Sparkles, Loader2, Filter } from 'lucide-react';

export default function IngredientsPage() {
    const router = useRouter();
    const [ingredients, setIngredients] = useState<{ name: string; recipeCount: number }[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [activeLetter, setActiveLetter] = useState<string | null>(null);

    const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

    useEffect(() => {
        async function load() {
            setLoading(true);
            try {
                const data = await fetchIngredientsAZ(activeLetter || undefined);
                setIngredients(data);
            } catch (err) {
                console.error("Error loading ingredients:", err);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [activeLetter]);

    const filteredIngredients = ingredients.filter(i =>
        i.name.toLowerCase().includes(search.toLowerCase())
    );

    const handleIngredientClick = (name: string) => {
        router.push(`/recipes?ingredients=${encodeURIComponent(name)}`);
    };

    return (
        <div className="space-y-10 pb-20">
            <header className="max-w-3xl">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-2 text-primary font-bold text-sm uppercase tracking-widest mb-4"
                >
                    <ChefHat size={16} />
                    De Smaakmakers
                </motion.div>
                <h1 className="text-5xl font-black text-white mb-4 leading-tight">
                    Ontdek per <span className="text-primary italic">Ingrediënt</span>.
                </h1>
                <p className="text-slate-400 text-lg">
                    Zoek op een specifiek ingrediënt om alle bijbehorende recepten te vinden.
                    Van zeldzame kruiden tot alledaagse basisproducten.
                </p>
            </header>

            {/* Search and A-Z Bar */}
            <div className="space-y-6">
                <div className="relative max-w-xl">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
                    <input
                        type="search"
                        placeholder="Zoek een ingrediënt..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-primary/50 transition-all"
                    />
                </div>

                <div className="flex flex-wrap gap-2">
                    <button
                        onClick={() => setActiveLetter(null)}
                        className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${activeLetter === null
                            ? "bg-primary text-white shadow-lg shadow-primary/20"
                            : "bg-white/5 text-slate-400 hover:text-white hover:bg-white/10"
                            }`}
                    >
                        ALLES
                    </button>
                    {alphabet.map(letter => (
                        <button
                            key={letter}
                            onClick={() => setActiveLetter(letter)}
                            className={`w-10 h-10 flex items-center justify-center rounded-xl text-sm font-bold transition-all ${activeLetter === letter
                                ? "bg-primary text-white shadow-lg shadow-primary/20"
                                : "bg-white/5 text-slate-400 hover:text-white hover:bg-white/10"
                                }`}
                        >
                            {letter}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content Grid */}
            <div className="min-h-[400px]">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-[400px] space-y-6">
                        <Loader2 className="animate-spin text-primary" size={48} />
                        <p className="text-slate-500 font-bold tracking-widest uppercase text-xs">Ingrediënten laden...</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        <AnimatePresence mode="popLayout">
                            {filteredIngredients.map((ing, idx) => (
                                <motion.div
                                    key={ing.name}
                                    layout
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.9 }}
                                    whileHover={{ x: 4 }}
                                    transition={{ duration: 0.2 }}
                                    onClick={() => handleIngredientClick(ing.name)}
                                    className="glass glass-hover p-4 rounded-2xl cursor-pointer group flex items-center justify-between"
                                >
                                    <div className="flex items-center gap-3 overflow-hidden">
                                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                            <ChefHat size={14} className="text-primary/70 group-hover:text-primary transition-colors" />
                                        </div>
                                        <span className="text-slate-200 font-medium truncate group-hover:text-white transition-colors capitalize">
                                            {ing.name}
                                        </span>
                                    </div>
                                    <span className="text-[10px] font-bold bg-white/5 px-2 py-1 rounded-lg text-slate-500 group-hover:text-primary/80 transition-colors">
                                        {ing.recipeCount}
                                    </span>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                )}
            </div>
        </div>
    );
}

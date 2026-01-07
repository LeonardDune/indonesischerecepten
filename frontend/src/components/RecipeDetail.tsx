'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Users, Flame, ChevronLeft, Printer, Share2 } from 'lucide-react';
import { Recipe } from '@/types';
import { useRouter } from 'next/navigation';
import { RecipeCard } from './RecipeCard';

interface RecipeDetailProps {
    recipe: Recipe;
    ingredients: any[];
    related: any[];
}

export const RecipeDetail: React.FC<RecipeDetailProps> = ({ recipe, ingredients, related }) => {
    const router = useRouter();

    return (
        <div className="max-w-5xl mx-auto space-y-6 md:space-y-10 pb-20">
            {/* Header / Back Navigation */}
            <div className="flex items-center justify-between">
                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors group text-sm md:text-base"
                >
                    <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
                    Terug naar overzicht
                </button>
                <div className="flex items-center gap-3">
                    <button className="p-2 glass rounded-xl text-slate-400 hover:text-white transition-all">
                        <Printer size={20} />
                    </button>
                    <button className="p-2 glass rounded-xl text-slate-400 hover:text-white transition-all">
                        <Share2 size={20} />
                    </button>
                </div>
            </div>

            {/* Hero Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-10 items-start">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="aspect-video md:aspect-square rounded-3xl overflow-hidden glass shadow-2xl"
                >
                    {recipe.image ? (
                        <img
                            src={recipe.image}
                            alt={recipe.name}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full bg-slate-800 flex items-center justify-center text-slate-500 italic">
                            Geen afbeelding beschikbaar
                        </div>
                    )}
                </motion.div>

                <div className="space-y-6">
                    <div>
                        <div className="flex flex-wrap gap-2 mb-4">
                            {recipe.countries.map(c => (
                                <span key={c} className="px-3 py-1 bg-primary/20 text-primary text-[10px] md:text-xs font-bold uppercase tracking-wider rounded-full">
                                    {c}
                                </span>
                            ))}
                            {recipe.regions.map(r => (
                                <span key={r} className="px-3 py-1 bg-secondary/20 text-secondary text-[10px] md:text-xs font-bold uppercase tracking-wider rounded-full">
                                    {r}
                                </span>
                            ))}
                            {recipe.mainIngredient && (
                                <span className="px-3 py-1 bg-purple-500/20 text-purple-400 text-[10px] md:text-xs font-bold uppercase tracking-wider rounded-full">
                                    {recipe.mainIngredient}
                                </span>
                            )}
                        </div>
                        <h1 className="text-2xl md:text-4xl font-black text-white leading-tight">
                            {recipe.name}
                        </h1>
                    </div>

                    <p className="text-slate-400 text-base md:text-lg leading-relaxed">
                        {recipe.description || "Geen beschrijving beschikbaar voor dit authentieke recept."}
                    </p>

                    <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/5">
                        <div className="text-center p-4 glass rounded-2xl">
                            <Clock className="mx-auto text-primary mb-2" size={24} />
                            <div className="text-xs text-slate-500 uppercase font-bold">Tijd</div>
                            <div className="text-white font-bold">30 min</div>
                        </div>
                        <div className="text-center p-4 glass rounded-2xl">
                            <Users className="mx-auto text-secondary mb-2" size={24} />
                            <div className="text-xs text-slate-500 uppercase font-bold">Serves</div>
                            <div className="text-white font-bold">{recipe.yield || "4 pers."}</div>
                        </div>
                        <div className="text-center p-4 glass rounded-2xl">
                            <Flame className="mx-auto text-orange-500 mb-2" size={24} />
                            <div className="text-xs text-slate-500 uppercase font-bold">Methode</div>
                            <div className="text-white font-bold capitalize">{recipe.methods[0] || "Bakken"}</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Ingredients & Instructions */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                <div className="lg:col-span-1 space-y-6">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <UtensilsCrossed className="text-primary" size={24} />
                        Ingrediënten
                    </h2>
                    <ul className="space-y-3">
                        {ingredients.map((ing, idx) => (
                            <li key={idx} className="flex justify-between items-center p-3 glass rounded-xl text-sm group hover:bg-white/5 transition-colors">
                                <span className="text-slate-100 font-medium">{ing.name}</span>
                                <span className="text-primary font-bold">{ing.value} {ing.unit}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="lg:col-span-2 space-y-6">
                    <h2 className="text-2xl font-bold text-white">Bereiding</h2>
                    <div className="glass p-8 rounded-3xl space-y-6 text-slate-300 leading-relaxed">
                        {recipe.instructions ? (
                            (Array.isArray(recipe.instructions) ? recipe.instructions.map(step => step.replace(/^\d+\.\s+/, '')) : recipe.instructions.split('\n').filter(s => s.trim())).map((step, idx) => (
                                <div key={idx} className="flex gap-6 items-start group">
                                    <span className="shrink-0 w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm">
                                        {idx + 1}
                                    </span>
                                    <p className="flex-1 pt-1">{step}</p>
                                </div>
                            ))
                        ) : (
                            <p className="italic text-slate-500">Geen instructies beschikbaar.</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Related Recipes */}
            {related.length > 0 && (
                <div className="pt-10 border-t border-white/5 space-y-8">
                    <h2 className="text-2xl font-bold text-white">Gerelateerde Recepten</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {related.map((r, idx) => (
                            <RecipeCard key={idx} recipe={r.recipe} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

// Internal icon for this file wrap
function UtensilsCrossed(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="m16 2-2.3 2.3a3 3 0 0 0 0 4.2l1.8 1.8a3 3 0 0 0 4.2 0L22 8" />
            <path d="M2 22l1.35-1.35" />
            <path d="M11 8l3 3" />
            <path d="M12 2v2" />
            <path d="M14.2 5.2 16 7" />
            <path d="M2 2l11 11" />
            <path d="M22 22l-11-11" />
            <path d="M7 16 5.2 14.2" />
            <path d="M12 22v-2" />
        </svg>
    );
}

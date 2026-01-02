'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { RecipeDetail } from '@/components/RecipeDetail';
import { fetchRecipeDetails } from '@/lib/api';
import { Recipe } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';

export default function RecipePage() {
    const params = useParams();
    // In [...id], params.id is an array.
    const idParts = params.id as string[];
    const [data, setData] = useState<{ recipe: Recipe; ingredients: any[]; related: any[] } | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            if (!idParts || idParts.length === 0) return;

            try {
                setLoading(true);
                // Join segments back into a URI. 
                // Next.js catch-all decodes URI segments, so we join with '/'
                let id = idParts.join('/');

                // Fix for common URI decoding quirks where // becomes /
                if (id.startsWith('https:/') && !id.startsWith('https://')) {
                    id = id.replace('https:/', 'https://');
                } else if (id.startsWith('http:/') && !id.startsWith('http://')) {
                    id = id.replace('http:/', 'http://');
                }

                const res = await fetchRecipeDetails(id);
                setData(res);
            } catch (err) {
                console.error("Error loading recipe:", err);
                setError("Kon het recept niet laden. Probeer het later opnieuw.");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [idParts]);

    return (
        <AnimatePresence mode="wait">
            {loading ? (
                <motion.div
                    key="loader"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center justify-center min-h-[60vh] space-y-4"
                >
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    <p className="text-slate-500 font-medium">Recept laden...</p>
                </motion.div>
            ) : error ? (
                <motion.div
                    key="error"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-20"
                >
                    <h2 className="text-2xl font-bold text-red-500 mb-4">{error}</h2>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-6 py-2 glass rounded-xl text-white hover:bg-white/10 transition-all"
                    >
                        Probeer opnieuw
                    </button>
                </motion.div>
            ) : data ? (
                <motion.div
                    key="content"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <RecipeDetail
                        recipe={data.recipe}
                        ingredients={data.ingredients}
                        related={data.related}
                    />
                </motion.div>
            ) : null}
        </AnimatePresence>
    );
}

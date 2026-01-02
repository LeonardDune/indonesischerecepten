'use client';

import React, { useEffect, useState } from 'react';
import { RecipeCard } from '@/components/RecipeCard';
import { fetchRecipes } from '@/lib/api';
import { Recipe } from '@/types';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ChevronRight, Sparkles, MessageSquare } from 'lucide-react';

export default function Home() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadRecipes() {
      try {
        const data = await fetchRecipes({ limit: 6 });
        setRecipes(data.recipes);
      } catch (error) {
        console.error('Error loading recipes:', error);
      } finally {
        setLoading(false);
      }
    }
    loadRecipes();
  }, []);

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="relative py-12">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center gap-2 text-primary font-bold tracking-widest uppercase text-xs mb-4">
            <Sparkles size={16} />
            <span>Ontdek wereldsmaken</span>
          </div>
          <h1 className="text-6xl font-black mb-6 leading-tight">
            Vind je volgende <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-orange-400">
              Culinair Avontuur
            </span>
          </h1>
          <p className="text-slate-400 text-lg max-w-xl mb-8 leading-relaxed">
            Blader door duizenden authentieke recepten uit diverse keukens.
            Vraag onze AI-assistent om advies of ontdek per regio of methode.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link href="/recipes" className="px-8 py-4 bg-primary text-white font-bold rounded-2xl hover:bg-orange-600 transition-all shadow-lg shadow-primary/20 flex items-center gap-2 group">
              Start Nu
              <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link href="/categories" className="px-8 py-4 glass text-white font-bold rounded-2xl hover:bg-white/5 transition-all">
              Verken Keukens
            </Link>
            <Link href="/chat" className="px-8 py-4 bg-secondary/20 text-secondary border border-secondary/30 font-bold rounded-2xl hover:bg-secondary/30 transition-all flex items-center gap-2 group">
              <MessageSquare size={20} />
              Vraag de Assistent
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Featured Recipes */}
      <section>
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold">Populaire Recepten</h2>
          <Link href="/recipes" className="text-primary hover:text-orange-400 transition-colors text-sm font-semibold flex items-center gap-1 group">
            Bekijk Alles
            <ChevronRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-80 glass rounded-2xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recipes.map((recipe) => (
              <RecipeCard key={recipe.id} recipe={recipe} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

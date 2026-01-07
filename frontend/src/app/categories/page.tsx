'use client';

import React, { useEffect, useState } from 'react';
import { fetchCategories } from '@/lib/api';
import { CategoryCount } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Map, Globe, Utensils, Loader2, Sparkles, ChefHat } from 'lucide-react';

export default function CategoriesPage() {
    const router = useRouter();
    const [activeTab, setActiveTab] = useState('country');
    const [counts, setCounts] = useState<CategoryCount[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            setLoading(true);
            try {
                const data = await fetchCategories(activeTab);
                setItems(data);
            } catch (err) {
                console.error("Error loading categories:", err);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [activeTab]);

    const setItems = (data: CategoryCount[]) => {
        setCounts(data);
    };

    const handleCategoryClick = (name: string) => {
        router.push(`/recipes?${activeTab}=${encodeURIComponent(name)}`);
    };

    const tabs = [
        { id: 'country', label: 'Keukens', icon: Globe },
        { id: 'region', label: 'Regio\'s', icon: Map },
        { id: 'method', label: 'Methodes', icon: Utensils },
        { id: 'main_ingredient', label: 'Hoofdingrediënten', icon: ChefHat },
    ];

    return (
        <div className="space-y-12 pb-20">
            <header className="max-w-3xl">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-2 text-primary font-bold text-sm uppercase tracking-widest mb-4"
                >
                    <Sparkles size={16} />
                    Ontdek de collectie
                </motion.div>
                <h1 className="text-3xl md:text-5xl font-black text-white mb-4 leading-tight">
                    De <span className="text-primary italic">Smaak</span> van de Wereld.
                </h1>
                <p className="text-slate-400 text-lg">
                    Blader door onze uitgebreide verzameling authentieke recepten,
                    gecategoriseerd op herkomst, regio en bereidingswijze.
                </p>
            </header>

            {/* Custom Tabs */}
            <div className="flex flex-nowrap md:flex-wrap gap-2 p-1.5 glass rounded-3xl w-full md:w-fit overflow-x-auto scrollbar-hide">
                {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-3 px-6 md:px-8 py-4 rounded-2xl transition-all duration-500 whitespace-nowrap shrink-0 ${isActive
                                ? "bg-primary text-white shadow-xl shadow-primary/30 scale-105"
                                : "text-slate-400 hover:text-white hover:bg-white/5"
                                }`}
                        >
                            <Icon size={20} className={isActive ? "animate-pulse" : ""} />
                            <span className="font-black text-sm uppercase tracking-wider">{tab.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* Content Grid */}
            <div className="min-h-[400px]">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-[400px] space-y-6">
                        <div className="relative">
                            <div className="w-16 h-16 border-4 border-primary/20 rounded-full" />
                            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin absolute top-0 left-0" />
                        </div>
                        <p className="text-slate-500 font-bold tracking-widest uppercase text-xs">Categorieën laden...</p>
                    </div>
                ) : (
                    <motion.div
                        layout
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8"
                    >
                        <AnimatePresence mode="popLayout">
                            {counts.map((cat, idx) => (
                                <motion.div
                                    key={cat.name}
                                    layout
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.9 }}
                                    whileHover={{ y: -8 }}
                                    transition={{ duration: 0.4, delay: idx * 0.05 }}
                                    onClick={() => handleCategoryClick(cat.name)}
                                    className="group relative h-80 rounded-[2.5rem] overflow-hidden cursor-pointer shadow-2xl shadow-black/50"
                                >
                                    {/* Image Background */}
                                    {cat.image ? (
                                        <img
                                            src={cat.image}
                                            alt={cat.name}
                                            className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                        />
                                    ) : (
                                        <div className="absolute inset-0 bg-slate-900 group-hover:bg-slate-800 transition-colors" />
                                    )}

                                    {/* Overlay */}
                                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent opacity-80 group-hover:opacity-90 transition-opacity" />

                                    {/* Content */}
                                    <div className="absolute inset-0 p-8 flex flex-col justify-end">
                                        <div className="flex items-center gap-3 mb-2">
                                            <div className="w-8 h-8 rounded-xl bg-primary/20 backdrop-blur-md flex items-center justify-center">
                                                {activeTab === 'country' && <Globe size={16} className="text-primary" />}
                                                {activeTab === 'region' && <Map size={16} className="text-secondary" />}
                                                {activeTab === 'method' && <Utensils size={16} className="text-orange-400" />}
                                                {activeTab === 'main_ingredient' && <ChefHat size={16} className="text-purple-400" />}
                                            </div>
                                            <span className="text-[10px] font-bold text-white/50 uppercase tracking-widest">
                                                {cat.recipeCount} {cat.recipeCount === 1 ? 'Recept' : 'Recepten'}
                                            </span>
                                        </div>
                                        <h3 className="text-2xl font-black text-white uppercase tracking-tight group-hover:text-primary transition-colors">
                                            {cat.name}
                                        </h3>

                                        <motion.div
                                            initial={{ opacity: 0, x: -10 }}
                                            whileHover={{ opacity: 1, x: 0 }}
                                            className="flex items-center gap-2 text-xs font-bold text-primary mt-4 opacity-0 group-hover:opacity-100 transition-all"
                                        >
                                            BEKIJK COLLECTIE <Sparkles size={12} />
                                        </motion.div>
                                    </div>

                                    {/* Counter Badge */}
                                    <div className="absolute top-6 right-6 w-10 h-10 rounded-2xl bg-white/10 backdrop-blur-xl border border-white/10 flex items-center justify-center text-sm font-black text-white/40">
                                        {idx + 1}
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </motion.div>
                )}
            </div>
        </div>
    );
}

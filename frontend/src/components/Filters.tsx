'use client';

import React from 'react';
import { FilterOptions } from '@/types';
import { ChevronDown, ChevronUp, X } from 'lucide-react';

interface FiltersProps {
    options: FilterOptions;
    selected: Record<string, string[]>;
    onChange: (type: string, value: string) => void;
    onReset: () => void;
}

export const Filters: React.FC<FiltersProps> = ({ options, selected, onChange, onReset }) => {
    const hasFilters = Object.values(selected).some(v => v.length > 0);

    return (
        <div className="space-y-8 glass p-6 rounded-2xl md:sticky md:top-24">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <h3 className="font-bold text-white flex items-center gap-2">
                    Filters
                </h3>
                {hasFilters && (
                    <button
                        onClick={onReset}
                        className="text-xs text-primary hover:text-orange-400 font-medium flex items-center gap-1 transition-colors"
                    >
                        Reset <X size={12} />
                    </button>
                )}
            </div>

            {/* Cuisine Filter */}
            <div className="space-y-3">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Keuken</label>
                <div className="flex flex-wrap gap-2">
                    {options.countries.map(country => (
                        <button
                            key={country}
                            onClick={() => onChange('country', country)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${selected.country?.includes(country)
                                ? "bg-primary text-white shadow-lg shadow-primary/20"
                                : "bg-white/5 text-slate-400 hover:bg-white/10"
                                }`}
                        >
                            {country}
                        </button>
                    ))}
                </div>
            </div>

            {/* Region Filter */}
            <div className="space-y-3">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Regio</label>
                <div className="flex flex-wrap gap-2">
                    {options.regions.map(region => (
                        <button
                            key={region}
                            onClick={() => onChange('region', region)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${selected.region?.includes(region)
                                ? "bg-secondary text-white shadow-lg shadow-secondary/20"
                                : "bg-white/5 text-slate-400 hover:bg-white/10"
                                }`}
                        >
                            {region}
                        </button>
                    ))}
                </div>
            </div>

            {/* Method Filter */}
            <div className="space-y-3">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Kookmethode</label>
                <div className="flex flex-wrap gap-2">
                    {options.methods.map(method => (
                        <button
                            key={method}
                            onClick={() => onChange('method', method)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${selected.method?.includes(method)
                                ? "bg-orange-500/80 text-white shadow-lg shadow-orange-500/20"
                                : "bg-white/5 text-slate-400 hover:bg-white/10"
                                }`}
                        >
                            {method}
                        </button>
                    ))}
                </div>
            </div>

            {/* Main Ingredient */}
            <div className="space-y-3">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Hoofdingrediënt</label>
                <select
                    className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-slate-300 outline-none focus:border-primary/50 transition-all shadow-xl"
                    onChange={(e) => onChange('main_ingredient', e.target.value)}
                    value={selected.main_ingredient?.[0] || ""}
                >
                    <option value="">Alle hoofdingrediënten</option>
                    {options.main_ingredients.map(ing => (
                        <option key={ing} value={ing}>{ing}</option>
                    ))}
                </select>
            </div>

            {/* General Ingredients */}
            <div className="space-y-3">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Ingrediënten</label>
                <input
                    list="ingredient-options"
                    placeholder="Zoek ingrediënt..."
                    className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-slate-300 outline-none focus:border-primary/50 transition-all shadow-xl"
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            const val = (e.currentTarget as HTMLInputElement).value;
                            if (val && options.ingredients.includes(val)) {
                                onChange('ingredients', val);
                                (e.currentTarget as HTMLInputElement).value = '';
                            }
                        }
                    }}
                    onBlur={(e) => {
                        const val = (e.currentTarget as HTMLInputElement).value;
                        if (val && options.ingredients.includes(val)) {
                            onChange('ingredients', val);
                            (e.currentTarget as HTMLInputElement).value = '';
                        }
                    }}
                />
                <datalist id="ingredient-options">
                    {options.ingredients.map(ing => (
                        <option key={ing} value={ing} />
                    ))}
                </datalist>

                {/* Selected Ingredients Tags */}
                <div className="flex flex-wrap gap-2 mt-2">
                    {selected.ingredients?.map(ing => (
                        <button
                            key={ing}
                            onClick={() => onChange('ingredients', ing)}
                            className="flex items-center gap-1.5 px-2 py-1 bg-primary/20 text-primary rounded-lg text-xs font-bold border border-primary/20 hover:bg-primary/30 transition-all"
                        >
                            {ing} <X size={10} />
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

'use client';

import { motion } from 'framer-motion';
import { Clock, Users, Flame } from 'lucide-react';
import { Recipe } from '@/types';
import { useRouter } from 'next/navigation';

interface RecipeCardProps {
    recipe: Recipe;
    onTagClick?: (type: string, value: string) => void;
}

export const RecipeCard: React.FC<RecipeCardProps> = ({ recipe, onTagClick }) => {
    const router = useRouter();

    const handleCardClick = (e: React.MouseEvent) => {
        // Prevent navigation if clicking on a tag button
        if ((e.target as HTMLElement).closest('.tag-button')) return;
        router.push(`/recipes/detail?id=${encodeURIComponent(recipe.id)}`);
    };

    const handleTagClick = (e: React.MouseEvent, type: string, value: string) => {
        e.stopPropagation();
        if (onTagClick) {
            onTagClick(type, value);
        } else {
            // Default behavior: navigate to recipes page with filter
            router.push(`/recipes?${type}=${encodeURIComponent(value)}`);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5 }}
            transition={{ duration: 0.3 }}
            className="glass glass-hover overflow-hidden rounded-2xl group cursor-pointer h-full flex flex-col"
            onClick={handleCardClick}
        >
            {/* Image Container */}
            <div className="relative h-48 w-full overflow-hidden shrink-0">
                {recipe.image ? (
                    <img
                        src={recipe.image}
                        alt={recipe.name}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                ) : (
                    <div className="w-full h-full bg-slate-800 flex items-center justify-center text-slate-500 italic">
                        Geen afbeelding
                    </div>
                )}
                <div className="absolute top-3 left-3 flex flex-wrap gap-2 pr-3">
                    {recipe.countries.map(country => (
                        <button
                            key={country}
                            onClick={(e) => handleTagClick(e, 'country', country)}
                            className="tag-button px-2 py-1 text-[10px] font-bold uppercase tracking-wider bg-primary text-white rounded-full hover:bg-orange-600 transition-colors shadow-sm"
                        >
                            {country}
                        </button>
                    ))}
                    {recipe.regions.map(region => (
                        <button
                            key={region}
                            onClick={(e) => handleTagClick(e, 'region', region)}
                            className="tag-button px-2 py-1 text-[10px] font-bold uppercase tracking-wider bg-secondary text-white rounded-full hover:bg-emerald-600 transition-colors shadow-sm"
                        >
                            {region}
                        </button>
                    ))}
                    {recipe.mainIngredient && (
                        <button
                            onClick={(e) => handleTagClick(e, 'main_ingredient', recipe.mainIngredient!)}
                            className="tag-button px-2 py-1 text-[10px] font-bold uppercase tracking-wider bg-purple-600 text-white rounded-full hover:bg-purple-700 transition-colors shadow-sm"
                        >
                            {recipe.mainIngredient}
                        </button>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="p-5 flex flex-col flex-1">
                <h3 className="text-lg font-bold text-white mb-2 line-clamp-2 group-hover:text-primary transition-colors min-h-[3.5rem]">
                    {recipe.name}
                </h3>

                <p className="text-sm text-slate-400 line-clamp-2 mb-4 h-10 overflow-hidden">
                    {recipe.description || "Geen beschrijving beschikbaar."}
                </p>

                {/* Meta Info */}
                <div className="mt-auto pt-4 border-t border-white/5 flex items-center justify-between text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                        <Clock size={14} className="text-primary/70" />
                        <span>30m</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Users size={14} className="text-secondary/70" />
                        <span>{recipe.yield || "4 pers."}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Flame size={14} className="text-orange-500/70" />
                        <button
                            onClick={(e) => handleTagClick(e, 'method', recipe.methods[0])}
                            className="tag-button hover:text-primary transition-colors capitalize"
                        >
                            {recipe.methods[0] || "Bakken"}
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Home,
    Search,
    Grid,
    MessageSquare,
    Info,
    UtensilsCrossed,
    ChefHat
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

const navItems = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Recepten', href: '/recipes', icon: UtensilsCrossed },
    { name: 'Categorieën', href: '/categories', icon: Grid },
    { name: 'Ingrediënten', href: '/ingredients', icon: ChefHat },
    { name: 'Assistant', href: '/chat', icon: MessageSquare },
];

export const Sidebar = () => {
    const pathname = usePathname();

    return (
        <div className="fixed left-0 top-0 h-screen w-64 glass border-r border-white/5 p-6 flex flex-col z-50">
            {/* Logo */}
            <div className="flex items-center gap-3 mb-10 px-2">
                <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
                    <UtensilsCrossed className="text-white" size={24} />
                </div>
                <span className="text-xl font-bold tracking-tight text-white uppercase tracking-wider">
                    Spice<span className="text-primary">Route</span>
                </span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-2">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 group relative",
                                isActive
                                    ? "bg-primary/10 text-primary"
                                    : "text-slate-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            <Icon size={20} className={cn(
                                "transition-colors",
                                isActive ? "text-primary" : "group-hover:text-white"
                            )} />
                            <span className="font-medium">{item.name}</span>

                            {isActive && (
                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full" />
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Footer Info */}
            <div className="mt-auto pt-6 border-t border-white/5 px-2">
                <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
                    <Info size={14} />
                    <span>v2.0 Beta (Next.js)</span>
                </div>
                <p className="text-[10px] text-slate-600">
                    Ontdek de rijkdom van de wereldkeuken.
                </p>
            </div>
        </div>
    );
};

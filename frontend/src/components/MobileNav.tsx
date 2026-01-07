'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Menu,
    X,
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

export const MobileNav = () => {
    const [isOpen, setIsOpen] = useState(false);
    const pathname = usePathname();

    // Close menu when route changes
    useEffect(() => {
        setIsOpen(false);
    }, [pathname]);

    // Prevent body scroll when menu is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [isOpen]);

    return (
        <div className="md:hidden">
            {/* Hamburger Button */}
            <button
                onClick={() => setIsOpen(true)}
                className="fixed top-4 left-4 z-50 p-2 glass rounded-xl text-white shadow-lg shadow-black/20"
                aria-label="Open menu"
            >
                <Menu size={24} />
            </button>

            {/* Overlay & Drawer */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsOpen(false)}
                            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                        />

                        {/* Drawer */}
                        <motion.div
                            initial={{ x: '-100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '-100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed top-0 left-0 bottom-0 w-[80%] max-w-sm bg-surface border-r border-white/10 z-50 flex flex-col p-6 shadow-2xl"
                        >
                            {/* Header */}
                            <div className="flex items-center justify-between mb-8">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
                                        <UtensilsCrossed className="text-white" size={24} />
                                    </div>
                                    <span className="text-xl font-bold tracking-tight text-white uppercase tracking-wider">
                                        Spice<span className="text-primary">Route</span>
                                    </span>
                                </div>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="p-2 glass rounded-full text-slate-400 hover:text-white"
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            {/* Navigation */}
                            <nav className="flex-1 space-y-2 overflow-y-auto">
                                {navItems.map((item) => {
                                    const Icon = item.icon;
                                    const isActive = pathname === item.href;

                                    return (
                                        <Link
                                            key={item.name}
                                            href={item.href}
                                            className={cn(
                                                "flex items-center gap-4 px-4 py-4 rounded-xl transition-all duration-200 group relative",
                                                isActive
                                                    ? "bg-primary/10 text-primary"
                                                    : "text-slate-400 hover:text-white hover:bg-white/5"
                                            )}
                                        >
                                            <Icon size={24} className={cn(
                                                "transition-colors",
                                                isActive ? "text-primary" : "group-hover:text-white"
                                            )} />
                                            <span className="font-medium text-lg">{item.name}</span>

                                            {isActive && (
                                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full" />
                                            )}
                                        </Link>
                                    );
                                })}
                            </nav>

                            {/* Footer */}
                            <div className="mt-auto pt-6 border-t border-white/5">
                                <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
                                    <Info size={14} />
                                    <span>v2.0 Beta</span>
                                </div>
                                <p className="text-[10px] text-slate-600">
                                    Ontdek de rijkdom van de wereldkeuken.
                                </p>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Sparkles, Trash2, ArrowRight } from 'lucide-react';
import { sendChatMessage } from '@/lib/api';
import { v4 as uuidv4 } from 'uuid';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Initialize session ID
        let id = localStorage.getItem('chat_session_id');
        if (!id) {
            id = uuidv4();
            localStorage.setItem('chat_session_id', id);
        }
        setSessionId(id);

        // Welcome message
        setMessages([
            {
                id: 'welcome',
                text: 'Welkom bij de SpiceRoute Assistant! 🌍 Ik ben je culinaire gids voor wereldkeukens. Of je nu op zoek bent naar een pittige Thaise curry, een authentieke Indonesische rendang of kooktechnieken voor de Chinese keuken, ik help je graag verder. Waar gaan we vandaag naartoe?',
                sender: 'bot',
                timestamp: new Date()
            }
        ]);
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: uuidv4(),
            text: input,
            sender: 'user',
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        const currentInput = input;
        setInput('');
        setIsLoading(true);

        try {
            const res = await sendChatMessage(currentInput, sessionId);
            const botMessage: Message = {
                id: uuidv4(),
                text: res.response,
                sender: 'bot',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: uuidv4(),
                text: "Sorry, er ging iets mis bij het verwerken van je vraag. Probeer het later opnieuw.",
                sender: 'bot',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = () => {
        const newId = uuidv4();
        setSessionId(newId);
        localStorage.setItem('chat_session_id', newId);
        setMessages([
            {
                id: 'welcome-reset',
                text: 'Chat gereset. Hoe kan ik je opnieuw helpen?',
                sender: 'bot',
                timestamp: new Date()
            }
        ]);
    };

    return (
        <div className="flex flex-col h-[calc(100vh-120px)] max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-primary/20 flex items-center justify-center">
                        <Bot className="text-primary" size={28} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">AI Assistant</h1>
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                            <Sparkles size={12} className="text-primary" />
                            Aangedreven door GPT-4 & Neo4j
                        </p>
                    </div>
                </div>
                <button
                    onClick={clearChat}
                    className="p-2 glass text-slate-500 hover:text-red-400 transition-colors rounded-xl"
                    title="Clear chat"
                >
                    <Trash2 size={20} />
                </button>
            </div>

            {/* Chat Body */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto glass rounded-3xl p-6 space-y-6 scrollbar-hide"
            >
                <AnimatePresence initial={false}>
                    {messages.map((msg) => (
                        <motion.div
                            key={msg.id}
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div className={`flex gap-3 max-w-[80%] ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                                <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center ${msg.sender === 'user' ? 'bg-secondary/20 text-secondary' : 'bg-primary/20 text-primary'
                                    }`}>
                                    {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                                </div>
                                <div className={`p-4 rounded-2xl text-sm leading-relaxed ${msg.sender === 'user'
                                    ? 'bg-secondary text-white rounded-tr-none'
                                    : 'bg-white/10 text-slate-200 rounded-tl-none border border-white/5'
                                    }`}>
                                    {msg.text}
                                    <div className={`text-[10px] mt-2 opacity-50 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
                                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {isLoading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex justify-start"
                    >
                        <div className="flex gap-3 items-center bg-white/5 border border-white/5 p-4 rounded-2xl rounded-tl-none">
                            <div className="flex gap-1">
                                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                            <span className="text-xs text-slate-500 font-medium tracking-wide">Assistant denkt na...</span>
                        </div>
                    </motion.div>
                )}
            </div>

            {/* Suggestions */}
            {messages.length < 3 && !isLoading && (
                <div className="grid grid-cols-2 gap-3 mt-6">
                    {[
                        "Geef me 3 recepten uit Thailand",
                        "Wat heb ik nodig voor Rendang?",
                        "Vegetarische gerechten uit de Chinese keuken",
                        "Hoe maak ik een authentieke curry?"
                    ].map(suggest => (
                        <button
                            key={suggest}
                            onClick={() => { setInput(suggest); }}
                            className="text-left p-3 glass border border-white/5 rounded-xl text-xs text-slate-400 hover:text-white hover:border-primary/30 transition-all flex items-center justify-between group"
                        >
                            {suggest}
                            <ArrowRight size={14} className="opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                        </button>
                    ))}
                </div>
            )}

            {/* Input Area */}
            <form onSubmit={handleSend} className="relative mt-6">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Stel je culinaire vraag aan de SpiceRoute Assistant..."
                    className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 pr-16 text-white placeholder:text-slate-600 focus:outline-none focus:border-primary/50 transition-all shadow-xl"
                />
                <button
                    type="submit"
                    disabled={!input.trim() || isLoading}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-primary text-white rounded-xl disabled:opacity-30 hover:bg-orange-600 transition-all shadow-lg shadow-primary/20"
                >
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
}

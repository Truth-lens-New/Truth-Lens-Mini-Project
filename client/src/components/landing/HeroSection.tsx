import { motion, useTransform, AnimatePresence } from 'framer-motion';
import { ArrowRight, ChevronDown, Play, Globe, Layers, Zap, BarChart3 } from 'lucide-react';
import { useLandingScroll } from './LandingScrollContext';
import { useState } from 'react';
import type { Page } from '../../App';
import { HeroGlobe } from './HeroGlobe';
import { HeroGlobe3D } from './HeroGlobe3D';
import { HeroMorphingCards } from './HeroMorphingCards';
import { HeroLiveAnalysis } from './HeroLiveAnalysis';
import { HeroForensicsDash } from './HeroForensicsDash';

interface HeroSectionProps {
    onNavigate: (page: Page) => void;
}

const VARIANTS = [
    { id: 'globe3d', label: '3D Globe', icon: Globe, component: HeroGlobe3D },
    { id: 'globe', label: 'Globe', icon: Globe, component: HeroGlobe },
    { id: 'cards', label: 'Cards', icon: Layers, component: HeroMorphingCards },
    { id: 'live', label: 'Live', icon: Zap, component: HeroLiveAnalysis },
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3, component: HeroForensicsDash },
] as const;

export function HeroSection({ onNavigate }: HeroSectionProps) {
    const { scrollYProgress } = useLandingScroll();
    const [activeVariant, setActiveVariant] = useState(0);

    // Parallax effects based on scroll
    const y = useTransform(scrollYProgress, [0, 0.2], [0, 200]);
    const opacity = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
    const scale = useTransform(scrollYProgress, [0, 0.2], [1, 0.9]);

    const ActiveComponent = VARIANTS[activeVariant].component;

    return (
        <section className="relative h-screen min-h-[800px] flex items-center justify-center snap-start perspective-1000">
            {/* Background Ambience */}
            <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
                {/* Dark Mode */}
                <div className="hidden dark:block absolute inset-0 bg-background">
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/20 rounded-full blur-[120px] animate-pulse" />
                    <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-transparent via-background/80 to-background" />
                </div>

                {/* Light Mode */}
                <div className="dark:hidden absolute inset-0 bg-background">
                    <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] bg-gradient-to-br from-primary/5 to-transparent rounded-full blur-[100px]" />
                    <div className="absolute bottom-[-20%] left-[-10%] w-[600px] h-[600px] bg-gradient-to-tr from-accent/10 to-transparent rounded-full blur-[80px]" />
                </div>
            </div>

            {/* Main Content */}
            <motion.div
                style={{ y, opacity, scale }}
                className="relative z-10 w-full max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center"
            >
                {/* Text Side */}
                <div className="space-y-8 text-center lg:text-left pt-20 lg:pt-0">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                    >
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 backdrop-blur-md text-xs font-medium text-primary tracking-wide">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                            SYSTEM V3.0 ONLINE
                        </span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
                        className="text-6xl lg:text-8xl font-bold tracking-tighter leading-none"
                    >
                        Truth, <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-purple-500 to-indigo-600 dark:from-cyan-400 dark:via-blue-500 dark:to-purple-500">
                            Clarified.
                        </span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="text-xl text-muted-foreground max-w-xl mx-auto lg:mx-0 leading-relaxed"
                    >
                        The world's most advanced multi-modal forensic analysis engine.
                        Instantly detect manipulation in video, audio, and text with
                        <span className="text-foreground font-semibold"> 99.8% verified accuracy.</span>
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.3 }}
                        className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start"
                    >
                        <button
                            onClick={() => onNavigate('verify-media')}
                            className="group relative px-8 py-4 rounded-xl bg-foreground text-background font-semibold text-lg overflow-hidden transition-all hover:scale-105 active:scale-95"
                        >
                            <span className="relative z-10 flex items-center gap-2">
                                Start Analysis <ArrowRight className="w-4 h-4" />
                            </span>
                            <div className="absolute inset-0 bg-primary/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                        </button>

                        <button
                            onClick={() => {
                                const demo = document.getElementById('demo-section');
                                demo?.scrollIntoView({ behavior: 'smooth' });
                            }}
                            className="px-8 py-4 rounded-xl border border-border hover:bg-secondary/50 transition-all font-medium flex items-center gap-2 group"
                        >
                            <Play className="w-4 h-4 fill-current group-hover:text-primary transition-colors" />
                            Watch Demo
                        </button>
                    </motion.div>
                </div>

                {/* Visual Side */}
                <div className="relative h-[500px] lg:h-[700px] w-full flex flex-col items-center justify-center">
                    {/* Variant display area */}
                    <div className="flex-1 w-full relative">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={activeVariant}
                                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                                transition={{ duration: 0.4, ease: 'easeOut' }}
                                className="absolute inset-0"
                            >
                                <ActiveComponent />
                            </motion.div>
                        </AnimatePresence>
                    </div>

                    {/* Variant Switcher */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6, duration: 0.5 }}
                        className="relative z-30 flex items-center gap-1 p-1 rounded-full bg-card/80 backdrop-blur-xl border border-border shadow-lg"
                    >
                        {VARIANTS.map((variant, i) => {
                            const Icon = variant.icon;
                            const isActive = i === activeVariant;
                            return (
                                <button
                                    key={variant.id}
                                    onClick={() => setActiveVariant(i)}
                                    className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300 ${isActive
                                        ? 'text-primary-foreground'
                                        : 'text-muted-foreground hover:text-foreground'
                                        }`}
                                >
                                    {isActive && (
                                        <motion.div
                                            layoutId="hero-variant-pill"
                                            className="absolute inset-0 rounded-full bg-primary"
                                            transition={{ type: 'spring', bounce: 0.2, duration: 0.5 }}
                                        />
                                    )}
                                    <Icon className="w-3.5 h-3.5 relative z-10" />
                                    <span className="relative z-10 hidden sm:inline">{variant.label}</span>
                                </button>
                            );
                        })}
                    </motion.div>
                </div>
            </motion.div>

            {/* Scroll Indicator */}
            <motion.div
                style={{ opacity: useTransform(scrollYProgress, [0, 0.05], [1, 0]) }}
                className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-muted-foreground"
            >
                <span className="text-secondary-foreground text-xs uppercase tracking-widest">Initialise</span>
                <ChevronDown className="w-5 h-5 animate-bounce" />
            </motion.div>
        </section>
    );
}

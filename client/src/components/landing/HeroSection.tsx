import { motion, useTransform } from 'framer-motion';
import { ArrowRight, ChevronDown, Play } from 'lucide-react';
import { useLandingScroll } from './LandingScrollContext';
import type { Page } from '../../App';

interface HeroSectionProps {
    onNavigate: (page: Page) => void;
}

export function HeroSection({ onNavigate }: HeroSectionProps) {
    const { scrollYProgress } = useLandingScroll();

    // Parallax effects based on scroll
    const y = useTransform(scrollYProgress, [0, 0.2], [0, 200]);
    const opacity = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
    const scale = useTransform(scrollYProgress, [0, 0.2], [1, 0.9]);

    return (
        <section className="relative h-screen min-h-[800px] flex items-center justify-center snap-start perspective-1000">
            {/* Background Ambience */}
            <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
                {/* Dark Mode: Supermemory "Void" */}
                <div className="hidden dark:block absolute inset-0 bg-background">
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/20 rounded-full blur-[120px] animate-pulse" />
                    <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-transparent via-background/80 to-background" />
                </div>

                {/* Light Mode: Antigravity "Structure" */}
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

                {/* Visual Side - "Artifact" */}
                <div className="relative h-[400px] lg:h-[600px] w-full flex items-center justify-center perspective-[2000px]">
                    {/* Central Cube / Sphere */}
                    <motion.div
                        animate={{
                            rotateY: [0, 360],
                            rotateX: [0, 360, 0],
                        }}
                        transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
                        className="relative w-72 h-72 preserve-3d"
                        style={{ transformStyle: 'preserve-3d' }}
                    >
                        {/* Faces of a "Glass Layout" - More delicate borders */}
                        <div className="absolute inset-0 border border-primary/20 bg-primary/5 backdrop-blur-xl rounded-[2rem] shadow-[0_0_30px_-5px_var(--primary)]"
                            style={{ transform: 'translateZ(100px)' }}></div>
                        <div className="absolute inset-0 border border-accent/20 bg-accent/5 backdrop-blur-xl rounded-[2rem]"
                            style={{ transform: 'rotateY(90deg) translateZ(100px)' }}></div>
                        <div className="absolute inset-0 border border-white/10 dark:border-white/5 bg-white/5 backdrop-blur-md rounded-[2rem]"
                            style={{ transform: 'rotateX(90deg) translateZ(100px)' }}></div>

                        {/* Inner Core */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-gradient-to-tr from-primary/30 to-accent/30 rounded-full blur-[50px] animate-pulse"></div>
                    </motion.div>

                    {/* Floating Orbitals - Thinner, more elegant */}
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
                        className="absolute w-[550px] h-[550px] border border-dashed border-primary/10 rounded-full pointer-events-none"
                    />
                    <motion.div
                        animate={{ rotate: -360 }}
                        transition={{ duration: 35, repeat: Infinity, ease: "linear" }}
                        className="absolute w-[450px] h-[450px] border border-dashed border-accent/10 rounded-full pointer-events-none"
                    />
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

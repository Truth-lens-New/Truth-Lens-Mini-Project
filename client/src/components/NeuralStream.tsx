import { motion, AnimatePresence } from 'framer-motion';
import { useMemo } from 'react';
import { Brain, Search, Database, Shield, Zap, Globe } from 'lucide-react';

interface NeuralStreamProps {
    currentStep?: string;
    isActive?: boolean;
}

const STEP_METADATA: Record<string, { label: string; color: string; icon: any }> = {
    idle: { label: 'Awaiting Input', color: '#6366f1', icon: Brain },
    extracting: { label: 'Extracting Claims', color: '#818cf8', icon: Search },
    checking_misinfo: { label: 'Querying Records', color: '#3b82f6', icon: Database },
    checking_wikidata: { label: 'Fact Checking', color: '#2dd4bf', icon: Globe },
    searching_web: { label: 'Deep Investigation', color: '#fbbf24', icon: Zap },
    analyzing_stance: { label: 'Synthesizing Consensus', color: '#f472b6', icon: Brain },
    synthesizing: { label: 'Finalizing Verdict', color: '#10b981', icon: Shield },
    error: { label: 'System Halted', color: '#ef4444', icon: Zap },
};

export function NeuralStream({ currentStep = 'idle' }: NeuralStreamProps) {
    const meta = STEP_METADATA[currentStep] || STEP_METADATA.idle;

    // Generate static particles for the background synapsis
    const particles = useMemo(() => {
        return Array.from({ length: 15 }).map((_, i) => ({
            id: i,
            x: Math.random() * 100,
            y: Math.random() * 100,
            size: Math.random() * 4 + 2,
            delay: Math.random() * 2,
            duration: Math.random() * 3 + 2,
        }));
    }, []);

    return (
        <div className="w-full flex flex-col items-center justify-center py-12 px-4">
            <div className="relative w-80 h-80 flex items-center justify-center">
                {/* SVG Filter for Gooey effect */}
                <svg className="absolute w-0 h-0">
                    <defs>
                        <filter id="goo">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="15" result="blur" />
                            <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7" result="goo" />
                            <feBlend in="SourceGraphic" in2="goo" />
                        </filter>
                    </defs>
                </svg>

                {/* Background Synapse Network */}
                <div className="absolute inset-0 opacity-30">
                    {particles.map((p) => (
                        <motion.div
                            key={p.id}
                            className="absolute rounded-full"
                            style={{
                                left: `${p.x}%`,
                                top: `${p.y}%`,
                                width: p.size,
                                height: p.size,
                                backgroundColor: meta.color,
                                filter: 'blur(1px)',
                            }}
                            animate={{
                                opacity: [0.2, 0.6, 0.2],
                                scale: [1, 1.5, 1],
                                x: [0, Math.random() * 20 - 10, 0],
                                y: [0, Math.random() * 20 - 10, 0],
                            }}
                            transition={{
                                duration: p.duration,
                                repeat: Infinity,
                                delay: p.delay,
                                ease: "easeInOut"
                            }}
                        />
                    ))}
                </div>

                {/* The Synapse Nucleus (Fluid Orb) */}
                <div style={{ filter: 'url(#goo)' }} className="relative flex items-center justify-center">
                    <motion.div
                        className="w-48 h-48 rounded-full relative z-10"
                        style={{ background: `radial-gradient(circle at 30% 30%, ${meta.color}, #000)` }}
                        animate={{
                            scale: [1, 1.05, 1],
                            borderRadius: [
                                "42% 58% 70% 30% / 45% 45% 55% 55%",
                                "58% 42% 38% 62% / 45% 55% 45% 55%",
                                "45% 55% 40% 60% / 65% 35% 65% 35%",
                                "42% 58% 70% 30% / 45% 45% 55% 55%"
                            ]
                        }}
                        transition={{
                            duration: 8,
                            repeat: Infinity,
                            ease: "easeInOut"
                        }}
                    >
                        {/* Glow effect inside nucleus */}
                        <motion.div
                            className="absolute inset-0 rounded-full opacity-50 blur-2xl"
                            style={{ backgroundColor: meta.color }}
                            animate={{ opacity: [0.3, 0.6, 0.3] }}
                            transition={{ duration: 2, repeat: Infinity }}
                        />
                    </motion.div>

                    {/* Orbiting Satellite Particles (Evidence) */}
                    <AnimatePresence>
                        {currentStep !== 'idle' && Array.from({ length: 4 }).map((_, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, scale: 0 }}
                                exit={{ opacity: 0, scale: 0 }}
                                className="absolute w-4 h-4 rounded-full z-20"
                                style={{
                                    backgroundColor: meta.color,
                                    boxShadow: `0 0 15px ${meta.color}`
                                }}
                                animate={{
                                    opacity: 1,
                                    scale: 1,
                                    x: [
                                        Math.cos((i * 90 * Math.PI) / 180) * 120,
                                        Math.cos(((i * 90 + 180) * Math.PI) / 180) * 120,
                                        Math.cos(((i * 90 + 360) * Math.PI) / 180) * 120
                                    ],
                                    y: [
                                        Math.sin((i * 90 * Math.PI) / 180) * 120,
                                        Math.sin(((i * 90 + 180) * Math.PI) / 180) * 120,
                                        Math.sin(((i * 90 + 360) * Math.PI) / 180) * 120
                                    ],
                                }}
                                transition={{
                                    duration: 6 + i,
                                    repeat: Infinity,
                                    ease: "linear"
                                }}
                            />
                        ))}
                    </AnimatePresence>
                </div>

                {/* Central Icon */}
                <div className="absolute z-30 flex flex-col items-center">
                    <motion.div
                        key={currentStep}
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="p-4 rounded-full bg-white/10 backdrop-blur-md border border-white/20 shadow-2xl"
                    >
                        <meta.icon className="w-10 h-10 text-white" />
                    </motion.div>
                </div>
            </div>

            {/* Thought Label */}
            <div className="mt-8 text-center space-y-2">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentStep}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="flex flex-col items-center"
                    >
                        <span className="text-2xl font-bold tracking-tight text-foreground">
                            {meta.label}
                        </span>
                        <div className="flex items-center gap-2 mt-2">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ backgroundColor: meta.color }}></span>
                                <span className="relative inline-flex rounded-full h-2 w-2" style={{ backgroundColor: meta.color }}></span>
                            </span>
                            <span className="text-sm font-medium text-muted-foreground uppercase tracking-[0.2em]">
                                Investigation in Progress
                            </span>
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>
        </div>
    );
}

import { motion, AnimatePresence } from 'framer-motion';
import { useMemo, useState, useEffect } from 'react';
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

const THOUGHT_STREAMS: Record<string, string[]> = {
    extracting: [
        "Parsing text structure...",
        "Identifying core arguments...",
        "Filtering noise...",
        "Isolating factual claims..."
    ],
    checking_misinfo: [
        "Checking known misinformation databases...",
        "Querying verified fact-checks...",
        "Matching against debunked narratives..."
    ],
    checking_wikidata: [
        "Querying Knowledge Graph...",
        "Verifying entity relationships...",
        "Cross-referencing historical dates..."
    ],
    searching_web: [
        "Scanning trusted news sources...",
        "Accessing academic journals...",
        "Filtering clickbait...",
        "Reading 20+ source documents...",
        "Searching PubMed for scientific consensus..."
    ],
    analyzing_stance: [
        "Reading source content...",
        "Detecting bias in sources...",
        "Comparing conflicting reports...",
        "Weighing evidence credibility...",
        "Identifying primary sources..."
    ],
    synthesizing: [
        "Synthesizing final verdict...",
        "Generating summary...",
        "Calculating confidence score..."
    ]
};

export function NeuralStream({ currentStep = 'idle' }: NeuralStreamProps) {
    const meta = STEP_METADATA[currentStep] || STEP_METADATA.idle;
    const [thought, setThought] = useState("");

    // Cycle Thoughts
    useEffect(() => {
        if (currentStep === 'idle' || currentStep === 'complete' || currentStep === 'error') {
            setThought("");
            return;
        }

        const thoughts = THOUGHT_STREAMS[currentStep] || [];
        setThought(thoughts[0] || "");
        let index = 0;

        const interval = setInterval(() => {
            index = (index + 1) % thoughts.length;
            setThought(thoughts[index]);
        }, 2500);

        return () => clearInterval(interval);
    }, [currentStep]);

    // Progress Zeno
    const [progress, setProgress] = useState(0);
    useEffect(() => {
        if (currentStep === 'idle') {
            setProgress(0); return;
        }
        let target = 0;
        switch (currentStep) {
            case 'extracting': target = 15; break;
            case 'checking_misinfo': target = 30; break;
            case 'checking_wikidata': target = 45; break;
            case 'searching_web': target = 70; break;
            case 'analyzing_stance': target = 85; break;
            case 'synthesizing': target = 95; break;
            case 'complete': target = 100; break;
        }
        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev >= target) return prev;
                const diff = target - prev;
                const increment = Math.max(0.1, diff * 0.1);
                return Math.min(target, prev + increment);
            });
        }, 50);
        return () => clearInterval(interval);
    }, [currentStep]);

    // Particles
    const particles = useMemo(() => Array.from({ length: 15 }).map((_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 4 + 2,
        delay: Math.random() * 2,
        duration: Math.random() * 3 + 2,
    })), []);

    return (
        <div className="w-full h-full flex flex-col items-center justify-center py-6 px-4 relative overflow-hidden">

            <div className="relative w-96 h-96 flex items-center justify-center z-10 shrink-0">
                {/* SVG Ring */}
                <svg className="absolute w-[400px] h-[400px] -rotate-90 pointer-events-none">
                    <circle cx="200" cy="200" r="190" className="stroke-muted/10" strokeWidth="2" fill="transparent" />
                    <motion.circle
                        cx="200" cy="200" r="190"
                        stroke={meta.color} strokeWidth="4" fill="transparent" strokeLinecap="round"
                        strokeDasharray="1194"
                        animate={{ strokeDashoffset: 1194 - (1194 * progress / 100) }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                        style={{ filter: `drop-shadow(0 0 15px ${meta.color})` }}
                    />
                </svg>

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

                <div className="absolute inset-0 opacity-30">
                    {particles.map((p) => (
                        <motion.div
                            key={p.id}
                            className="absolute rounded-full"
                            style={{
                                left: `${p.x}%`, top: `${p.y}%`, width: p.size, height: p.size,
                                backgroundColor: meta.color, filter: 'blur(1px)',
                            }}
                            animate={{
                                opacity: [0.2, 0.6, 0.2], scale: [1, 1.5, 1],
                                x: [0, Math.random() * 20 - 10, 0], y: [0, Math.random() * 20 - 10, 0],
                            }}
                            transition={{ duration: p.duration, repeat: Infinity, delay: p.delay, ease: "easeInOut" }}
                        />
                    ))}
                </div>

                <div style={{ filter: 'url(#goo)' }} className="relative flex items-center justify-center">
                    <motion.div
                        className="w-48 h-48 rounded-full relative z-10"
                        style={{ background: `radial-gradient(circle at 30% 30%, ${meta.color}, #000)` }}
                        animate={{
                            scale: [1, 1.05, 1],
                            borderRadius: ["42% 58% 70% 30% / 45% 45% 55% 55%", "58% 42% 38% 62% / 45% 55% 45% 55%", "45% 55% 40% 60% / 65% 35% 65% 35%", "42% 58% 70% 30% / 45% 45% 55% 55%"]
                        }}
                        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                    >
                        <motion.div className="absolute inset-0 rounded-full opacity-50 blur-2xl" style={{ backgroundColor: meta.color }} animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 2, repeat: Infinity }} />
                    </motion.div>
                </div>

                <div className="absolute z-30 flex flex-col items-center">
                    <motion.div
                        key={currentStep}
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="p-5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 shadow-2xl"
                    >
                        <meta.icon className="w-12 h-12 text-white" />
                    </motion.div>
                </div>
            </div>

            <div className="mt-4 text-center space-y-3 relative z-10 w-full max-w-2xl shrink-0">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentStep}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="flex flex-col items-center"
                    >
                        {/* Percentage Display */}
                        <div
                            className="text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-gray-900 to-gray-500 dark:from-white dark:to-white/50 mb-1"
                            style={{ textShadow: `0 0 30px ${meta.color}40` }}
                        >
                            {Math.round(progress)}%
                        </div>

                        <span className="text-sm font-bold tracking-[0.3em] uppercase mb-4" style={{ color: meta.color }}>
                            {meta.label}
                        </span>

                        {/* Elegant Dynamic Thought Stream */}
                        <div className="h-10 flex items-center justify-center w-full">
                            <AnimatePresence mode="wait">
                                {thought && (
                                    <motion.p
                                        initial={{ opacity: 0, y: 5, filter: "blur(4px)" }}
                                        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                                        exit={{ opacity: 0, y: -5, filter: "blur(4px)" }}
                                        key={thought}
                                        className="text-2xl md:text-3xl font-serif text-gray-800 dark:text-white/90 italic text-center leading-relaxed"
                                    >
                                        {thought}
                                    </motion.p>
                                )}
                            </AnimatePresence>
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>
        </div>
    );
}

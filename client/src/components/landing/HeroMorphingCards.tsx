import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Newspaper, Twitter, Video } from 'lucide-react';

interface MediaCard {
    type: 'news' | 'tweet' | 'video';
    title: string;
    source: string;
    verdict: 'verified' | 'fake' | 'uncertain';
    confidence: number;
}

const CARDS: MediaCard[] = [
    {
        type: 'news',
        title: '"New study confirms breakthrough in quantum computing reliability"',
        source: 'Science Daily',
        verdict: 'verified',
        confidence: 94,
    },
    {
        type: 'tweet',
        title: '"BREAKING: Major city confirms mandatory evacuation order for all residents"',
        source: '@breaking_alerts',
        verdict: 'fake',
        confidence: 87,
    },
    {
        type: 'video',
        title: '"World leader caught making shocking statement on live TV"',
        source: 'Viral Video',
        verdict: 'fake',
        confidence: 91,
    },
    {
        type: 'news',
        title: '"Global temperatures reach record high for 3rd consecutive month"',
        source: 'Reuters',
        verdict: 'verified',
        confidence: 98,
    },
    {
        type: 'tweet',
        title: '"Scientists discover high levels of microplastics in popular bottled water brands"',
        source: '@healthwatch',
        verdict: 'uncertain',
        confidence: 62,
    },
];

const verdictConfig = {
    verified: { icon: CheckCircle, label: 'VERIFIED', color: 'text-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
    fake: { icon: XCircle, label: 'FAKE', color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/30' },
    uncertain: { icon: AlertTriangle, label: 'UNCERTAIN', color: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
};

const typeIcons = { news: Newspaper, tweet: Twitter, video: Video };

export function HeroMorphingCards() {
    const [activeIndex, setActiveIndex] = useState(0);
    const [showVerdict, setShowVerdict] = useState(false);

    useEffect(() => {
        const cycle = () => {
            setShowVerdict(false);
            // Show card for 1.5s, then reveal verdict
            setTimeout(() => setShowVerdict(true), 1500);
            // Move to next card after 3.5s total
            setTimeout(() => {
                setActiveIndex(prev => (prev + 1) % CARDS.length);
            }, 3800);
        };

        cycle();
        const interval = setInterval(cycle, 4000);
        return () => clearInterval(interval);
    }, []);

    const card = CARDS[activeIndex];
    const vConfig = verdictConfig[card.verdict];
    const VerdictIcon = vConfig.icon;
    const TypeIcon = typeIcons[card.type];

    return (
        <div className="relative w-full h-full flex items-center justify-center">
            {/* Background stacked cards (behind) */}
            {[2, 1].map(offset => {
                const idx = (activeIndex + offset) % CARDS.length;

                return (
                    <motion.div
                        key={`stack-${offset}-${idx}`}
                        className="absolute w-[420px] rounded-2xl border border-border bg-card/60 backdrop-blur-sm p-6"
                        style={{
                            transform: `translateY(${offset * 18}px) translateX(${offset * 10}px) scale(${1 - offset * 0.05})`,
                            zIndex: 10 - offset,
                            opacity: 1 - offset * 0.3,
                        }}
                    >
                        <div className="h-24" />
                    </motion.div>
                );
            })}

            {/* Active card (front) */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={activeIndex}
                    initial={{ opacity: 0, y: 30, rotateX: -10 }}
                    animate={{ opacity: 1, y: 0, rotateX: 0 }}
                    exit={{ opacity: 0, y: -20, scale: 0.95 }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                    className="absolute w-[420px] z-20 rounded-2xl border border-border bg-card shadow-2xl shadow-black/10 dark:shadow-black/30 overflow-hidden"
                >
                    {/* Card Header */}
                    <div className="p-5 space-y-3">
                        <div className="flex items-center gap-2 text-muted-foreground">
                            <TypeIcon className="w-4 h-4" />
                            <span className="text-xs font-medium uppercase tracking-wider">{card.type}</span>
                            <span className="text-xs opacity-50">•</span>
                            <span className="text-xs">{card.source}</span>
                        </div>
                        <p className="text-sm font-medium text-foreground leading-relaxed">{card.title}</p>

                        {/* Scanning animation */}
                        <AnimatePresence>
                            {!showVerdict && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="space-y-2 pt-2"
                                >
                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                        <motion.div
                                            animate={{ rotate: 360 }}
                                            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                            className="w-3 h-3 border-2 border-primary/30 border-t-primary rounded-full"
                                        />
                                        Analyzing claim...
                                    </div>
                                    <div className="w-full h-1 bg-secondary rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: '0%' }}
                                            animate={{ width: '100%' }}
                                            transition={{ duration: 1.4, ease: 'easeInOut' }}
                                            className="h-full bg-primary rounded-full"
                                        />
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Verdict reveal */}
                    <AnimatePresence>
                        {showVerdict && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.4, ease: 'easeOut' }}
                                className={`border-t ${vConfig.border} ${vConfig.bg}`}
                            >
                                <div className="p-4 flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <VerdictIcon className={`w-5 h-5 ${vConfig.color}`} />
                                        <span className={`text-sm font-bold ${vConfig.color}`}>{vConfig.label}</span>
                                    </div>
                                    <div className="text-right">
                                        <div className={`text-lg font-bold ${vConfig.color}`}>{card.confidence}%</div>
                                        <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Confidence</div>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>
            </AnimatePresence>

            {/* Progress dots */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5">
                {CARDS.map((_, i) => (
                    <div
                        key={i}
                        className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${i === activeIndex ? 'bg-primary w-4' : 'bg-muted-foreground/30'
                            }`}
                    />
                ))}
            </div>
        </div>
    );
}

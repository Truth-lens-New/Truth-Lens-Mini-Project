import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import { Search, Shield, CheckCircle, XCircle, Globe, FileText, ExternalLink } from 'lucide-react';

const HEADLINES = [
    { url: 'bbc.com/news/climate-record-temps-2026', verdict: 'verified' as const, confidence: 96, label: 'Climate record temperatures confirmed by NASA, NOAA' },
    { url: 'twitter.com/viral_post/status/182736', verdict: 'fake' as const, confidence: 89, label: 'Celebrity death hoax spreads on social media' },
    { url: 'reuters.com/tech/ai-regulation-bill', verdict: 'verified' as const, confidence: 93, label: 'EU passes comprehensive AI regulation framework' },
    { url: 'facebook.com/shared_post/991827', verdict: 'fake' as const, confidence: 95, label: '5G towers linked to health issues claim debunked' },
];

const SOURCES = [
    'Reuters', 'AP News', 'Wikipedia', 'Google Scholar', 'PubMed', 'Snopes', 'PolitiFact'
];

export function HeroLiveAnalysis() {
    const [phase, setPhase] = useState<'typing' | 'scanning' | 'result'>('typing');
    const [headlineIndex, setHeadlineIndex] = useState(0);
    const [typedChars, setTypedChars] = useState(0);
    const [scanProgress, setScanProgress] = useState(0);
    const [activeSource, setActiveSource] = useState(0);


    const headline = HEADLINES[headlineIndex];

    useEffect(() => {
        // Full cycle: type → scan → result → next
        const runCycle = () => {
            // Reset
            setPhase('typing');
            setTypedChars(0);
            setScanProgress(0);

            // Typing phase
            const url = HEADLINES[headlineIndex].url;
            let charIdx = 0;
            const typeInterval = setInterval(() => {
                charIdx++;
                setTypedChars(charIdx);
                if (charIdx >= url.length) {
                    clearInterval(typeInterval);
                    // Start scanning after short pause
                    setTimeout(() => {
                        setPhase('scanning');
                        let progress = 0;
                        let srcIdx = 0;
                        const scanInterval = setInterval(() => {
                            progress += 2;
                            setScanProgress(progress);
                            if (progress % 15 === 0) {
                                srcIdx = (srcIdx + 1) % SOURCES.length;
                                setActiveSource(srcIdx);
                            }
                            if (progress >= 100) {
                                clearInterval(scanInterval);
                                setTimeout(() => setPhase('result'), 300);
                            }
                        }, 40);
                    }, 400);
                }
            }, 45);

            return typeInterval;
        };

        const typeInt = runCycle();

        // Move to next headline every 6s
        const cycleInterval = setInterval(() => {
            setHeadlineIndex(prev => (prev + 1) % HEADLINES.length);
        }, 6500);

        return () => {
            clearInterval(typeInt);
            clearInterval(cycleInterval);
        };
    }, [headlineIndex]);

    const isVerified = headline.verdict === 'verified';

    return (
        <div className="relative w-full h-full flex items-center justify-center px-2">
            <div className="w-full max-w-[500px] rounded-2xl border border-border bg-card shadow-2xl shadow-black/10 dark:shadow-black/40 overflow-hidden">
                {/* Browser Chrome */}
                <div className="flex items-center gap-2 px-4 py-2.5 bg-secondary/50 border-b border-border">
                    <div className="flex gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-400/70" />
                        <div className="w-2.5 h-2.5 rounded-full bg-amber-400/70" />
                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-400/70" />
                    </div>
                    <div className="flex-1 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-background border border-border text-xs font-mono">
                        <Search className="w-3 h-3 text-muted-foreground shrink-0" />
                        <span className="text-muted-foreground truncate">
                            {headline.url.slice(0, typedChars)}
                            {phase === 'typing' && (
                                <motion.span
                                    animate={{ opacity: [1, 0] }}
                                    transition={{ duration: 0.5, repeat: Infinity }}
                                    className="inline-block w-[1px] h-3.5 bg-primary ml-0.5 align-middle"
                                />
                            )}
                        </span>
                    </div>
                    <ExternalLink className="w-3 h-3 text-muted-foreground" />
                </div>

                {/* Content Area */}
                <div className="p-4 space-y-3 min-h-[200px]">
                    {/* Article title */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: phase !== 'typing' ? 1 : 0.3 }}
                        className="space-y-1"
                    >
                        <div className="flex items-center gap-1.5 text-muted-foreground">
                            <Globe className="w-3 h-3" />
                            <span className="text-[10px] uppercase tracking-wider font-medium">Claim Detected</span>
                        </div>
                        <p className="text-xs text-foreground/80 leading-relaxed">{headline.label}</p>
                    </motion.div>

                    {/* Scanning phase */}
                    <AnimatePresence mode="wait">
                        {phase === 'scanning' && (
                            <motion.div
                                key="scanning"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -5 }}
                                className="space-y-2.5 pt-1"
                            >
                                <div className="flex items-center justify-between text-[10px]">
                                    <span className="text-muted-foreground flex items-center gap-1.5">
                                        <motion.div
                                            animate={{ rotate: 360 }}
                                            transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                                            className="w-3 h-3 border-[1.5px] border-primary/30 border-t-primary rounded-full"
                                        />
                                        Cross-referencing sources...
                                    </span>
                                    <span className="text-primary font-mono font-bold">{scanProgress}%</span>
                                </div>
                                <div className="w-full h-1 bg-secondary rounded-full overflow-hidden">
                                    <motion.div
                                        className="h-full bg-primary rounded-full"
                                        style={{ width: `${scanProgress}%` }}
                                    />
                                </div>
                                <div className="flex flex-wrap gap-1.5">
                                    {SOURCES.map((src, i) => (
                                        <motion.span
                                            key={src}
                                            initial={{ opacity: 0.3 }}
                                            animate={{ opacity: i <= activeSource ? 1 : 0.3 }}
                                            className={`text-[9px] px-2 py-0.5 rounded-full border ${i <= activeSource
                                                ? 'border-primary/30 bg-primary/10 text-primary'
                                                : 'border-border text-muted-foreground'
                                                }`}
                                        >
                                            {src} {i < activeSource ? '✓' : ''}
                                        </motion.span>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {/* Result phase */}
                        {phase === 'result' && (
                            <motion.div
                                key="result"
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="space-y-3 pt-1"
                            >
                                {/* Verdict */}
                                <div className={`flex items-center justify-between p-3 rounded-xl border ${isVerified
                                    ? 'bg-emerald-500/10 border-emerald-500/30'
                                    : 'bg-red-500/10 border-red-500/30'
                                    }`}>
                                    <div className="flex items-center gap-2">
                                        {isVerified
                                            ? <CheckCircle className="w-5 h-5 text-emerald-500" />
                                            : <XCircle className="w-5 h-5 text-red-500" />
                                        }
                                        <div>
                                            <div className={`text-sm font-bold ${isVerified ? 'text-emerald-500' : 'text-red-500'}`}>
                                                {isVerified ? 'VERIFIED' : 'FAKE'}
                                            </div>
                                            <div className="text-[10px] text-muted-foreground">
                                                {headline.confidence}% confidence
                                            </div>
                                        </div>
                                    </div>
                                    <Shield className={`w-6 h-6 ${isVerified ? 'text-emerald-500/50' : 'text-red-500/50'}`} />
                                </div>

                                {/* Sources count */}
                                <div className="flex items-center justify-between text-[10px] text-muted-foreground px-1">
                                    <span className="flex items-center gap-1">
                                        <FileText className="w-3 h-3" />
                                        {SOURCES.length} sources verified
                                    </span>
                                    <span>Analysis complete in 2.1s</span>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}

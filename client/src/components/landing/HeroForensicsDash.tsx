import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { Activity, Shield, Eye, Zap, Database, Wifi } from 'lucide-react';

const SCANNING_HEADLINES = [
    'BBC News: New climate agreement reached at summit...',
    'CNN: Tech giant announces layoffs affecting 10,000...',
    'AP: Study reveals new data on vaccine effectiveness...',
    'Reuters: Central bank signals rate hike amid inflation...',
    'Fox: Border security bill passes in senate vote...',
    'Al Jazeera: Ceasefire negotiations stall once again...',
    'NYT: AI regulation bill moves through committee...',
    'Guardian: Record floods displace thousands in region...',
];

function useAnimatedNumber(target: number, duration = 2000) {
    const [value, setValue] = useState(0);
    useEffect(() => {
        const start = Date.now();
        const from = value;
        const tick = () => {
            const elapsed = Date.now() - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            setValue(Math.round(from + (target - from) * eased));
            if (progress < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    }, [target]);
    return value;
}

function MiniGauge({ value, label, color }: { value: number; label: string; color: string }) {
    const circumference = 2 * Math.PI * 18;
    const offset = circumference - (value / 100) * circumference;

    return (
        <div className="flex flex-col items-center gap-1">
            <svg width="48" height="48" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="18" fill="none" stroke="currentColor" className="text-border" strokeWidth="2.5" />
                <motion.circle
                    cx="24" cy="24" r="18" fill="none" stroke={color} strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset: offset }}
                    transition={{ duration: 1.5, ease: 'easeOut' }}
                    transform="rotate(-90 24 24)"
                />
                <text x="24" y="27" textAnchor="middle" className="fill-foreground" fontSize="11" fontWeight="bold">
                    {value}
                </text>
            </svg>
            <span className="text-[9px] text-muted-foreground uppercase tracking-wider">{label}</span>
        </div>
    );
}

export function HeroForensicsDash() {
    const [scanIdx, setScanIdx] = useState(0);
    const [isDark, setIsDark] = useState(false);

    useEffect(() => {
        const check = () => setIsDark(document.documentElement.classList.contains('dark'));
        check();
        const observer = new MutationObserver(check);
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        const interval = setInterval(() => {
            setScanIdx(prev => (prev + 1) % SCANNING_HEADLINES.length);
        }, 2000);
        return () => clearInterval(interval);
    }, []);

    const threatCount = useAnimatedNumber(847, 3000);
    const claimsCount = useAnimatedNumber(12453, 3000);
    const accuracyVal = useAnimatedNumber(99, 2000);

    return (
        <div className="relative w-full h-full flex items-center justify-center px-2">
            {/* Main dashboard card */}
            <div className="w-full max-w-[500px] rounded-2xl border border-border bg-card/90 backdrop-blur-xl shadow-2xl shadow-black/10 dark:shadow-black/40 overflow-hidden">

                {/* Top bar */}
                <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-secondary/30">
                    <div className="flex items-center gap-2">
                        <Shield className="w-3.5 h-3.5 text-primary" />
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-foreground">TruthLens Forensics</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[9px] text-emerald-500 font-medium">LIVE</span>
                    </div>
                </div>

                {/* Stats row */}
                <div className="grid grid-cols-3 gap-0 border-b border-border">
                    {[
                        { icon: Eye, label: 'Claims Analyzed', value: claimsCount.toLocaleString(), color: 'text-primary' },
                        { icon: Zap, label: 'Threats Found', value: threatCount.toLocaleString(), color: 'text-red-500' },
                        { icon: Activity, label: 'Accuracy', value: `${accuracyVal}.8%`, color: 'text-emerald-500' },
                    ].map((stat, i) => (
                        <div key={i} className={`p-3 text-center ${i < 2 ? 'border-r border-border' : ''}`}>
                            <stat.icon className={`w-3.5 h-3.5 mx-auto mb-1 ${stat.color}`} />
                            <div className={`text-base font-bold font-mono ${stat.color}`}>{stat.value}</div>
                            <div className="text-[8px] text-muted-foreground uppercase tracking-wider">{stat.label}</div>
                        </div>
                    ))}
                </div>

                {/* Gauges */}
                <div className="flex items-center justify-around py-3 px-4 border-b border-border">
                    <MiniGauge value={94} label="Trust" color={isDark ? '#22d3ee' : '#7c3aed'} />
                    <MiniGauge value={87} label="Sources" color={isDark ? '#34d399' : '#4f46e5'} />
                    <MiniGauge value={76} label="Consensus" color="#f59e0b" />
                    <MiniGauge value={99} label="Integrity" color="#10b981" />
                </div>

                {/* Live scanning ticker */}
                <div className="p-3 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground uppercase tracking-wider mb-2">
                        <Database className="w-3 h-3" />
                        Live Feed Scanner
                    </div>
                    <div className="space-y-1 max-h-[80px] overflow-hidden">
                        {[0, 1, 2].map(offset => {
                            const idx = (scanIdx + offset) % SCANNING_HEADLINES.length;
                            const isFirst = offset === 0;
                            return (
                                <motion.div
                                    key={`${scanIdx}-${offset}`}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: isFirst ? 1 : 0.4 - offset * 0.1, x: 0 }}
                                    transition={{ duration: 0.3 }}
                                    className="flex items-center gap-2 text-[10px]"
                                >
                                    {isFirst ? (
                                        <motion.div
                                            animate={{ rotate: 360 }}
                                            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                            className="w-2.5 h-2.5 border border-primary/40 border-t-primary rounded-full shrink-0"
                                        />
                                    ) : (
                                        <span className="w-2.5 h-2.5 flex items-center justify-center text-emerald-500 shrink-0">✓</span>
                                    )}
                                    <span className={`truncate ${isFirst ? 'text-foreground' : 'text-muted-foreground'}`}>
                                        {SCANNING_HEADLINES[idx]}
                                    </span>
                                </motion.div>
                            );
                        })}
                    </div>
                </div>

                {/* Bottom wave / scan line */}
                <div className="relative h-8 overflow-hidden border-t border-border bg-secondary/20">
                    <motion.div
                        animate={{ x: ['-100%', '200%'] }}
                        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                        className="absolute top-0 left-0 w-1/3 h-full bg-gradient-to-r from-transparent via-primary/20 to-transparent"
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="flex items-center gap-1.5 text-[9px] text-muted-foreground">
                            <Wifi className="w-3 h-3 text-primary" />
                            <span>Connected to 7 verification networks</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    CheckCircle2, XCircle, AlertTriangle,
    Globe, Database, FileSearch, Brain, Shield, Zap,
    ExternalLink, AlertCircle, Loader2, RotateCcw, Lightbulb,
    ChevronRight, BarChart3, Link as LinkIcon, Star
} from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer,
    Cell, PieChart, Pie
} from 'recharts';
import type { V3VerifiedClaim, V3EvidenceItem, HistoryItem } from '../lib/api';
import { investigateClaim } from '../lib/api';
import { NeuralStream } from './NeuralStream';
import { TruthSpectrum } from './TruthSpectrum';

// === Types ===
type InvestigationStep =
    | 'idle'
    | 'extracting'
    | 'checking_misinfo'
    | 'checking_wikidata'
    | 'searching_web'
    | 'analyzing_stance'
    | 'synthesizing'
    | 'complete'
    | 'error';

type VerdictType = 'verified_true' | 'verified_false' | 'disputed' | 'unverified' | 'insufficient_evidence' | 'not_checkable';

// === Constants ===
const STEPS = [
    { id: 'extracting', num: 1, label: 'Extract', desc: 'Analyzing claims', icon: FileSearch, duration: 800 },
    { id: 'checking_misinfo', num: 2, label: 'Records', desc: 'Known facts', icon: Database, duration: 1000 },
    { id: 'checking_wikidata', num: 3, label: 'Facts', desc: 'Databases', icon: Shield, duration: 1000 },
    { id: 'searching_web', num: 4, label: 'Search', desc: 'Web sources', icon: Globe, duration: 1200 },
    { id: 'analyzing_stance', num: 5, label: 'Analyze', desc: 'Stance detection', icon: Brain, duration: 1000 },
    { id: 'synthesizing', num: 6, label: 'Verdict', desc: 'Synthesizing', icon: Zap, duration: 800 },
] as const;

// Source icons
const SOURCE_ICONS: Record<string, string> = {
    'known_misinfo': '🚨',
    'wikidata': '📊',
    'wikipedia': '📚',
    'fact_check': '✅',
    'news_article': '📰',
    'academic_paper': '🔬',
    'web_search': '🌐',
};

// === Helper Components ===

function GradientText({ children, className = '' }: { children: React.ReactNode; className?: string }) {
    return (
        <span
            className={className}
            style={{
                backgroundImage: 'var(--gradient-primary)',
                backgroundSize: '200% 200%',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
            }}
        >
            {children}
        </span>
    );
}

function GlassCard({ children, className = '', glow = false }: {
    children: React.ReactNode;
    className?: string;
    glow?: boolean;
}) {
    return (
        <div
            className={`relative rounded-3xl backdrop-blur-xl overflow-hidden transition-all
                border border-border/50 bg-card/60 shadow-xl
                dark:border-white/10 dark:bg-gradient-to-br dark:from-card/80 dark:to-card/40
                dark:shadow-[0_0_40px_-15px] dark:shadow-white/10
                dark:ring-1 dark:ring-white/5
                ${glow ? 'dark:border-primary/40 dark:shadow-primary/30' : ''}
                ${className}`}
        >
            {/* Dark mode top edge glow */}
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent hidden dark:block rounded-t-3xl" />
            {children}
        </div>
    );
}

function StepIndicator({
    step,
    isActive,
    isComplete,
    isPending
}: {
    step: typeof STEPS[number];
    isActive: boolean;
    isComplete: boolean;
    isPending: boolean;
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: step.num * 0.1 }}
            className="flex flex-col items-center gap-3 relative z-10"
            style={{ minWidth: '80px' }}
        >
            {/* Numbered circle */}
            <div
                className="relative w-16 h-16 rounded-full flex items-center justify-center transition-all duration-500"
                style={{
                    background: isComplete
                        ? 'linear-gradient(135deg, #10b981, #059669)'
                        : isActive
                            ? 'linear-gradient(135deg, #06b6d4, #0891b2)'
                            : 'rgba(20, 20, 20, 0.8)',
                    border: isActive
                        ? '2px solid rgba(6, 182, 212, 0.5)'
                        : isComplete
                            ? 'none'
                            : '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: isActive
                        ? '0 0 40px rgba(6, 182, 212, 0.5)'
                        : isComplete
                            ? '0 0 30px rgba(16, 185, 129, 0.3)'
                            : 'none',
                }}
            >
                {isComplete ? (
                    <CheckCircle2 className="w-8 h-8 text-white" />
                ) : isActive ? (
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    >
                        <Loader2 className="w-8 h-8 text-white" />
                    </motion.div>
                ) : (
                    <span
                        className="text-xl font-bold"
                        style={{ color: isPending ? 'var(--muted-foreground)' : 'var(--foreground)' }}
                    >
                        {step.num}
                    </span>
                )}

                {isActive && (
                    <motion.div
                        className="absolute inset-0 rounded-full"
                        style={{ border: '2px solid rgba(6, 182, 212, 0.5)' }}
                        animate={{ scale: [1, 1.4, 1], opacity: [0.5, 0, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity }}
                    />
                )}
            </div>

            <div className="text-center">
                <div
                    className="text-sm font-bold tracking-wide uppercase transition-colors"
                >
                    <span className={isActive ? 'text-accent-foreground' : isComplete ? 'text-green-500' : 'text-muted-foreground'}>
                        {step.label}
                    </span>
                </div>
            </div>
        </motion.div>
    );
}

function EvidenceCard({ evidence, index }: { evidence: V3EvidenceItem; index: number }) {
    const stanceStyles = {
        supports: { bg: 'rgba(16, 185, 129, 0.1)', border: 'rgba(16, 185, 129, 0.3)', text: '#34d399', label: '✓ Supports' },
        refutes: { bg: 'rgba(239, 68, 68, 0.1)', border: 'rgba(239, 68, 68, 0.3)', text: '#f87171', label: '✗ Refutes' },
        neutral: { bg: 'rgba(107, 114, 128, 0.1)', border: 'rgba(107, 114, 128, 0.3)', text: '#9ca3af', label: '○ Neutral' },
    };
    const s = stanceStyles[evidence.stance] || stanceStyles.neutral;
    const icon = SOURCE_ICONS[evidence.source_type] || '🌐';

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="group relative p-6 rounded-2xl transition-all duration-300 hover:scale-[1.01] backdrop-blur-sm
                border border-border/40 bg-card
                hover:bg-muted/10 dark:hover:bg-white/5
                dark:border-white/10 dark:bg-gradient-to-br dark:from-card/60 dark:to-card/30
                dark:hover:border-white/20 dark:shadow-[0_0_30px_-15px] dark:shadow-white/5
                dark:ring-1 dark:ring-white/5"
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center text-xl">
                        {icon}
                    </div>
                    <div>
                        <div className="font-semibold text-foreground text-base truncate max-w-[180px]">
                            {evidence.source_domain}
                        </div>
                        <div className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
                            {evidence.source_type.replace('_', ' ')}
                        </div>
                    </div>
                </div>
                <span
                    className="px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider"
                    style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.text }}
                >
                    {s.label}
                </span>
            </div>

            {/* Source DNA Badges */}
            <div className="flex gap-2 mb-3 flex-wrap">
                {evidence.source_type === 'academic_paper' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wide">
                        Academic Source
                    </span>
                )}
                {evidence.source_type === 'fact_check' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-500/10 text-green-400 border border-green-500/20 uppercase tracking-wide">
                        Verified Fact Check
                    </span>
                )}
                {evidence.trust_score >= 80 && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20 uppercase tracking-wide">
                        High Authority
                    </span>
                )}
                {evidence.trust_score < 40 && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 uppercase tracking-wide">
                        Low Reliability
                    </span>
                )}
            </div>

            <p className="text-sm leading-relaxed mb-4 text-muted-foreground">
                "{evidence.text_preview}"
            </p>

            <div className="flex items-center justify-between pt-4 border-t border-white/5">
                <div className="flex items-center gap-3 w-full max-w-[200px]">
                    <span
                        className="text-xs font-bold"
                        style={{ color: evidence.trust_score >= 80 ? '#34d399' : evidence.trust_score >= 50 ? '#fbbf24' : '#f87171' }}
                    >
                        {evidence.trust_score}% Trust
                    </span>
                    <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div
                            className="h-full rounded-full transition-all duration-1000"
                            style={{
                                width: `${evidence.trust_score}%`,
                                background: evidence.trust_score >= 80 ? '#34d399' : evidence.trust_score >= 50 ? '#fbbf24' : '#f87171'
                            }}
                        />
                    </div>
                </div>

                {evidence.source_url && (
                    <a
                        href={evidence.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
                    >
                        Source <ExternalLink className="w-3 h-3" />
                    </a>
                )}
            </div>
        </motion.div>
    );
}

function AnalysisCharts({ evidence }: { evidence: V3EvidenceItem[] }) {
    const trustData = useMemo(() => {
        return evidence.map((e) => ({
            name: e.source_domain,
            trust: e.trust_score,
            stance: e.stance
        })).sort((a, b) => b.trust - a.trust).slice(0, 8);
    }, [evidence]);

    const stanceData = useMemo(() => {
        const counts = { supports: 0, refutes: 0, neutral: 0 };
        evidence.forEach(e => {
            if (counts[e.stance] !== undefined) counts[e.stance]++;
        });
        return [
            { name: 'Supports', value: counts.supports, color: '#34d399' },
            { name: 'Refutes', value: counts.refutes, color: '#f87171' },
            { name: 'Neutral', value: counts.neutral, color: '#9ca3af' }
        ].filter(d => d.value > 0);
    }, [evidence]);

    if (evidence.length === 0) return null;

    // Theme-aware colors via CSS variables
    const labelColor = 'oklch(var(--muted-foreground))';
    const gridColor = 'oklch(var(--border) / 0.2)';

    return (
        <div className="grid md:grid-cols-2 gap-6 mb-8">
            <GlassCard className="p-8">
                <div className="flex items-center gap-3 mb-8">
                    <div className="p-2 rounded-lg bg-cyan-500/10">
                        <BarChart3 className="w-5 h-5 text-cyan-500" />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground">Source Reliability</h3>
                </div>
                <div className="h-[220px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={trustData} layout="vertical" margin={{ left: 0, right: 30, top: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={gridColor} />
                            <XAxis type="number" domain={[0, 100]} hide />
                            <YAxis
                                type="category"
                                dataKey="name"
                                width={120}
                                tick={{ fill: labelColor, fontSize: 12, fontWeight: 500 }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <Bar dataKey="trust" radius={[0, 4, 4, 0]} barSize={24}>
                                {trustData.map((entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={entry.trust >= 80 ? '#34d399' : entry.trust >= 50 ? '#fbbf24' : '#f87171'}
                                        fillOpacity={0.9}
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </GlassCard>

            <GlassCard className="p-8">
                <div className="flex items-center gap-3 mb-8">
                    <div className="p-2 rounded-lg bg-purple-500/10">
                        <Brain className="w-5 h-5 text-purple-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-foreground">Stance Distribution</h3>
                </div>
                <div className="h-[220px] flex items-center justify-center relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={stanceData}
                                innerRadius={70}
                                outerRadius={90}
                                paddingAngle={5}
                                dataKey="value"
                                stroke="none"
                            >
                                {stanceData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                        <div className="text-3xl font-bold text-foreground">{evidence.length}</div>
                        <div className="text-xs text-muted-foreground uppercase tracking-widest mt-1">Sources</div>
                    </div>
                </div>
                <div className="flex justify-center gap-6 mt-4">
                    {stanceData.map(d => (
                        <div key={d.name} className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ background: d.color }} />
                            <span className="text-sm text-foreground/80 font-medium">{d.name}</span>
                        </div>
                    ))}
                </div>
            </GlassCard>
        </div>
    );
}

// Verdict display
function VerdictDisplay({ claim }: { claim: V3VerifiedClaim }) {
    const verdictStyles: Record<VerdictType, { gradient: string; icon: typeof CheckCircle2; label: string }> = {
        verified_true: {
            gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            icon: CheckCircle2,
            label: 'VERIFIED TRUE'
        },
        verified_false: {
            gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            icon: XCircle,
            label: 'VERIFIED FALSE'
        },
        disputed: {
            gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            icon: AlertTriangle,
            label: 'DISPUTED'
        },
        unverified: {
            gradient: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
            icon: AlertCircle,
            label: 'UNVERIFIED'
        },
        insufficient_evidence: {
            gradient: 'linear-gradient(135deg, #eab308 0%, #ca8a04 100%)',
            icon: AlertCircle,
            label: 'INSUFFICIENT EVIDENCE'
        },
        not_checkable: {
            gradient: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
            icon: AlertCircle,
            label: 'NOT CHECKABLE'
        },
    };

    const v = verdictStyles[claim.verdict as VerdictType] || verdictStyles.unverified;
    const Icon = v.icon;
    const confidence = Math.round(claim.confidence * 100);

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: "spring", damping: 20 }}
            className="w-full"
        >
            <div className="relative overflow-hidden rounded-[2.5rem] p-[1px]" style={{ background: v.gradient }}>
                <div className="absolute inset-0 opacity-20 bg-background mix-blend-overlay" />

                <div className="relative bg-background/95 rounded-[2.5rem] p-8 md:p-12 overflow-hidden border border-border/20 shadow-2xl">
                    {/* Background glow for verdict */}
                    <div
                        className="absolute -top-32 -right-32 w-96 h-96 rounded-full opacity-20 blur-[100px]"
                        style={{ background: v.gradient }}
                    />

                    <div className="relative z-10 flex flex-col md:flex-row gap-8 md:gap-16 items-start">
                        {/* Main Verdict Info */}
                        <div className="flex-1 space-y-8">
                            <div>
                                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-6">
                                    <Star className="w-3 h-3 text-white/60" />
                                    <span className="text-xs font-medium text-white/60 uppercase tracking-widest">
                                        AI Investigation Result
                                    </span>
                                </div>

                                <div className="flex items-center gap-6 mb-2">
                                    <div
                                        className="w-20 h-20 rounded-2xl flex items-center justify-center shadow-lg transform -rotate-3"
                                        style={{ background: v.gradient }}
                                    >
                                        <Icon className="w-10 h-10 text-white" />
                                    </div>
                                    <h2
                                        className="text-5xl md:text-6xl font-black tracking-tight"
                                        style={{
                                            background: v.gradient,
                                            WebkitBackgroundClip: 'text',
                                            WebkitTextFillColor: 'transparent',
                                        }}
                                    >
                                        {v.label}
                                    </h2>
                                </div>
                            </div>

                            <div className="bg-white/5 rounded-2xl p-6 border border-white/5 backdrop-blur-sm">
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-sm font-medium text-muted-foreground/70">Confidence Level</span>
                                    <span className="text-xl font-bold text-foreground">{confidence}%</span>
                                </div>
                                <div className="h-3 bg-muted/20 rounded-full overflow-hidden p-0.5">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${confidence}%` }}
                                        transition={{ duration: 1.5, ease: "easeOut" }}
                                        className="h-full rounded-full shadow-lg"
                                        style={{ background: v.gradient }}
                                    />
                                </div>
                            </div>

                            <p className="text-xl leading-relaxed text-foreground/80 font-light">
                                {claim.evidence_summary}
                            </p>

                            {/* Consensus Spectrum */}
                            <div className="pt-4">
                                <TruthSpectrum
                                    score={
                                        claim.verdict === 'verified_true' ? 0.5 + (0.5 * claim.confidence) :
                                            claim.verdict === 'verified_false' ? 0.5 - (0.5 * claim.confidence) :
                                                0.5
                                    }
                                    confidence={claim.confidence}
                                    evidenceCount={claim.evidence.length}
                                />
                            </div>
                        </div>

                        {/* Quick Stats Column */}
                        <div className="w-full md:w-72 space-y-4">
                            <div className="group rounded-2xl p-5 transition-colors
                                bg-muted/30 hover:bg-muted/50 border border-border/50
                                dark:bg-white/[0.03] dark:hover:bg-white/[0.06] dark:border-white/5">
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-2 rounded-lg bg-blue-500/20">
                                        <Database className="w-4 h-4 text-blue-500 dark:text-blue-400" />
                                    </div>
                                    <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Sources Checked</div>
                                </div>
                                <div className="text-3xl font-bold text-foreground pl-1">{claim.sources_checked}</div>
                            </div>

                            <div className="group rounded-2xl p-5 transition-colors
                                bg-muted/30 hover:bg-muted/50 border border-border/50
                                dark:bg-white/[0.03] dark:hover:bg-white/[0.06] dark:border-white/5">
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-2 rounded-lg bg-emerald-500/20">
                                        <Zap className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
                                    </div>
                                    <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Speed</div>
                                </div>
                                <div className="text-3xl font-bold text-foreground pl-1">{claim.investigation_time_ms}ms</div>
                            </div>

                            <div className="group rounded-2xl p-5 transition-colors
                                bg-muted/30 hover:bg-muted/50 border border-border/50
                                dark:bg-white/[0.03] dark:hover:bg-white/[0.06] dark:border-white/5">
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-2 rounded-lg bg-purple-500/20">
                                        <Brain className="w-4 h-4 text-purple-500 dark:text-purple-400" />
                                    </div>
                                    <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Category</div>
                                </div>
                                <div className="text-lg font-bold text-foreground pl-1 capitalize truncate">
                                    {claim.claim_type.replace(/_/g, ' ')}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}

// Not Checkable UI (Educational)
function NotCheckableDisplay({ claimType, text }: { claimType: string; text: string }) {
    return (
        <GlassCard className="p-12 text-center" glow>
            <div className="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-6">
                <Lightbulb className="w-12 h-12 text-yellow-500" />
            </div>

            <h2 className="text-3xl font-bold text-white mb-4">Input Not Verifiable</h2>

            <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-8 leading-relaxed">
                The content you provided appears to be <span className="text-foreground font-semibold">"{claimType}"</span> which relies on subjective interpretation rather than objective facts.
            </p>

            <div className="bg-muted/10 rounded-2xl p-6 max-w-xl mx-auto border border-border/10">
                <div className="text-xs text-muted-foreground uppercase tracking-widest mb-3">Your Input</div>
                <p className="text-foreground/90 italic font-serif text-lg">"{text}"</p>
            </div>
        </GlassCard>
    );
}

// === Main Component ===
export function InvestigationPage() {
    const [inputText, setInputText] = useState('');
    const [currentStep, setCurrentStep] = useState<InvestigationStep>('idle');
    const [completedSteps, setCompletedSteps] = useState<string[]>([]);
    const [verifiedClaims, setVerifiedClaims] = useState<V3VerifiedClaim[]>([]);
    const [activeClaimIndex, setActiveClaimIndex] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [isArchived, setIsArchived] = useState(false);

    // Auto-detect URL
    const isUrl = useMemo(() => {
        const trimmed = inputText.trim();
        return trimmed.startsWith('http://') || trimmed.startsWith('https://');
    }, [inputText]);

    const location = useLocation();

    useEffect(() => {
        if (location.state?.archivedResult) {
            const archived = location.state.archivedResult as HistoryItem;
            // Map HistoryItem to V3VerifiedClaim
            const confidenceMap: Record<string, number> = { 'High': 0.9, 'Medium': 0.6, 'Low': 0.3, 'high': 0.9, 'medium': 0.6, 'low': 0.3 };

            const claim: V3VerifiedClaim = {
                original_text: archived.input_text || archived.claim,
                claim_type: 'fact',
                verdict: (archived.verdict?.toLowerCase().replace(' ', '_') || 'unverified') as any,
                confidence: confidenceMap[archived.confidence] || 0.5,
                evidence_summary: archived.explanation || 'No explanation available for this archived result.',
                evidence_count: 0,
                sources_checked: 0,
                investigation_time_ms: 0, // Unknown
                evidence: [] // Evidence not archived in V1/V2
            };

            setVerifiedClaims([claim]);
            setInputText(claim.original_text);
            setCurrentStep('complete');
            setIsArchived(true);
        } else if (location.state?.initialQuery && !inputText) {
            setInputText(location.state.initialQuery);
        }
    }, [location.state]);

    // Effect to trigger run when inputText is set from navigation
    useEffect(() => {
        if (location.state?.initialQuery && inputText === location.state.initialQuery && currentStep === 'idle') {
            runInvestigation();
        }
    }, [inputText, location.state, currentStep]);

    const runInvestigation = useCallback(async (manualInput?: string) => {
        const textToUse = manualInput || inputText;
        if (!textToUse.trim()) return;

        setError(null);
        setVerifiedClaims([]);
        setCompletedSteps([]);

        // Determine input type
        const autoIsUrl = textToUse.trim().startsWith('http://') || textToUse.trim().startsWith('https://'); // Recalculate for potential manual input
        const inputType = autoIsUrl ? 'url' : 'text';
        const apiPromise = investigateClaim(textToUse, inputType);

        // Animate through steps
        for (const step of STEPS) {
            setCurrentStep(step.id as InvestigationStep);
            await new Promise(resolve => setTimeout(resolve, step.duration));
            setCompletedSteps(prev => [...prev, step.id]);
        }

        try {
            const response = await apiPromise;

            // Prioritize checkable claims if multiple found
            const claims = response.verified_claims || [];
            // Sort: checkable first, then by confidence
            claims.sort((a, b) => {
                const aIdx = a.verdict === 'not_checkable' ? 1 : 0;
                const bIdx = b.verdict === 'not_checkable' ? 1 : 0;
                return aIdx - bIdx;
            });

            setVerifiedClaims(claims);
            setActiveClaimIndex(0);
            setCurrentStep('complete');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Investigation failed');
            setCurrentStep('error');
        }
    }, [inputText, isUrl]);

    const handleReset = () => {
        setInputText('');
        setCurrentStep('idle');
        setCompletedSteps([]);
        setVerifiedClaims([]);
        setError(null);
    };

    const isInvestigating = currentStep !== 'idle' && currentStep !== 'complete' && currentStep !== 'error';
    const primaryClaim = verifiedClaims[activeClaimIndex];

    return (
        <div
            className="min-h-screen pt-28 pb-24 px-6 font-sans text-foreground transition-colors duration-300"
        >

            <div className="relative z-10 max-w-7xl mx-auto">

                {/* Hero Header */}
                <motion.div
                    initial={{ opacity: 0, y: -30 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-16"
                >
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-6 backdrop-blur-md">
                        <span className="relative flex h-2 w-2">
                            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isArchived ? 'bg-amber-400' : 'bg-emerald-400'}`}></span>
                            <span className={`relative inline-flex rounded-full h-2 w-2 ${isArchived ? 'bg-amber-500' : 'bg-emerald-500'}`}></span>
                        </span>
                        <span className="text-xs font-semibold text-foreground/80 uppercase tracking-widest">
                            {isArchived ? 'Archived Analysis' : 'TruthLens V3 Active'}
                        </span>
                    </div>

                    <h1 className="text-6xl md:text-7xl font-bold mb-6 tracking-tight">
                        <GradientText>TruthLens Investigation</GradientText>
                    </h1>
                    <p className="text-xl md:text-2xl font-light text-muted-foreground max-w-2xl mx-auto">
                        Advanced claim verification and real-time evidence synthesis
                    </p>
                </motion.div>

                {/* Input Section */}
                <AnimatePresence mode="wait">
                    {currentStep === 'idle' && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="mb-24"
                        >
                            <div className="max-w-4xl mx-auto relative group">
                                {/* Glowing border effect */}
                                <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-[2rem] opacity-30 group-hover:opacity-60 transition duration-1000 blur"></div>

                                <div className="relative bg-card rounded-[2rem] p-1.5 shadow-xl border border-border/20">
                                    <div className="bg-background/50 rounded-[1.8rem] p-8 md:p-10 relative overflow-hidden backdrop-blur-sm">

                                        <div className="flex justify-between items-center mb-6">
                                            <label className="text-sm font-semibold text-muted-foreground uppercase tracking-widest">
                                                Investigation Target
                                            </label>
                                            {isUrl && (
                                                <div className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-bold flex items-center gap-2 border border-blue-500/20">
                                                    <LinkIcon className="w-3 h-3" />
                                                    ARTICLE DETECTED
                                                </div>
                                            )}
                                        </div>

                                        <textarea
                                            value={inputText}
                                            onChange={(e) => setInputText(e.target.value)}
                                            placeholder="Paste a claim, sentence, or article URL..."
                                            className="w-full h-40 bg-transparent text-3xl md:text-4xl font-light text-foreground placeholder-muted-foreground/60 focus:outline-none resize-none"
                                            spellCheck={false}
                                        />

                                        <div className="flex justify-between items-end mt-6">
                                            <div className="text-xs text-muted-foreground/60">
                                                Supports text, URLs, and social media links
                                            </div>
                                            <button
                                                onClick={() => runInvestigation()}
                                                disabled={!inputText.trim()}
                                                className="group/btn relative px-8 py-4 rounded-xl font-bold text-lg flex items-center gap-3 transition-all disabled:opacity-40 disabled:cursor-not-allowed overflow-hidden"
                                                style={{
                                                    background: inputText.trim()
                                                        ? 'var(--gradient-primary)'
                                                        : 'var(--muted)',
                                                    color: inputText.trim() ? '#fff' : 'var(--muted-foreground)',
                                                }}
                                            >
                                                {/* Shimmer effect */}
                                                <div className="absolute inset-0 -translate-x-full group-hover/btn:animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent" />

                                                <Zap className="w-5 h-5 fill-current" />
                                                <span>{isUrl ? 'Analyze Source' : 'Investigate'}</span>
                                                <ChevronRight className="w-5 h-5 group-hover/btn:translate-x-1 transition-transform" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Timeline Steps / Neural Stream */}
                {(isInvestigating || currentStep === 'complete' || currentStep === 'error') && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="mb-16"
                    >
                        {currentStep === 'complete' ? (
                            <div className="flex items-center justify-center flex-wrap gap-4 md:gap-8">
                                {STEPS.map((step) => (
                                    <div key={step.id} className="relative">
                                        {/* Connector line */}
                                        {step.num < 6 && (
                                            <div className="absolute top-8 left-1/2 w-full h-[2px] bg-white/5 -z-0"
                                                style={{ width: 'calc(100% + 2rem + 80px)' }} />
                                        )}

                                        <StepIndicator
                                            step={step}
                                            isActive={false}
                                            isComplete={completedSteps.includes(step.id)}
                                            isPending={!completedSteps.includes(step.id)}
                                        />
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <NeuralStream currentStep={currentStep} />
                        )}
                    </motion.div>
                )}

                {/* Results Section */}
                <AnimatePresence mode="wait">
                    {/* Error state */}
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                        >
                            <GlassCard className="p-12 max-w-2xl mx-auto text-center">
                                <div className="w-20 h-20 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-6">
                                    <XCircle className="w-10 h-10 text-red-500" />
                                </div>
                                <h3 className="text-2xl font-bold text-foreground mb-2">Investigation Halted</h3>
                                <p className="text-muted-foreground mb-8">{error}</p>
                                <button
                                    onClick={handleReset}
                                    className="px-8 py-3 rounded-full font-bold bg-muted/20 hover:bg-muted/30 transition-colors text-foreground"
                                >
                                    Retry Investigation
                                </button>
                            </GlassCard>
                        </motion.div>
                    )}

                    {/* No Claims Found State */}
                    {!primaryClaim && currentStep === 'complete' && !error && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                        >
                            <GlassCard className="p-12 max-w-2xl mx-auto text-center" glow>
                                <div className="w-20 h-20 bg-amber-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                                    <AlertCircle className="w-10 h-10 text-amber-500" />
                                </div>
                                <h3 className="text-2xl font-bold text-foreground mb-2">No Verifiable Claims Found</h3>
                                <p className="text-muted-foreground mb-8 max-w-md mx-auto">
                                    The input provided doesn't contain a clear factual claim that can be verified.
                                    Try providing a more specific statement or a longer text with concrete claims.
                                </p>
                                <div className="flex justify-center gap-4">
                                    <button
                                        onClick={handleReset}
                                        className="px-8 py-3 rounded-full font-bold bg-muted/20 hover:bg-muted/30 transition-colors text-foreground"
                                    >
                                        Try Again
                                    </button>
                                </div>
                            </GlassCard>
                        </motion.div>
                    )}

                    {/* Success Verified State */}
                    {primaryClaim && currentStep === 'complete' && (
                        <motion.div
                            initial={{ opacity: 0, y: 40 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, ease: "easeOut" }}
                            className="space-y-12"
                        >
                            {/* Action Bar */}
                            <div className="flex justify-between items-center">
                                <div className="text-sm text-muted-foreground/60">
                                    Investigated {verifiedClaims.length} claim(s)
                                </div>
                                <button
                                    onClick={handleReset}
                                    className="flex items-center gap-2 px-6 py-2.5 rounded-full text-sm font-semibold transition-all hover:bg-white/10 text-white/60 hover:text-white border border-transparent hover:border-white/10"
                                >
                                    <RotateCcw className="w-4 h-4" />
                                    New Search
                                </button>
                            </div>

                            {/* Verdict Display */}
                            {primaryClaim.verdict === 'not_checkable' ? (
                                <NotCheckableDisplay
                                    claimType={primaryClaim.claim_type}
                                    text={primaryClaim.original_text}
                                />
                            ) : (
                                <VerdictDisplay claim={primaryClaim} />
                            )}

                            {/* Evidence Visualization */}
                            {primaryClaim.evidence && primaryClaim.evidence.length > 0 && (
                                <AnalysisCharts evidence={primaryClaim.evidence} />
                            )}

                            {/* Detailed Evidence Grid */}
                            {primaryClaim.evidence && primaryClaim.evidence.length > 0 && (
                                <div>
                                    <h2 className="text-2xl font-bold text-foreground mb-8 flex items-center gap-3">
                                        <FileSearch className="w-6 h-6 text-emerald-400" />
                                        Verified Evidence Trail
                                    </h2>
                                    <div className="grid md:grid-cols-2 gap-6">
                                        {primaryClaim.evidence.map((ev, i) => (
                                            <EvidenceCard key={i} evidence={ev} index={i} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Footer Disclaimer */}
                            <div className="border-t border-border/30 dark:border-white/10 pt-8 text-center">
                                <p className="text-xs text-muted-foreground/50 font-mono">
                                    TruthLens v3.0 • Hybrid Pipeline Architecture • Analysis completed in {(primaryClaim.investigation_time_ms / 1000).toFixed(2)}s
                                </p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

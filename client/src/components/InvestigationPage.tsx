import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    CheckCircle2, XCircle, AlertTriangle,
    Globe, Database, FileSearch, Brain, Shield, Zap,
    ExternalLink, AlertCircle, Loader2, RotateCcw, Lightbulb,
    ChevronRight, BarChart3, Link as LinkIcon
} from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer,
    Cell, PieChart, Pie
} from 'recharts';
import type { V3InvestigateResponse, V3VerifiedClaim, V3EvidenceItem } from '../lib/api';
import { investigateClaim } from '../lib/api';

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
                background: 'linear-gradient(135deg, #06b6d4 0%, #10b981 50%, #06b6d4 100%)',
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
            className={`relative rounded-2xl ${className}`}
            style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                boxShadow: glow ? '0 0 60px rgba(6, 182, 212, 0.1)' : 'none',
            }}
        >
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
            className="flex flex-col items-center gap-3"
            style={{ minWidth: '80px' }}
        >
            {/* Numbered circle */}
            <div
                className="relative w-14 h-14 rounded-full flex items-center justify-center transition-all duration-500"
                style={{
                    background: isComplete
                        ? 'linear-gradient(135deg, #10b981, #059669)'
                        : isActive
                            ? 'linear-gradient(135deg, #06b6d4, #0891b2)'
                            : 'rgba(255, 255, 255, 0.05)',
                    border: isActive
                        ? '2px solid rgba(6, 182, 212, 0.5)'
                        : '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: isActive
                        ? '0 0 30px rgba(6, 182, 212, 0.4)'
                        : isComplete
                            ? '0 0 20px rgba(16, 185, 129, 0.3)'
                            : 'none',
                }}
            >
                {isComplete ? (
                    <CheckCircle2 className="w-6 h-6 text-white" />
                ) : isActive ? (
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    >
                        <Loader2 className="w-6 h-6 text-white" />
                    </motion.div>
                ) : (
                    <span
                        className="text-lg font-semibold"
                        style={{ color: isPending ? 'rgba(255,255,255,0.3)' : 'white' }}
                    >
                        {step.num}
                    </span>
                )}

                {isActive && (
                    <motion.div
                        className="absolute inset-0 rounded-full"
                        style={{ border: '2px solid rgba(6, 182, 212, 0.5)' }}
                        animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity }}
                    />
                )}
            </div>

            <div className="text-center">
                <div
                    className="text-sm font-medium"
                    style={{
                        color: isActive ? '#06b6d4' : isComplete ? '#10b981' : 'rgba(255,255,255,0.5)'
                    }}
                >
                    {step.label}
                </div>
                <div
                    className="text-xs mt-0.5"
                    style={{ color: 'rgba(255,255,255,0.3)' }}
                >
                    {step.desc}
                </div>
            </div>
        </motion.div>
    );
}

function EvidenceCard({ evidence, index }: { evidence: V3EvidenceItem; index: number }) {
    const stanceStyles = {
        supports: { bg: 'rgba(16, 185, 129, 0.1)', border: 'rgba(16, 185, 129, 0.3)', text: '#10b981', label: '✓ Supports' },
        refutes: { bg: 'rgba(239, 68, 68, 0.1)', border: 'rgba(239, 68, 68, 0.3)', text: '#ef4444', label: '✗ Refutes' },
        neutral: { bg: 'rgba(107, 114, 128, 0.1)', border: 'rgba(107, 114, 128, 0.3)', text: '#9ca3af', label: '○ Neutral' },
    };
    const s = stanceStyles[evidence.stance] || stanceStyles.neutral;
    const icon = SOURCE_ICONS[evidence.source_type] || '🌐';

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-5 rounded-xl transition-all duration-300 hover:scale-[1.02]"
            style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
            }}
        >
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-xl">{icon}</span>
                    <span className="font-medium text-white truncate max-w-[200px]">{evidence.source_domain}</span>
                </div>
                <span
                    className="px-2.5 py-1 rounded-full text-xs font-medium"
                    style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.text }}
                >
                    {s.label}
                </span>
            </div>

            <p className="text-sm leading-relaxed mb-3 line-clamp-3" style={{ color: 'rgba(255,255,255,0.6)' }}>
                {evidence.text_preview}
            </p>

            <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                    <span style={{ color: evidence.trust_score >= 80 ? '#10b981' : evidence.trust_score >= 50 ? '#f59e0b' : '#ef4444' }}>
                        Trust: {evidence.trust_score}%
                    </span>
                    <div className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                        <div
                            className="h-full rounded-full"
                            style={{
                                width: `${evidence.trust_score}%`,
                                background: evidence.trust_score >= 80 ? '#10b981' : evidence.trust_score >= 50 ? '#f59e0b' : '#ef4444'
                            }}
                        />
                    </div>
                </div>

                {evidence.source_url && (
                    <a
                        href={evidence.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 hover:opacity-80 transition-opacity"
                        style={{ color: '#06b6d4' }}
                    >
                        View <ExternalLink className="w-3 h-3" />
                    </a>
                )}
            </div>
        </motion.div>
    );
}

function AnalysisCharts({ evidence }: { evidence: V3EvidenceItem[] }) {
    // Aggregate trust scores
    const trustData = useMemo(() => {
        return evidence.map((e, i) => ({
            name: e.source_domain,
            trust: e.trust_score,
            stance: e.stance
        })).sort((a, b) => b.trust - a.trust).slice(0, 8); // Top 8 sources
    }, [evidence]);

    // Stance distribution
    const stanceData = useMemo(() => {
        const counts = { supports: 0, refutes: 0, neutral: 0 };
        evidence.forEach(e => {
            if (counts[e.stance] !== undefined) counts[e.stance]++;
        });
        return [
            { name: 'Supports', value: counts.supports, color: '#10b981' },
            { name: 'Refutes', value: counts.refutes, color: '#ef4444' },
            { name: 'Neutral', value: counts.neutral, color: '#9ca3af' }
        ].filter(d => d.value > 0);
    }, [evidence]);

    if (evidence.length === 0) return null;

    return (
        <div className="grid md:grid-cols-2 gap-6 mb-8">
            <GlassCard className="p-6">
                <div className="flex items-center gap-2 mb-6">
                    <BarChart3 className="w-5 h-5" style={{ color: '#06b6d4' }} />
                    <h3 className="font-medium text-white">Source Reliability</h3>
                </div>
                <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={trustData} layout="vertical" margin={{ left: 0, right: 30, top: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
                            <XAxis type="number" domain={[0, 100]} hide />
                            <YAxis
                                type="category"
                                dataKey="name"
                                width={120}
                                tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
                                axisLine={false}
                                tickLine={false}
                            />
                            <Bar dataKey="trust" radius={[0, 4, 4, 0]} barSize={20}>
                                {trustData.map((entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={entry.trust >= 80 ? '#10b981' : entry.trust >= 50 ? '#f59e0b' : '#ef4444'}
                                        fillOpacity={0.8}
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </GlassCard>

            <GlassCard className="p-6">
                <div className="flex items-center gap-2 mb-6">
                    <Brain className="w-5 h-5" style={{ color: '#06b6d4' }} />
                    <h3 className="font-medium text-white">Stance Distribution</h3>
                </div>
                <div className="h-[200px] flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={stanceData}
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {stanceData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                                ))}
                            </Pie>
                        </PieChart>
                    </ResponsiveContainer>
                    {/* Center Label */}
                    <div className="absolute text-center">
                        <div className="text-2xl font-bold text-white">{evidence.length}</div>
                        <div className="text-xs text-white/50">Sources</div>
                    </div>
                </div>
                <div className="flex justify-center gap-4 mt-2">
                    {stanceData.map(d => (
                        <div key={d.name} className="flex items-center gap-2 text-xs">
                            <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                            <span style={{ color: 'rgba(255,255,255,0.6)' }}>{d.name} ({d.value})</span>
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
            gradient: 'linear-gradient(135deg, #10b981, #059669)',
            icon: CheckCircle2,
            label: 'VERIFIED TRUE'
        },
        verified_false: {
            gradient: 'linear-gradient(135deg, #ef4444, #dc2626)',
            icon: XCircle,
            label: 'VERIFIED FALSE'
        },
        disputed: {
            gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
            icon: AlertTriangle,
            label: 'DISPUTED'
        },
        unverified: {
            gradient: 'linear-gradient(135deg, #6b7280, #4b5563)',
            icon: AlertCircle,
            label: 'UNVERIFIED'
        },
        insufficient_evidence: {
            gradient: 'linear-gradient(135deg, #eab308, #ca8a04)',
            icon: AlertCircle,
            label: 'INSUFFICIENT EVIDENCE'
        },
        not_checkable: {
            gradient: 'linear-gradient(135deg, #6b7280, #4b5563)',
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
        >
            <GlassCard className="p-8" glow>
                <div className="flex flex-col md:flex-row gap-8 items-start">
                    {/* Main Verdict Info */}
                    <div className="flex-1">
                        <div
                            className="text-xs font-medium tracking-widest mb-4"
                            style={{ color: 'rgba(255,255,255,0.4)' }}
                        >
                            VERDICT ANALYSIS
                        </div>

                        <div className="flex items-center gap-4 mb-6">
                            <div
                                className="w-16 h-16 rounded-2xl flex items-center justify-center shrink-0"
                                style={{ background: v.gradient }}
                            >
                                <Icon className="w-8 h-8 text-white" />
                            </div>
                            <div>
                                <div
                                    className="text-3xl md:text-4xl font-bold"
                                    style={{
                                        background: v.gradient,
                                        WebkitBackgroundClip: 'text',
                                        WebkitTextFillColor: 'transparent',
                                    }}
                                >
                                    {v.label}
                                </div>
                            </div>
                        </div>

                        <div className="mb-6">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>Evidence Confidence</span>
                                <span className="text-sm font-semibold" style={{ color: '#06b6d4' }}>{confidence}%</span>
                            </div>
                            <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.1)' }}>
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${confidence}%` }}
                                    transition={{ duration: 1, ease: "easeOut" }}
                                    className="h-full rounded-full"
                                    style={{ background: v.gradient }}
                                />
                            </div>
                        </div>

                        <p className="text-lg leading-relaxed text-white/80">
                            {claim.evidence_summary}
                        </p>
                    </div>

                    {/* Quick Stats */}
                    <div className="w-full md:w-64 space-y-3">
                        <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                            <div className="text-xs text-white/40 mb-1">Sources Checked</div>
                            <div className="text-2xl font-bold text-white">{claim.sources_checked}</div>
                        </div>
                        <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                            <div className="text-xs text-white/40 mb-1">Response Time</div>
                            <div className="text-2xl font-bold text-white">{claim.investigation_time_ms}ms</div>
                        </div>
                        <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                            <div className="text-xs text-white/40 mb-1">Claim Type</div>
                            <div className="text-lg font-medium text-white capitalize">{claim.claim_type.replace('_', ' ')}</div>
                        </div>
                    </div>
                </div>
            </GlassCard>
        </motion.div>
    );
}

// === Main Component ===
export function InvestigationPage() {
    const [inputText, setInputText] = useState('');
    const [currentStep, setCurrentStep] = useState<InvestigationStep>('idle');
    const [completedSteps, setCompletedSteps] = useState<string[]>([]);
    const [_result, setResult] = useState<V3InvestigateResponse | null>(null);
    const [primaryClaim, setPrimaryClaim] = useState<V3VerifiedClaim | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Auto-detect URL
    const isUrl = useMemo(() => {
        const trimmed = inputText.trim();
        return trimmed.startsWith('http://') || trimmed.startsWith('https://');
    }, [inputText]);

    const runInvestigation = useCallback(async () => {
        if (!inputText.trim()) return;

        setError(null);
        setResult(null);
        setPrimaryClaim(null);
        setCompletedSteps([]);

        // Determine input type
        const inputType = isUrl ? 'url' : 'text';
        const apiPromise = investigateClaim(inputText, inputType);

        // Animate through steps
        for (const step of STEPS) {
            setCurrentStep(step.id as InvestigationStep);
            await new Promise(resolve => setTimeout(resolve, step.duration));
            setCompletedSteps(prev => [...prev, step.id]);
        }

        try {
            const response = await apiPromise;
            setResult(response);
            setPrimaryClaim(response.verified_claims?.[0] || null);
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
        setResult(null);
        setPrimaryClaim(null);
        setError(null);
    };

    const isInvestigating = currentStep !== 'idle' && currentStep !== 'complete' && currentStep !== 'error';

    return (
        <div
            className="min-h-screen pt-24 pb-16 px-6"
            style={{ background: 'linear-gradient(180deg, #050505 0%, #0a0a0a 100%)' }}
        >
            {/* Background glow effects */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div
                    className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] opacity-30"
                    style={{
                        background: 'radial-gradient(ellipse, rgba(6, 182, 212, 0.15) 0%, transparent 70%)',
                    }}
                />
            </div>

            <div className="relative z-10 max-w-6xl mx-auto">
                {/* Hero Header */}
                <motion.div
                    initial={{ opacity: 0, y: -30 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-12"
                >
                    <h1 className="text-5xl md:text-6xl font-bold mb-4 tracking-tight">
                        <GradientText>TruthLens Investigation</GradientText>
                    </h1>
                    <p className="text-lg" style={{ color: 'rgba(255,255,255,0.5)' }}>
                        Comprehensive claim verification and article analysis
                    </p>
                </motion.div>

                {/* Input Section */}
                <AnimatePresence mode="wait">
                    {currentStep === 'idle' && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="mb-16"
                        >
                            <GlassCard className="p-8 max-w-3xl mx-auto">
                                <div className="flex justify-between items-center mb-4">
                                    <label
                                        className="block text-sm font-medium"
                                        style={{ color: 'rgba(255,255,255,0.6)' }}
                                    >
                                        Enter a claim or article URL
                                    </label>
                                    {isUrl && (
                                        <motion.div
                                            initial={{ opacity: 0, x: 10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            className="px-2 py-1 rounded bg-blue-500/10 text-blue-400 text-xs border border-blue-500/20 flex items-center gap-1"
                                        >
                                            <LinkIcon className="w-3 h-3" />
                                            URL Detected
                                        </motion.div>
                                    )}
                                </div>
                                <textarea
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    placeholder="Examples:
- 'COVID vaccines cause autism'
- https://example.com/news/article"
                                    className="w-full h-32 px-5 py-4 rounded-xl resize-none text-white text-lg focus:outline-none transition-all"
                                    style={{
                                        background: 'rgba(255,255,255,0.03)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                    }}
                                    onFocus={(e) => e.target.style.borderColor = 'rgba(6, 182, 212, 0.5)'}
                                    onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
                                />
                                <button
                                    onClick={runInvestigation}
                                    disabled={!inputText.trim()}
                                    className="w-full mt-6 py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-3 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                                    style={{
                                        background: inputText.trim()
                                            ? 'linear-gradient(135deg, #06b6d4 0%, #10b981 100%)'
                                            : 'rgba(255,255,255,0.1)',
                                        color: inputText.trim() ? '#000' : 'rgba(255,255,255,0.3)',
                                        boxShadow: inputText.trim() ? '0 0 40px rgba(6, 182, 212, 0.3)' : 'none',
                                    }}
                                >
                                    <Zap className="w-5 h-5" />
                                    {isUrl ? 'Analyze Article' : 'Start Investigation'}
                                    <ChevronRight className="w-5 h-5" />
                                </button>
                            </GlassCard>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Timeline Steps - Horizontal */}
                {(isInvestigating || currentStep === 'complete' || currentStep === 'error') && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-12"
                    >
                        {/* Connection Lines (Behind) */}
                        <div className="flex items-center justify-center flex-wrap gap-2">
                            {STEPS.map((step) => (
                                <StepIndicator
                                    key={step.id}
                                    step={step}
                                    isActive={currentStep === step.id}
                                    isComplete={completedSteps.includes(step.id)}
                                    isPending={!completedSteps.includes(step.id) && currentStep !== step.id}
                                />
                            ))}
                        </div>
                    </motion.div>
                )}

                {/* Results Section */}
                <AnimatePresence mode="wait">
                    {/* Loading state */}
                    {isInvestigating && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="text-center py-12"
                        >
                            <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full" style={{ background: 'rgba(6, 182, 212, 0.1)' }}>
                                <Loader2 className="w-5 h-5 animate-spin" style={{ color: '#06b6d4' }} />
                                <span style={{ color: '#06b6d4' }}>Analyzing content and gathering evidence...</span>
                            </div>
                        </motion.div>
                    )}

                    {/* Error state */}
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                        >
                            <GlassCard className="p-8 max-w-2xl mx-auto text-center">
                                <XCircle className="w-12 h-12 mx-auto mb-4" style={{ color: '#ef4444' }} />
                                <h3 className="text-xl font-semibold mb-2" style={{ color: '#ef4444' }}>Investigation Failed</h3>
                                <p className="mb-6" style={{ color: 'rgba(255,255,255,0.6)' }}>{error}</p>
                                <button
                                    onClick={handleReset}
                                    className="px-6 py-3 rounded-xl font-medium"
                                    style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' }}
                                >
                                    <RotateCcw className="w-4 h-4 inline mr-2" />
                                    Try Again
                                </button>
                            </GlassCard>
                        </motion.div>
                    )}

                    {/* Success state */}
                    {primaryClaim && currentStep === 'complete' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="space-y-8"
                        >
                            {/* New search button */}
                            <div className="flex justify-end">
                                <button
                                    onClick={handleReset}
                                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all hover:opacity-80"
                                    style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.6)' }}
                                >
                                    <RotateCcw className="w-4 h-4" />
                                    New Investigation
                                </button>
                            </div>

                            {/* Verdict */}
                            <VerdictDisplay claim={primaryClaim} />

                            {/* Deep Analysis Charts */}
                            {primaryClaim.evidence && primaryClaim.evidence.length > 0 && (
                                <AnalysisCharts evidence={primaryClaim.evidence} />
                            )}

                            {/* Evidence cards */}
                            {primaryClaim.evidence && primaryClaim.evidence.length > 0 && (
                                <div>
                                    <h2 className="text-xl font-semibold mb-6" style={{ color: 'rgba(255,255,255,0.9)' }}>
                                        Detailed Evidence
                                    </h2>
                                    <div className="grid md:grid-cols-2 gap-4">
                                        {primaryClaim.evidence.map((ev, i) => (
                                            <EvidenceCard key={i} evidence={ev} index={i} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Disclaimer */}
                            <div
                                className="p-4 rounded-xl flex gap-3 max-w-2xl mx-auto"
                                style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)' }}
                            >
                                <AlertTriangle className="w-5 h-5 flex-shrink-0" style={{ color: '#f59e0b' }} />
                                <p className="text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>
                                    <span className="font-medium" style={{ color: '#f59e0b' }}>Advisory:</span> This is an automated assessment. Always verify critical information from multiple trusted sources.
                                </p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

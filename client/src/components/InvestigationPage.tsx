import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search, CheckCircle2, XCircle, AlertTriangle,
    Globe, Database, FileSearch, Brain, Shield, Zap,
    ExternalLink, AlertCircle, Loader2, RotateCcw, Lightbulb,
    ChevronRight
} from 'lucide-react';
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

// === Styled Components ===

// Gradient text component
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

// Glass card component
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

// Numbered step indicator (supermemory style)
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
    const Icon = step.icon;

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

                {/* Active pulse ring */}
                {isActive && (
                    <motion.div
                        className="absolute inset-0 rounded-full"
                        style={{ border: '2px solid rgba(6, 182, 212, 0.5)' }}
                        animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity }}
                    />
                )}
            </div>

            {/* Label */}
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

// Connection line between steps
function StepConnector({ isComplete }: { isComplete: boolean }) {
    return (
        <div
            className="flex-1 h-0.5 mx-2 rounded-full transition-all duration-500"
            style={{
                background: isComplete
                    ? 'linear-gradient(90deg, #10b981, #06b6d4)'
                    : 'rgba(255, 255, 255, 0.1)',
                minWidth: '20px',
                maxWidth: '60px',
            }}
        />
    );
}

// Evidence card
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
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-xl">{icon}</span>
                    <span className="font-medium text-white">{evidence.source_domain}</span>
                </div>
                <span
                    className="px-2.5 py-1 rounded-full text-xs font-medium"
                    style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.text }}
                >
                    {s.label}
                </span>
            </div>

            {/* Content */}
            <p className="text-sm leading-relaxed mb-3" style={{ color: 'rgba(255,255,255,0.6)' }}>
                {evidence.text_preview}
            </p>

            {/* Footer */}
            <div className="flex items-center justify-between text-xs">
                <span style={{ color: evidence.trust_score >= 80 ? '#10b981' : evidence.trust_score >= 50 ? '#f59e0b' : '#ef4444' }}>
                    Trust: {evidence.trust_score}%
                </span>
                {evidence.source_url && (
                    <a
                        href={evidence.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 hover:opacity-80"
                        style={{ color: '#06b6d4' }}
                    >
                        View <ExternalLink className="w-3 h-3" />
                    </a>
                )}
            </div>
        </motion.div>
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
                {/* Verdict label */}
                <div
                    className="text-xs font-medium tracking-widest mb-4"
                    style={{ color: 'rgba(255,255,255,0.4)' }}
                >
                    VERDICT
                </div>

                {/* Main verdict */}
                <div className="flex items-center gap-4 mb-6">
                    <div
                        className="w-16 h-16 rounded-2xl flex items-center justify-center"
                        style={{ background: v.gradient }}
                    >
                        <Icon className="w-8 h-8 text-white" />
                    </div>
                    <div>
                        <div
                            className="text-3xl font-bold"
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

                {/* Confidence bar */}
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>
                            Evidence Confidence
                        </span>
                        <span className="text-sm font-semibold" style={{ color: '#06b6d4' }}>
                            {confidence}%
                        </span>
                    </div>
                    <div
                        className="h-2 rounded-full overflow-hidden"
                        style={{ background: 'rgba(255,255,255,0.1)' }}
                    >
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${confidence}%` }}
                            transition={{ duration: 1, ease: "easeOut" }}
                            className="h-full rounded-full"
                            style={{ background: v.gradient }}
                        />
                    </div>
                    <p className="text-xs mt-2 italic" style={{ color: 'rgba(255,255,255,0.3)' }}>
                        Based on evidence consistency, not absolute truth
                    </p>
                </div>

                {/* Summary */}
                <p className="text-base leading-relaxed mb-6" style={{ color: 'rgba(255,255,255,0.7)' }}>
                    {claim.evidence_summary}
                </p>

                {/* Stats */}
                <div className="flex gap-4">
                    <div
                        className="px-4 py-2 rounded-lg"
                        style={{ background: 'rgba(255,255,255,0.05)' }}
                    >
                        <span style={{ color: 'rgba(255,255,255,0.6)' }}>{claim.sources_checked} sources</span>
                    </div>
                    <div
                        className="px-4 py-2 rounded-lg"
                        style={{ background: 'rgba(255,255,255,0.05)' }}
                    >
                        <span style={{ color: 'rgba(255,255,255,0.6)' }}>{claim.investigation_time_ms}ms</span>
                    </div>
                </div>
            </GlassCard>
        </motion.div>
    );
}

// Not checkable education
function NotCheckableEducation({ claimType, text }: { claimType: string; text: string }) {
    const info: Record<string, { icon: string; title: string; desc: string; tip: string }> = {
        opinion: {
            icon: '💭',
            title: 'This is an Opinion',
            desc: 'Opinions express personal beliefs and cannot be objectively verified.',
            tip: 'Try rephrasing as a factual claim with measurable criteria.'
        },
        prediction: {
            icon: '🔮',
            title: 'This is a Prediction',
            desc: 'Future events cannot be verified until they occur.',
            tip: 'Check back after the predicted date, or search for expert forecasts.'
        },
        question: {
            icon: '❓',
            title: 'This is a Question',
            desc: 'Questions seek information rather than making claims.',
            tip: 'Convert your question to a statement to fact-check it.'
        },
    };
    const i = info[claimType] || { icon: '🔍', title: 'Unable to Verify', desc: 'This statement cannot be fact-checked.', tip: 'Try simplifying or rephrasing.' };

    return (
        <GlassCard className="p-8">
            <div className="text-4xl mb-4">{i.icon}</div>
            <h3 className="text-2xl font-semibold text-white mb-3">{i.title}</h3>
            <p className="text-base mb-6" style={{ color: 'rgba(255,255,255,0.6)' }}>{i.desc}</p>

            <div
                className="p-4 rounded-xl flex gap-3"
                style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}
            >
                <Lightbulb className="w-5 h-5 flex-shrink-0" style={{ color: '#06b6d4' }} />
                <div>
                    <span className="text-sm font-medium" style={{ color: '#06b6d4' }}>Tip:</span>
                    <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.6)' }}>{i.tip}</p>
                </div>
            </div>

            <div className="mt-6 p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)' }}>
                <span className="text-xs" style={{ color: 'rgba(255,255,255,0.4)' }}>Your input:</span>
                <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.6)' }}>"{text}"</p>
            </div>
        </GlassCard>
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

    const runInvestigation = useCallback(async () => {
        if (!inputText.trim()) return;

        setError(null);
        setResult(null);
        setPrimaryClaim(null);
        setCompletedSteps([]);

        const apiPromise = investigateClaim(inputText);

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
    }, [inputText]);

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

            <div className="relative z-10 max-w-5xl mx-auto">
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
                        Watch the verification process unfold in real-time
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
                                <label
                                    className="block text-sm font-medium mb-4"
                                    style={{ color: 'rgba(255,255,255,0.6)' }}
                                >
                                    Enter a claim to investigate
                                </label>
                                <textarea
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    placeholder="e.g., 'COVID vaccines cause autism' or 'The Earth is flat'"
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
                                    Start Investigation
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
                        <div className="flex items-center justify-center flex-wrap gap-2">
                            {STEPS.map((step, i) => (
                                <div key={step.id} className="flex items-center">
                                    <StepIndicator
                                        step={step}
                                        isActive={currentStep === step.id}
                                        isComplete={completedSteps.includes(step.id)}
                                        isPending={!completedSteps.includes(step.id) && currentStep !== step.id}
                                    />
                                    {i < STEPS.length - 1 && (
                                        <StepConnector isComplete={completedSteps.includes(STEPS[i + 1].id)} />
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Current claim being investigated */}
                        <div className="mt-8 text-center">
                            <span className="text-xs" style={{ color: 'rgba(255,255,255,0.4)' }}>Investigating:</span>
                            <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.6)' }}>"{inputText}"</p>
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
                                <span style={{ color: '#06b6d4' }}>Gathering evidence...</span>
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
                                    onClick={runInvestigation}
                                    className="px-6 py-3 rounded-xl font-medium"
                                    style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' }}
                                >
                                    <RotateCcw className="w-4 h-4 inline mr-2" />
                                    Retry
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

                            {/* Verdict or Not Checkable */}
                            {primaryClaim.verdict === 'not_checkable' ? (
                                <NotCheckableEducation
                                    claimType={primaryClaim.claim_type}
                                    text={primaryClaim.original_text}
                                />
                            ) : (
                                <VerdictDisplay claim={primaryClaim} />
                            )}

                            {/* Evidence cards */}
                            {primaryClaim.evidence && primaryClaim.evidence.length > 0 && (
                                <div>
                                    <h2 className="text-xl font-semibold mb-6" style={{ color: 'rgba(255,255,255,0.9)' }}>
                                        Evidence Found
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

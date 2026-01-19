import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search, CheckCircle2, XCircle, AlertTriangle, Clock,
    Database, Globe, FileSearch, Brain, ChevronDown, ChevronUp,
    ExternalLink, Shield, AlertCircle, Loader2, RotateCcw, Info,
    BookOpen, Lightbulb
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

interface TimelineStepData {
    id: InvestigationStep;
    label: string;
    honestLabel: string;  // Senior feedback: honest language
    icon: React.ElementType;
    duration: number;  // Minimum display time in ms
}

// === Constants ===
const TIMELINE_STEPS: TimelineStepData[] = [
    { id: 'extracting', label: 'Extracting Claims', honestLabel: 'Analyzing text for verifiable claims...', icon: FileSearch, duration: 800 },
    { id: 'checking_misinfo', label: 'Known Records', honestLabel: 'Scanning prior verifications (if available)', icon: Database, duration: 1000 },
    { id: 'checking_wikidata', label: 'Fact Database', honestLabel: 'Checking structured knowledge sources', icon: BookOpen, duration: 1000 },
    { id: 'searching_web', label: 'Web Evidence', honestLabel: 'Searching available online sources...', icon: Globe, duration: 1200 },
    { id: 'analyzing_stance', label: 'Stance Analysis', honestLabel: 'Analyzing evidence consistency...', icon: Brain, duration: 1000 },
    { id: 'synthesizing', label: 'Verdict Synthesis', honestLabel: 'Weighing evidence to determine verdict', icon: Shield, duration: 800 },
];

// Source type icons (Senior feedback)
const SOURCE_ICONS: Record<string, string> = {
    'known_misinfo': '🚨',
    'wikidata': '📊',
    'wikipedia': '📚',
    'fact_check': '✅',
    'news_article': '📰',
    'academic_paper': '🔬',
    'web_search': '🌐',
    'archive': '📁',
    'social_media': '💬',
};

const SOURCE_LABELS: Record<string, string> = {
    'known_misinfo': 'Verified Database',
    'wikidata': 'Structured Data',
    'wikipedia': 'Encyclopedia',
    'fact_check': 'Fact-Check',
    'news_article': 'News',
    'academic_paper': 'Academic',
    'web_search': 'Web Source',
    'archive': 'Archive',
    'social_media': 'Social',
};

// Verdict styling based on confidence (Senior feedback: tie intensity to confidence)
const getVerdictStyle = (verdict: VerdictType, confidence: number) => {
    const isHighConfidence = confidence >= 0.7;
    const isMedConfidence = confidence >= 0.4;

    switch (verdict) {
        case 'verified_true':
            return {
                bg: isHighConfidence ? 'bg-emerald-500/20' : 'bg-emerald-500/10',
                border: isHighConfidence ? 'border-emerald-400' : 'border-emerald-500/50',
                text: 'text-emerald-400',
                icon: CheckCircle2,
                label: 'Verified True',
                glow: isHighConfidence ? 'shadow-[0_0_30px_rgba(16,185,129,0.3)]' : '',
            };
        case 'verified_false':
            return {
                bg: isHighConfidence ? 'bg-red-500/20' : 'bg-red-500/10',
                border: isHighConfidence ? 'border-red-400' : 'border-red-500/50',
                text: 'text-red-400',
                icon: XCircle,
                label: 'Verified False',
                glow: isHighConfidence ? 'shadow-[0_0_30px_rgba(239,68,68,0.3)]' : '',
            };
        case 'disputed':
            return {
                bg: 'bg-amber-500/15',
                border: 'border-amber-500/50',
                text: 'text-amber-400',
                icon: AlertTriangle,
                label: 'Disputed',
                glow: '',
            };
        case 'not_checkable':
            return {
                bg: 'bg-slate-500/15',
                border: 'border-slate-500/50',
                text: 'text-slate-400',
                icon: Info,
                label: 'Not Fact-Checkable',
                glow: '',
            };
        case 'insufficient_evidence':
            return {
                bg: 'bg-yellow-500/10',
                border: 'border-yellow-500/50',
                text: 'text-yellow-400',
                icon: AlertCircle,
                label: 'Insufficient Evidence',
                glow: '',
            };
        default: // unverified
            return {
                bg: isMedConfidence ? 'bg-blue-500/15' : 'bg-slate-500/10',
                border: 'border-blue-500/50',
                text: 'text-blue-400',
                icon: Clock,
                label: 'Unverified',
                glow: '',
            };
    }
};

// === Components ===

// Timeline Step Component
function TimelineStep({
    step,
    currentStep,
    completedSteps,
    isExpanded,
    onToggle,
    details
}: {
    step: TimelineStepData;
    currentStep: InvestigationStep;
    completedSteps: InvestigationStep[];
    isExpanded: boolean;
    onToggle: () => void;
    details?: string;
}) {
    const isActive = currentStep === step.id;
    const isCompleted = completedSteps.includes(step.id);
    const isPending = !isActive && !isCompleted;

    const Icon = step.icon;

    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`
                relative p-4 rounded-xl border backdrop-blur-sm cursor-pointer
                transition-all duration-300
                ${isActive ? 'bg-cyan-500/10 border-cyan-500/50' : ''}
                ${isCompleted ? 'bg-white/5 border-white/20' : ''}
                ${isPending ? 'bg-white/5 border-white/10 opacity-50' : ''}
            `}
            onClick={onToggle}
        >
            <div className="flex items-center gap-3">
                {/* Status indicator */}
                <div className={`
                    w-10 h-10 rounded-full flex items-center justify-center
                    ${isActive ? 'bg-cyan-500/20' : ''}
                    ${isCompleted ? 'bg-emerald-500/20' : ''}
                    ${isPending ? 'bg-white/5' : ''}
                `}>
                    {isActive && (
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        >
                            <Loader2 className="w-5 h-5 text-cyan-400" />
                        </motion.div>
                    )}
                    {isCompleted && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                    {isPending && <Icon className="w-5 h-5 text-white/40" />}
                </div>

                {/* Content */}
                <div className="flex-1">
                    <div className="flex items-center justify-between">
                        <span className={`font-medium ${isActive ? 'text-cyan-400' : isCompleted ? 'text-white' : 'text-white/50'}`}>
                            {step.label}
                        </span>
                        {(isCompleted || isActive) && (
                            isExpanded ? <ChevronUp className="w-4 h-4 text-white/50" /> : <ChevronDown className="w-4 h-4 text-white/50" />
                        )}
                    </div>
                    <p className="text-xs text-white/50 mt-0.5">{step.honestLabel}</p>
                </div>
            </div>

            {/* Expandable details (Senior feedback: interactive timeline) */}
            <AnimatePresence>
                {isExpanded && details && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="mt-3 pt-3 border-t border-white/10 text-sm text-white/70">
                            {details}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Active pulse animation (subdued for low confidence claims) */}
            {isActive && (
                <motion.div
                    className="absolute inset-0 rounded-xl border-2 border-cyan-400/50"
                    animate={{ opacity: [0.5, 0, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                />
            )}
        </motion.div>
    );
}

// Evidence Card Component
function EvidenceCard({ evidence, index }: { evidence: V3EvidenceItem; index: number }) {
    const stanceColors = {
        supports: 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400',
        refutes: 'bg-red-500/20 border-red-500/50 text-red-400',
        neutral: 'bg-slate-500/20 border-slate-500/50 text-slate-400',
    };

    const sourceIcon = SOURCE_ICONS[evidence.source_type] || '🌐';
    const sourceLabel = SOURCE_LABELS[evidence.source_type] || 'Source';

    // Trust score badge (Senior feedback: simple tooltip)
    const getTrustBadge = (score: number) => {
        if (score >= 80) return { label: 'Highly Trusted', color: 'text-emerald-400' };
        if (score >= 60) return { label: 'Generally Reliable', color: 'text-cyan-400' };
        if (score >= 40) return { label: 'Mixed Reliability', color: 'text-amber-400' };
        return { label: 'Low Trust', color: 'text-red-400' };
    };

    const trustBadge = getTrustBadge(evidence.trust_score);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.15 }}
            className="p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
        >
            {/* Header */}
            <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-lg">{sourceIcon}</span>
                    <div>
                        <span className="text-sm font-medium text-white">{evidence.source_domain}</span>
                        <span className="text-xs text-white/40 ml-2">{sourceLabel}</span>
                    </div>
                </div>

                {/* Stance badge */}
                <div className={`px-2 py-1 rounded-full text-xs font-medium border ${stanceColors[evidence.stance]}`}>
                    {evidence.stance === 'supports' ? '✓ Supports' : evidence.stance === 'refutes' ? '✗ Refutes' : '○ Neutral'}
                </div>
            </div>

            {/* Content */}
            <p className="text-sm text-white/70 mb-3 line-clamp-2">
                {evidence.text_preview}
            </p>

            {/* Footer */}
            <div className="flex items-center justify-between text-xs">
                {/* Trust score with tooltip (Senior feedback) */}
                <span
                    className={trustBadge.color}
                    title={`Trust Score: ${evidence.trust_score}/100 - ${trustBadge.label}`}
                >
                    Trust: {evidence.trust_score}% • {trustBadge.label}
                </span>

                {evidence.source_url && (
                    <a
                        href={evidence.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300"
                    >
                        View <ExternalLink className="w-3 h-3" />
                    </a>
                )}
            </div>
        </motion.div>
    );
}

// Not Checkable Educational Display (Senior feedback: teaching, not rejection)
function NotCheckableDisplay({ claimType, text }: { claimType: string; text: string }) {
    const explanations: Record<string, { title: string; description: string; tip: string }> = {
        opinion: {
            title: '💭 This appears to be an Opinion',
            description: 'Opinions and value judgments express personal preferences or beliefs. They cannot be objectively verified as true or false.',
            tip: 'Try rephrasing as a factual claim, e.g., "Studies show X is better than Y"',
        },
        prediction: {
            title: '🔮 This appears to be a Prediction',
            description: 'Predictions about future events cannot be verified until they occur. We cannot fact-check what hasn\'t happened yet.',
            tip: 'Check back after the predicted date, or search for expert forecasts on this topic.',
        },
        question: {
            title: '❓ This appears to be a Question',
            description: 'Questions ask for information rather than making claims. To fact-check, we need an assertion.',
            tip: 'Convert your question to a statement, e.g., "Is X true?" → "X is true"',
        },
        command: {
            title: '👆 This appears to be a Command',
            description: 'Commands or instructions tell someone what to do. They don\'t make factual claims that can be verified.',
            tip: 'If this relates to a factual claim, try phrasing it as a statement.',
        },
        hypothetical: {
            title: '🤔 This appears to be a Hypothetical',
            description: 'Hypothetical scenarios ("what if...") explore possibilities rather than making factual claims.',
            tip: 'Try focusing on a specific, verifiable aspect of your hypothetical.',
        },
        unknown: {
            title: '🔍 Unable to Classify',
            description: 'We couldn\'t determine the type of this statement. It may be too ambiguous or complex.',
            tip: 'Try simplifying your input or breaking it into smaller, clearer claims.',
        },
    };

    const info = explanations[claimType] || explanations.unknown;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-6 rounded-2xl bg-gradient-to-br from-slate-500/10 to-slate-600/5 border border-slate-500/30"
        >
            <h3 className="text-xl font-medium mb-3">{info.title}</h3>
            <p className="text-white/70 mb-4">{info.description}</p>

            <div className="flex items-start gap-2 p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                <Lightbulb className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
                <div>
                    <span className="text-sm font-medium text-cyan-400">Tip:</span>
                    <p className="text-sm text-white/70 mt-1">{info.tip}</p>
                </div>
            </div>

            <div className="mt-4 p-3 rounded-lg bg-white/5">
                <span className="text-xs text-white/50">Your input:</span>
                <p className="text-sm text-white/70 mt-1">"{text}"</p>
            </div>
        </motion.div>
    );
}

// Confidence Meter with Context (Senior feedback)
function ConfidenceMeter({ confidence, verdict }: { confidence: number; verdict: VerdictType }) {
    const percentage = Math.round(confidence * 100);
    const verdictStyle = getVerdictStyle(verdict, confidence);

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
                <span className="text-white/70">Evidence Confidence</span>
                <span className={verdictStyle.text}>{percentage}%</span>
            </div>

            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className={`h-full rounded-full ${verdict === 'verified_true' ? 'bg-emerald-500' :
                        verdict === 'verified_false' ? 'bg-red-500' :
                            verdict === 'disputed' ? 'bg-amber-500' :
                                'bg-cyan-500'
                        }`}
                />
            </div>

            {/* Context label (Senior feedback: explain what confidence means) */}
            <p className="text-xs text-white/40 italic">
                Based on evidence consistency, not absolute truth
            </p>
        </div>
    );
}

// === Main Component ===
export function InvestigationPage() {
    const [inputText, setInputText] = useState('');
    const [currentStep, setCurrentStep] = useState<InvestigationStep>('idle');
    const [completedSteps, setCompletedSteps] = useState<InvestigationStep[]>([]);
    const [expandedStep, setExpandedStep] = useState<InvestigationStep | null>(null);
    const [stepDetails, setStepDetails] = useState<Record<InvestigationStep, string>>({} as any);
    const [_result, setResult] = useState<V3InvestigateResponse | null>(null);
    const [primaryClaim, setPrimaryClaim] = useState<V3VerifiedClaim | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Simulate staged investigation (Senior feedback: artificial delays)
    const runStagedInvestigation = useCallback(async () => {
        if (!inputText.trim()) return;

        setError(null);
        setResult(null);
        setPrimaryClaim(null);
        setCompletedSteps([]);
        setStepDetails({} as any);

        // Start API request in background
        const apiPromise = investigateClaim(inputText);

        // Run through timeline steps with minimum delays
        for (const step of TIMELINE_STEPS) {
            setCurrentStep(step.id);

            // Wait minimum duration for UX pacing
            await new Promise(resolve => setTimeout(resolve, step.duration));

            // Add to completed
            setCompletedSteps(prev => [...prev, step.id]);
            setStepDetails(prev => ({ ...prev, [step.id]: `Completed in ${step.duration}ms` }));
        }

        // Wait for API response
        try {
            const response = await apiPromise;
            setResult(response);

            // Extract primary claim from verified_claims array
            const claim = response.verified_claims?.[0] || null;
            setPrimaryClaim(claim);
            setCurrentStep('complete');

            // Update step details with actual results
            if (claim) {
                setStepDetails(prev => ({
                    ...prev,
                    extracting: `Detected claim type: ${claim.claim_type}`,
                    searching_web: `Found ${claim.evidence_count} sources`,
                    synthesizing: `Verdict: ${claim.verdict} (${Math.round(claim.confidence * 100)}% confidence)`,
                }));
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Investigation failed');
            setCurrentStep('error');
        }
    }, [inputText]);

    const handleReset = () => {
        setInputText('');
        setCurrentStep('idle');
        setCompletedSteps([]);
        setExpandedStep(null);
        setStepDetails({} as any);
        setResult(null);
        setPrimaryClaim(null);
        setError(null);
    };

    const isInvestigating = currentStep !== 'idle' && currentStep !== 'complete' && currentStep !== 'error';

    return (
        <div className="min-h-screen pt-20 pb-12 px-4 md:px-8">
            {/* Background effects */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-40 left-1/4 w-[500px] h-[500px] bg-cyan-500/5 rounded-full blur-[140px]" />
                <div className="absolute bottom-40 right-1/4 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-[140px]" />
            </div>

            <div className="relative z-10 max-w-6xl mx-auto">
                {/* Header */}
                <div className="text-center mb-10">
                    <motion.h1
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent"
                    >
                        TruthLens Investigation
                    </motion.h1>
                    <p className="text-white/60">Watch the verification process unfold in real-time</p>
                </div>

                {/* Input Section */}
                {currentStep === 'idle' && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="max-w-2xl mx-auto mb-10"
                    >
                        <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
                            <label className="block text-sm text-white/60 mb-3">
                                Enter a claim to investigate
                            </label>
                            <textarea
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                placeholder="e.g., 'COVID vaccines cause autism' or 'New Delhi is the capital of India'"
                                className="w-full h-32 px-4 py-3 rounded-xl bg-white/5 border border-white/10 
                                         focus:border-cyan-500/50 focus:outline-none resize-none text-white
                                         placeholder:text-white/30"
                            />
                            <button
                                onClick={runStagedInvestigation}
                                disabled={!inputText.trim()}
                                className="w-full mt-4 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 
                                         text-black font-medium hover:shadow-[0_0_30px_rgba(6,182,212,0.3)]
                                         disabled:opacity-50 disabled:cursor-not-allowed transition-all
                                         flex items-center justify-center gap-2"
                            >
                                <Search className="w-5 h-5" />
                                Start Investigation
                            </button>
                        </div>
                    </motion.div>
                )}

                {/* Investigation in Progress */}
                {(isInvestigating || currentStep === 'complete' || currentStep === 'error') && (
                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Left: Timeline */}
                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-medium">Investigation Timeline</h2>
                                {currentStep === 'complete' && (
                                    <button
                                        onClick={handleReset}
                                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 
                                                 border border-white/10 hover:bg-white/10 text-sm"
                                    >
                                        <RotateCcw className="w-4 h-4" />
                                        New Search
                                    </button>
                                )}
                            </div>

                            <div className="space-y-3">
                                {TIMELINE_STEPS.map((step) => (
                                    <TimelineStep
                                        key={step.id}
                                        step={step}
                                        currentStep={currentStep}
                                        completedSteps={completedSteps}
                                        isExpanded={expandedStep === step.id}
                                        onToggle={() => setExpandedStep(expandedStep === step.id ? null : step.id)}
                                        details={stepDetails[step.id]}
                                    />
                                ))}
                            </div>

                            {/* Claim being investigated */}
                            <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/10">
                                <span className="text-xs text-white/50">Investigating:</span>
                                <p className="text-sm text-white/80 mt-1">"{inputText}"</p>
                            </div>
                        </div>

                        {/* Right: Results */}
                        <div>
                            {/* Error State */}
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="p-6 rounded-2xl bg-red-500/10 border border-red-500/30"
                                >
                                    <div className="flex items-center gap-3 mb-3">
                                        <XCircle className="w-8 h-8 text-red-400" />
                                        <h3 className="text-xl font-medium text-red-400">Investigation Failed</h3>
                                    </div>
                                    <p className="text-white/70 mb-4">{error}</p>
                                    <button
                                        onClick={runStagedInvestigation}
                                        className="px-4 py-2 rounded-lg bg-red-500/20 border border-red-500/30 
                                                 hover:bg-red-500/30 text-red-400"
                                    >
                                        Retry Investigation
                                    </button>
                                </motion.div>
                            )}

                            {/* Loading placeholder */}
                            {isInvestigating && !error && (
                                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 animate-pulse">
                                    <div className="flex items-center gap-3 mb-4">
                                        <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
                                        <span className="text-lg text-white/70">Gathering evidence...</span>
                                    </div>
                                    <div className="space-y-3">
                                        <div className="h-4 bg-white/10 rounded w-3/4" />
                                        <div className="h-4 bg-white/10 rounded w-1/2" />
                                        <div className="h-4 bg-white/10 rounded w-2/3" />
                                    </div>
                                </div>
                            )}

                            {/* Results */}
                            {primaryClaim && currentStep === 'complete' && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="space-y-4"
                                >
                                    {/* Not checkable - Educational display */}
                                    {primaryClaim.verdict === 'not_checkable' ? (
                                        <NotCheckableDisplay
                                            claimType={primaryClaim.claim_type}
                                            text={primaryClaim.original_text}
                                        />
                                    ) : (
                                        <>
                                            {/* Verdict Card (intensity tied to confidence) */}
                                            {(() => {
                                                const style = getVerdictStyle(primaryClaim.verdict as VerdictType, primaryClaim.confidence);
                                                const Icon = style.icon;
                                                return (
                                                    <motion.div
                                                        initial={{ scale: 0.9, opacity: 0 }}
                                                        animate={{ scale: 1, opacity: 1 }}
                                                        transition={{ type: "spring", damping: 15 }}
                                                        className={`p-6 rounded-2xl ${style.bg} border ${style.border} ${style.glow}`}
                                                    >
                                                        <div className="flex items-center gap-4 mb-4">
                                                            <div className={`w-14 h-14 rounded-full ${style.bg} flex items-center justify-center`}>
                                                                <Icon className={`w-8 h-8 ${style.text}`} />
                                                            </div>
                                                            <div>
                                                                <div className="text-xs text-white/50">Verdict</div>
                                                                <div className={`text-2xl font-bold ${style.text}`}>
                                                                    {style.label}
                                                                </div>
                                                            </div>
                                                        </div>

                                                        <ConfidenceMeter
                                                            confidence={primaryClaim.confidence}
                                                            verdict={primaryClaim.verdict as VerdictType}
                                                        />

                                                        <p className="mt-4 text-white/70">{primaryClaim.evidence_summary}</p>

                                                        <div className="mt-4 flex gap-4 text-xs text-white/50">
                                                            <span>{primaryClaim.sources_checked} sources checked</span>
                                                            <span>{primaryClaim.investigation_time_ms}ms</span>
                                                        </div>
                                                    </motion.div>
                                                );
                                            })()}

                                            {/* Evidence Cards */}
                                            {primaryClaim.evidence && primaryClaim.evidence.length > 0 && (
                                                <div>
                                                    <h3 className="text-lg font-medium mb-3">Evidence Found</h3>
                                                    <div className="space-y-3">
                                                        {primaryClaim.evidence.map((ev: V3EvidenceItem, i: number) => (
                                                            <EvidenceCard key={i} evidence={ev} index={i} />
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </>
                                    )}

                                    {/* Disclaimer */}
                                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex gap-3">
                                        <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
                                        <p className="text-xs text-white/60">
                                            <span className="text-amber-400 font-medium">Advisory Notice:</span> This is an automated assessment based on available evidence.
                                            Always verify critical information from multiple trusted sources.
                                        </p>
                                    </div>
                                </motion.div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

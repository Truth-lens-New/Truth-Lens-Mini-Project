
import { Shield, Landmark, Microscope, Zap, Database, Globe } from 'lucide-react';
import { motion } from 'framer-motion';

export type ClaimType =
    | 'scientific_medical'
    | 'political_allegation'
    | 'breaking_event'
    | 'statistical_claim'
    | 'factual_statement'
    | 'opinion'
    | 'rumor_debunk'
    | 'scheme_scam'
    | 'fact';

interface StrategyBadgeProps {
    claimType: string;
    stats?: Record<string, any>;
    className?: string;
}

export function StrategyBadge({ claimType, stats, className = '' }: StrategyBadgeProps) {
    if (!stats) return null;

    // Configuration for each strategy type
    const config = {
        scientific_medical: {
            icon: Microscope,
            label: "Scientific Consensus",
            color: "text-cyan-400",
            bg: "bg-cyan-500/10",
            border: "border-cyan-500/20",
            renderStats: () => {
                const score = stats.consensus_score ? Math.round(stats.consensus_score * 100) : 0;
                return (
                    <div className="flex items-center gap-2">
                        <span className="font-bold text-lg">{score}%</span>
                        <span className="text-xs opacity-70">Scientific Agreement</span>
                    </div>
                );
            }
        },
        political_allegation: {
            icon: Landmark,
            label: "Political Analysis",
            color: "text-amber-400",
            bg: "bg-amber-500/10",
            border: "border-amber-500/20",
            renderStats: () => {
                const count = stats.official_sources || 0;
                return (
                    <div className="flex items-center gap-2">
                        <span className="font-bold text-lg">{count}</span>
                        <span className="text-xs opacity-70">Official Records Found</span>
                    </div>
                );
            }
        },
        breaking_event: {
            icon: Zap,
            label: "Real-Time Velocity",
            color: "text-orange-400",
            bg: "bg-orange-500/10",
            border: "border-orange-500/20",
            renderStats: () => {
                const velocity = stats.velocity || 0;
                return (
                    <div className="flex items-center gap-2">
                        <span className="font-bold text-lg">{velocity}</span>
                        <span className="text-xs opacity-70">Sources / Hour</span>
                    </div>
                );
            }
        },
        factual_statement: {
            icon: Database,
            label: "Knowledge Graph",
            color: "text-purple-400",
            bg: "bg-purple-500/10",
            border: "border-purple-500/20",
            renderStats: () => (
                <div className="flex items-center gap-2">
                    <span className="text-xs">Verified via Wikidata</span>
                </div>
            )
        },
        rumor_debunk: {
            icon: Shield,
            label: "Rumor Shield",
            color: "text-emerald-400",
            bg: "bg-emerald-500/10",
            border: "border-emerald-500/20",
            renderStats: () => (
                <div className="flex items-center gap-2">
                    <span className="text-xs">Matched Fact Check DB</span>
                </div>
            )
        },
        default: {
            icon: Globe,
            label: "Web Analysis",
            color: "text-blue-400",
            bg: "bg-blue-500/10",
            border: "border-blue-500/20",
            renderStats: () => null
        }
    };

    // Determine which config to use
    // Mapping backend claim types to frontend config keys
    // Some backend types might need normalization
    const typeKey = (claimType in config) ? claimType as keyof typeof config : 'default';
    const activeConfig = config[typeKey];
    const Icon = activeConfig.icon;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex items-center gap-4 p-4 rounded-xl backdrop-blur-sm border ${activeConfig.bg} ${activeConfig.border} ${className}`}
        >
            <div className={`p-3 rounded-full bg-white/5 ${activeConfig.color}`}>
                <Icon className="w-6 h-6" />
            </div>

            <div className="flex flex-col">
                <span className={`text-xs font-bold uppercase tracking-widest mb-1 ${activeConfig.color}`}>
                    {activeConfig.label}
                </span>
                <div className="text-foreground">
                    {activeConfig.renderStats()}
                </div>
            </div>

            {/* Pulsing indicator for breaking events */}
            {typeKey === 'breaking_event' && (
                <div className="ml-auto relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-orange-500"></span>
                </div>
            )}
        </motion.div>
    );
}

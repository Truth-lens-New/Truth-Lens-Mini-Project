import { motion } from "framer-motion";

interface HybridTruthGaugeProps {
    score: number; // 0 (False) to 1 (True)
    confidence: number; // 0 to 1
    evidenceCount: number;
}

const clamp = (n: number, min = 0, max = 1) => Math.min(Math.max(n, min), max);

export function HybridTruthGauge({
    score,
    confidence,
    evidenceCount,
}: HybridTruthGaugeProps) {
    const safeScore = clamp(score);
    const safeConfidence = clamp(confidence);
    const position = safeScore * 100;
    const confidencePct = Math.round(safeConfidence * 100);

    const getColor = (s: number) => {
        if (s >= 0.65) return "bg-emerald-500";
        if (s <= 0.35) return "bg-red-500";
        return "bg-amber-500";
    };

    const activeColorClass = getColor(safeScore);

    return (
        <div className="w-full mt-8 mb-6" role="meter" aria-label="Truth confidence gauge">
            {/* Minimalist Legend */}
            <div className="flex justify-between text-xs font-medium text-muted-foreground uppercase tracking-widest mb-4">
                <span>False</span>
                <span>Uncertain</span>
                <span>True</span>
            </div>

            {/* Flat Track */}
            <div className="relative h-2 rounded-full bg-secondary overflow-hidden">
                {/* Zones (Subtle) */}
                <div className="absolute inset-0 flex opacity-20">
                    <div className="w-[35%] bg-red-500/50" />
                    <div className="w-[30%] bg-amber-500/50" />
                    <div className="w-[35%] bg-emerald-500/50" />
                </div>
            </div>

            {/* Position Indicator */}
            <div className="relative -mt-3.5 h-6">
                <motion.div
                    initial={{ left: "50%" }}
                    animate={{ left: `${position}%` }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                    className="absolute top-0 -translate-x-1/2 flex flex-col items-center"
                >
                    {/* Minimalist Handle */}
                    <div className={`w-4 h-4 rounded-full border-[3px] border-background shadow-sm ${activeColorClass}`} />

                    {/* Confidence Label */}
                    <div className="mt-2 px-3 py-1 rounded-md bg-secondary border border-border/50 text-xs font-bold text-foreground shadow-sm whitespace-nowrap">
                        {confidencePct}% Confidence
                    </div>
                </motion.div>
            </div>

            {/* Source Count */}
            <div className="text-center mt-8 text-xs text-muted-foreground">
                Verified against <span className="font-semibold text-foreground">{evidenceCount} sources</span>
            </div>
        </div>
    );
}

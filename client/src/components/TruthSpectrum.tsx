import { motion } from 'framer-motion';

interface TruthSpectrumProps {
    score: number; // 0 (False) to 1 (True)
    confidence: number;
    evidenceCount: number;
}

export function TruthSpectrum({ score, confidence, evidenceCount }: TruthSpectrumProps) {
    // Calculate position (0 to 100%)
    const position = score * 100;

    return (
        <div className="w-full mt-8 mb-4">
            <div className="flex justify-between text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">
                <span>Falsehood</span>
                <span>Disputed</span>
                <span>Truth</span>
            </div>

            <div className="relative h-6 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 opacity-80 shadow-lg">
                {/* Spectrum Marker */}
                <motion.div
                    initial={{ left: '50%' }}
                    animate={{ left: `${position}%` }}
                    transition={{ type: 'spring', stiffness: 50, damping: 20 }}
                    className="absolute top-1/2 -translate-y-1/2 w-8 h-8 rounded-full border-4 border-white dark:border-gray-900 shadow-xl z-10 flex items-center justify-center transform -translate-x-1/2"
                    style={{
                        background: position > 66 ? '#10b981' : position > 33 ? '#eab308' : '#ef4444'
                    }}
                >
                    <div className="w-2 h-2 rounded-full bg-white" />
                </motion.div>

                {/* Evidence Dots (Simulated for visual effect) */}
                {Array.from({ length: evidenceCount }).map((_, i) => (
                    <div
                        key={i}
                        className="absolute top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-white/40"
                        style={{
                            left: `${Math.min(100, Math.max(0, position + (Math.random() * 20 - 10)))}%`
                        }}
                    />
                ))}
            </div>

            <div className="text-center mt-3 text-xs text-muted-foreground">
                <span className="font-semibold text-foreground">{evidenceCount} sources</span> plotted ({Math.round(confidence * 100)}% confidence)
            </div>
        </div>
    );
}

import { useRef, useMemo } from 'react';
import { motion, useScroll, useTransform, useSpring, MotionValue } from 'framer-motion';

type GlyphType = "verified" | "misinfo" | "neutral";

export function FinalHybridStoryComponent() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start end", "end start"]
    });

    // SLOWER physics for smoother, longer animations (stiffness 40 = more gradual)
    const smoothProgress = useSpring(scrollYProgress, { stiffness: 40, damping: 20, restDelta: 0.001 });

    // --- ANIMATION VALUES ---

    // Background headlines fade gradually
    const opacityHeadlines = useTransform(smoothProgress, [0, 0.25], [0.5, 0]);

    // Phase 1: "The Noise is Deafening" - LONGER visible duration with smooth fade
    const opacity1 = useTransform(smoothProgress, [0.05, 0.12, 0.30, 0.40], [0, 1, 1, 0]);
    const scale1 = useTransform(smoothProgress, [0.05, 0.15], [0.92, 1]);
    const blur1 = useTransform(smoothProgress, [0.30, 0.40], ["0px", "8px"]);

    // Phase 2: "Separating Lies from Truth" - LONGER middle phase with overlap
    const opacity2 = useTransform(smoothProgress, [0.35, 0.45, 0.58, 0.68], [0, 1, 1, 0]);
    const scale2 = useTransform(smoothProgress, [0.35, 0.45], [0.92, 1]);
    const y2 = useTransform(smoothProgress, [0.35, 0.68], [50, -50]);

    // Phase 3: "We Bring Focus" - Fades in smoothly, stays visible
    const opacity3 = useTransform(smoothProgress, [0.62, 0.78], [0, 1]);
    const scale3 = useTransform(smoothProgress, [0.62, 0.78], [0.92, 1]);

    // Transition beam scanning effect
    const beamProgress = useTransform(smoothProgress, [0.55, 0.78], ["-20%", "120%"]);
    const beamOpacity = useTransform(smoothProgress, [0.55, 0.60, 0.75, 0.80], [0, 0.7, 0.7, 0]);

    // Dim particles when text is active - smooth multi-stage
    const particleOpacity = useTransform(smoothProgress, [0.05, 0.15, 0.30, 0.45, 0.62, 0.80], [1, 0.5, 0.5, 0.4, 0.4, 0.7]);

    return (
        <section ref={containerRef} className="h-[600vh] relative z-10 bg-background text-foreground transition-colors duration-300 font-['Space_Grotesk']">
            <div className="sticky top-0 h-screen w-full flex items-center justify-center overflow-hidden perspective-[1000px]">

                {/* 1. CHAOTIC PARTICLES - Core chaos-to-order effect */}
                <motion.div style={{ opacity: particleOpacity }} className="absolute inset-0 z-0">
                    <SmartDataCloud progress={smoothProgress} />
                </motion.div>

                {/* 2. BACKGROUND TEXTURE - Scrolling headlines */}
                <FakeHeadlines opacity={opacityHeadlines} />

                {/* 3. TRANSITION BEAM - Scanning effect */}
                <motion.div
                    style={{ top: beamProgress, opacity: beamOpacity }}
                    className="absolute left-0 w-full h-[18vh] z-20 pointer-events-none"
                >
                    <div className="w-full h-full bg-gradient-to-b from-transparent via-emerald-500/25 to-transparent border-b border-emerald-500/50" />
                </motion.div>

                {/* 4. CONTENT LAYER - Text cards with proper centering */}
                <div className="relative z-30 w-full h-full flex items-center justify-center">

                    {/* Phase 1: "The Noise is Deafening" */}
                    <motion.div
                        style={{ opacity: opacity1, scale: scale1, filter: useTransform(blur1, b => `blur(${b})`) }}
                        className="absolute inset-0 flex items-center justify-center p-6"
                    >
                        <div className="max-w-3xl w-full px-10 py-12 md:px-16 md:py-16 rounded-3xl bg-white/90 dark:bg-zinc-900/90 backdrop-blur-2xl border border-zinc-200/80 dark:border-zinc-700/60 shadow-[0_16px_100px_rgba(0,0,0,0.18)] dark:shadow-[0_16px_100px_rgba(0,0,0,0.6)]">
                            <h2 className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight text-zinc-900 dark:text-zinc-100 text-center leading-tight">
                                THE NOISE IS
                                <span className="block mt-2 font-serif italic font-light text-zinc-600 dark:text-zinc-300">
                                    DEAFENING.
                                </span>
                            </h2>
                        </div>
                    </motion.div>

                    {/* Phase 2: "Separating Lies from Truth" */}
                    <motion.div
                        style={{ opacity: opacity2, scale: scale2, y: y2 }}
                        className="absolute inset-0 flex items-center justify-center p-6"
                    >
                        <div className="max-w-3xl w-full px-10 py-12 md:px-16 md:py-16 rounded-3xl bg-white/90 dark:bg-zinc-900/90 backdrop-blur-2xl border border-zinc-200/80 dark:border-zinc-700/60 shadow-[0_16px_100px_rgba(0,0,0,0.18)] dark:shadow-[0_16px_100px_rgba(0,0,0,0.6)]">
                            <h2 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 text-center leading-tight">
                                SEPARATING
                                <span className="block mt-2">
                                    <span className="font-serif italic text-red-600/80 dark:text-red-400/80">LIES</span>
                                    <span className="mx-3 text-zinc-500 dark:text-zinc-400">FROM</span>
                                    <span className="font-serif italic text-emerald-600 dark:text-emerald-400">TRUTH</span>
                                </span>
                            </h2>
                        </div>
                    </motion.div>

                    {/* Phase 3: "We Bring Focus" */}
                    <motion.div
                        style={{ opacity: opacity3, scale: scale3 }}
                        className="absolute inset-0 flex items-center justify-center p-6"
                    >
                        <div className="max-w-3xl w-full px-10 py-12 md:px-16 md:py-16 rounded-3xl bg-white/90 dark:bg-zinc-900/90 backdrop-blur-2xl border border-zinc-200/80 dark:border-zinc-700/60 shadow-[0_16px_100px_rgba(0,0,0,0.18)] dark:shadow-[0_16px_100px_rgba(0,0,0,0.6)]">
                            <h2 className="text-4xl sm:text-5xl md:text-7xl font-black tracking-tight text-zinc-900 dark:text-zinc-100 text-center leading-tight">
                                WE BRING
                                <span className="block mt-2 text-emerald-600 dark:text-emerald-400">
                                    FOCUS.
                                </span>
                            </h2>
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}

// --- SUB-COMPONENTS ---

function SmartDataCloud({ progress }: { progress: MotionValue<number> }) {
    const particles = useMemo(() => {
        const glyphs = ["0", "1", "?", "!", "≠", "§"];
        // RESTORED: 120 particles for full chaos effect
        return Array.from({ length: 120 }).map((_, i) => {
            const randomX = (Math.random() - 0.5) * 150;
            const randomY = (Math.random() - 0.5) * 150;
            const depth = Math.random();

            const col = i % 12;
            const row = Math.floor(i / 12);
            const orderX = (col - 5.5) * 8;
            const orderY = (row - 4.5) * 9;

            // CLASSIFICATION LOGIC
            let type: GlyphType = "neutral";
            if (i % 5 === 0) type = "misinfo";
            if (i % 8 === 0) type = "verified";

            return { randomX, randomY, depth, orderX, orderY, type, char: glyphs[i % glyphs.length] };
        });
    }, []);

    return (
        <div className="absolute inset-0 flex items-center justify-center perspective-[1000px] z-0">
            {particles.map((p, i) => (
                <SmartParticle key={i} data={p} progress={progress} />
            ))}
        </div>
    );
}

function SmartParticle({ data, progress }: { data: any; progress: MotionValue<number> }) {
    const size = 1 + (data.depth * 1.4);

    // Position: CHAOS to ORDER - scattered to structured grid (SLOW transition from 0.12 to 0.88)
    const x = useTransform(progress, [0.12, 0.88], [`${data.randomX}vw`, `${data.orderX}vw`]);
    const y = useTransform(progress, [0.12, 0.88], [`${data.randomY}vh`, `${data.orderY}vh`]);
    const z = useTransform(progress, [0.12, 0.88], [data.depth * -500, 0]);

    const isMisinfo = data.type === "misinfo";
    const isVerified = data.type === "verified";

    // Dynamic colors based on scroll progress
    const color = useTransform(progress, [0.35, 0.85],
        isMisinfo ? ["#ef4444", "#ef444450"] : // Red fades out
            isVerified ? ["#34d399", "#34d399"] : // Green stays strong
                ["var(--muted-foreground)", "var(--foreground)"]
    );

    // Opacity: misinformation fades, truth strengthens
    const opacity = useTransform(progress, [0.35, 0.90],
        isMisinfo ? [0.9, 0.1] :
            isVerified ? [0.85, 1] :
                [0.75, 0.35]
    );

    // Scale: verified particles grow significantly
    const scale = useTransform(progress, [0.60, 0.92],
        isVerified ? [size, size * 2] : [size, size]
    );

    return (
        <motion.span
            style={{ x, y, z, scale, opacity, color }}
            className={`absolute font-mono font-bold select-none text-lg md:text-xl ${isVerified ? 'drop-shadow-[0_0_12px_rgba(52,211,153,0.9)]' : ''}`}
        >
            {data.char}
        </motion.span>
    );
}

function FakeHeadlines({ opacity }: { opacity: MotionValue<number> }) {
    const headlines = [
        "BREAKING: False Claims Circulate",
        "VIRAL: Manipulated Media Detected",
        "ANALYSIS: Source Unverified",
        "ALERT: Context Missing"
    ];

    return (
        <motion.div style={{ opacity }} className="absolute inset-0 overflow-hidden pointer-events-none z-0">
            {[1, 2, 3].map((row) => (
                <motion.div
                    key={row}
                    className="absolute whitespace-nowrap text-xs md:text-sm font-mono text-red-500/15 dark:text-red-500/25"
                    style={{ top: `${row * 25}%` }}
                    animate={{ x: row % 2 === 0 ? ['0%', '-50%'] : ['-50%', '0%'] }}
                    transition={{ duration: 50 + row * 12, repeat: Infinity, ease: "linear" }}
                >
                    {Array(5).fill(headlines).flat().map((h, i) => (
                        <span key={i} className="mx-10">{h}</span>
                    ))}
                </motion.div>
            ))}
        </motion.div>
    );
}

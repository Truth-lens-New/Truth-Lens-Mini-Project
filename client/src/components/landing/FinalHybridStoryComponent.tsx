import { useRef, useMemo } from 'react';
import { motion, useScroll, useTransform, useSpring, MotionValue } from 'framer-motion';

type GlyphType = "verified" | "misinfo" | "neutral";

export function FinalHybridStoryComponent() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start end", "end start"]
    });

    // 1. ANCHOR: Slower physics (Stiffness 50 instead of 100)
    const smoothProgress = useSpring(scrollYProgress, { stiffness: 50, damping: 20, restDelta: 0.001 });

    // --- ANIMATION VALUES ---

    // Background fades earlier
    const opacityHeadlines = useTransform(smoothProgress, [0, 0.25], [0.6, 0]);

    // Phase 1: Noise - sharper text, less blur
    // SHIFTED: Starts at 0.15 (fully on screen) instead of 0.05
    const opacity1 = useTransform(smoothProgress, [0.15, 0.3], [1, 0]);
    const blur1 = useTransform(smoothProgress, [0.15, 0.3], ["0px", "8px"]);
    const scale1 = useTransform(smoothProgress, [0.15, 0.3], [1, 1.1]);

    // Phase 2: Scattered
    // SHIFTED: Starts at 0.35
    const opacity2 = useTransform(smoothProgress, [0.35, 0.55, 0.65], [0, 1, 0]);
    const y2 = useTransform(smoothProgress, [0.35, 0.65], [50, -50]);

    // Phase 3: Focus
    // SHIFTED: Starts at 0.75
    const opacity3 = useTransform(smoothProgress, [0.75, 0.95], [0, 1]);
    const scale3 = useTransform(smoothProgress, [0.75, 0.95], [1.1, 1]);

    // Beam Transition
    const beamProgress = useTransform(smoothProgress, [0.7, 0.9], ["-20%", "120%"]);
    const beamOpacity = useTransform(smoothProgress, [0.7, 0.75, 0.9, 0.95], [0, 1, 1, 0]);

    // Dim background particles when text is focusing
    const particleOpacity = useTransform(smoothProgress, [0.3, 0.6, 0.75], [1, 0.5, 1]);

    return (
        <section ref={containerRef} className="h-[600vh] relative z-10 bg-background text-foreground transition-colors duration-300 font-['Space_Grotesk']">
            <div className="sticky top-0 h-screen w-full flex items-center justify-center overflow-hidden perspective-[1000px]">

                {/* 1. PARTICLES */}
                <motion.div style={{ opacity: particleOpacity }} className="absolute inset-0 z-0">
                    <SmartDataCloud progress={smoothProgress} />
                </motion.div>

                {/* 2. BACKGROUND TEXTURE */}
                <FakeHeadlines opacity={opacityHeadlines} />

                {/* 3. TRANSITION BEAM */}
                <motion.div
                    style={{ top: beamProgress, opacity: beamOpacity }}
                    className="absolute left-0 w-full h-[20vh] z-20 pointer-events-none"
                >
                    <div className="w-full h-full bg-gradient-to-b from-transparent via-primary/30 to-transparent border-b-2 border-primary/60 shadow-[0_0_30px_rgba(var(--primary),0.3)]" />
                </motion.div>

                {/* 4. CONTENT LAYER */}
                <div className="relative z-30 text-center w-full max-w-5xl px-6 pointer-events-none mix-blend-normal">

                    {/* Phase 1: "The Noise is Deafening" */}
                    <motion.div
                        style={{ opacity: opacity1, filter: useTransform(blur1, b => `blur(${b})`), scale: scale1 }}
                        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full p-12 rounded-[2rem] backdrop-blur-md bg-white/40 dark:bg-black/40 border border-white/20 dark:border-white/10 shadow-2xl"
                    >
                        <h2 className="text-6xl md:text-9xl font-black tracking-tighter text-zinc-900 dark:text-white drop-shadow-sm">
                            THE NOISE IS<br /><span className="font-serif italic font-light">DEAFENING.</span>
                        </h2>
                    </motion.div>

                    {/* Phase 2: "Separating Lies from Truth" */}
                    <motion.div
                        style={{ opacity: opacity2, y: y2 }}
                        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full p-12 rounded-[2rem] backdrop-blur-md bg-white/40 dark:bg-black/40 border border-white/20 dark:border-white/10 shadow-2xl"
                    >
                        <h2 className="text-5xl md:text-7xl font-bold tracking-tight mb-4 text-zinc-900 dark:text-white">
                            SEPARATING <span className="font-serif italic text-red-600 dark:text-red-500">LIES</span> FROM <span className="font-serif italic text-emerald-600 dark:text-emerald-500">TRUTH</span>.
                        </h2>
                    </motion.div>

                    {/* Phase 3: "We Bring Focus" */}
                    <motion.div
                        style={{ opacity: opacity3, scale: scale3 }}
                        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full p-12 rounded-[2rem] backdrop-blur-md bg-white/40 dark:bg-black/40 border border-white/20 dark:border-white/10 shadow-2xl"
                    >
                        <h2 className="text-7xl md:text-[8rem] font-black tracking-tighter leading-none text-zinc-900 dark:text-white">
                            WE BRING
                            <br />
                            <span className="text-emerald-600 dark:text-[#00FFC3]">FOCUS.</span>
                        </h2>
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
        return Array.from({ length: 120 }).map((_, i) => {
            const randomX = (Math.random() - 0.5) * 120;
            const randomY = (Math.random() - 0.5) * 120;
            const depth = Math.random();

            const col = i % 12;
            const row = Math.floor(i / 12);
            const orderX = (col - 5.5) * 8;
            const orderY = (row - 4.5) * 8;

            // CLASSIFICATION LOGIC
            let type: GlyphType = "neutral";
            if (i % 5 === 0) type = "misinfo"; // 20% lies
            if (i % 8 === 0) type = "verified"; // 12% truth (rarer)

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

function SmartParticle({ data, progress }: any) {
    const size = 1 + (data.depth * 1.5);

    // Position
    const x = useTransform(progress, [0.2, 0.8], [`${data.randomX}vw`, `${data.orderX}vw`]);
    const y = useTransform(progress, [0.2, 0.8], [`${data.randomY}vh`, `${data.orderY}vh`]);
    const z = useTransform(progress, [0.2, 0.8], [data.depth * -500, 0]);

    // Appearance State logic
    const isMisinfo = data.type === "misinfo";
    const isVerified = data.type === "verified";

    const color = useTransform(progress, [0.5, 0.9],
        isMisinfo ? ["#ef4444", "#ef4444"] : // Red stays red
            isVerified ? ["#34d399", "#34d399"] : // Green stays green
                ["var(--muted-foreground)", "var(--foreground)"] // Grey turns to text color OR fades
    );

    const opacity = useTransform(progress, [0.5, 0.9],
        isMisinfo ? [0.8, 0.1] : // Lies fade out!
            isVerified ? [1, 1] :    // Truth stays strong
                [1, 0.3]                 // Neutral: Start clear then fade to allow text focus
    );

    const scale = useTransform(progress, [0.7, 0.9],
        isVerified ? [size, size * 2] : // Truth gets bigger
            [size, size]
    );

    return (
        <motion.span
            style={{ x, y, z, color, scale, opacity }}
            className={`absolute font-mono font-bold select-none text-xl ${isVerified ? 'drop-shadow-[0_0_8px_rgba(52,211,153,0.8)]' : ''}`}
        >
            {data.char}
        </motion.span>
    );
}

function FakeHeadlines({ opacity }: { opacity: any }) {
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
                    className="absolute whitespace-nowrap text-xs md:text-sm font-mono text-red-500/10 dark:text-red-500/20"
                    style={{ top: `${row * 25}%` }}
                    animate={{ x: row % 2 === 0 ? ['0%', '-50%'] : ['-50%', '0%'] }}
                    transition={{ duration: 40 + row * 10, repeat: Infinity, ease: "linear" }}
                >
                    {Array(4).fill(headlines).flat().map((h, i) => (
                        <span key={i} className="mx-8">{h}</span>
                    ))}
                </motion.div>
            ))}
        </motion.div>
    );
}

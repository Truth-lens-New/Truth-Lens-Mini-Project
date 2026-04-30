import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Scan, AlertTriangle } from 'lucide-react';

export function ScrollDemo() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start end", "end start"]
    });

    // 0.0–0.2  : fade the whole panel in
    // 0.3–0.6  : scan line moves top→bottom, revealing "analyzed" video above it
    // 0.6–0.7  : neural nodes pulse green
    // 0.75–0.9 : verdict card slides in from right

    const opacity = useTransform(scrollYProgress, [0, 0.2], [0, 1]);
    const scanPct = useTransform(scrollYProgress, [0.3, 0.6], [0, 100]);  // 0-100 %
    const clipPath = useTransform(scanPct, v => `inset(0 0 ${100 - v}% 0)`);
    const scanTopPct = useTransform(scanPct, v => `${v}%`);
    const nodeScale = useTransform(scrollYProgress, [0.6, 0.7], [1, 1.2]);
    const nodeColor = useTransform(scrollYProgress, [0.6, 0.7], ['#555', '#00FFC2']);
    const verdictX = useTransform(scrollYProgress, [0.75, 0.9], [80, 0]);
    const verdictOpacity = useTransform(scrollYProgress, [0.75, 0.82], [0, 1]);

    return (
        <section id="demo-section" ref={containerRef} className="h-[200vh] relative z-20">
            <div className="sticky top-0 h-screen w-full flex flex-col items-center justify-center bg-background border-y border-border/50 overflow-hidden">

                <div className="absolute top-20 text-center">
                    <h2 className="text-sm font-mono text-primary mb-2 uppercase tracking-widest">Interactive Demo</h2>
                    <h3 className="text-3xl font-bold">Scroll to Analyze</h3>
                </div>

                <motion.div
                    style={{ opacity }}
                    className="relative w-full max-w-4xl aspect-video bg-card rounded-3xl border border-border flex shadow-2xl overflow-hidden"
                >
                    {/* ── Left panel: before / after reveal ───────────────────── */}
                    <div className="w-1/2 h-full relative border-r border-border bg-black overflow-hidden">

                        {/* LAYER 1 – original video (always visible, behind everything) */}
                        <video
                            src="/sora_demo.mp4"
                            autoPlay loop muted playsInline
                            className="absolute inset-0 w-full h-full object-cover"
                        />

                        {/* LABEL: ORIGINAL — bottom of unscanned area */}
                        <motion.div
                            className="absolute left-2 z-10 flex items-center gap-1 bg-black/60 backdrop-blur-sm px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-widest text-white/50"
                            style={{ top: scanTopPct }}
                        />

                        {/* LAYER 2 – heatmap-filtered "analyzed" video, clipped ABOVE scan line */}
                        <motion.div
                            className="absolute inset-0 overflow-hidden"
                            style={{ clipPath }}
                        >
                            <video
                                src="/sora_demo.mp4"
                                autoPlay loop muted playsInline
                                className="absolute inset-0 w-full h-full object-cover"
                                style={{ filter: 'sepia(1) saturate(5) hue-rotate(-15deg) brightness(0.8)' }}
                            />
                            {/* subtle red tint overlay */}
                            <div className="absolute inset-0 bg-red-600/15 mix-blend-multiply pointer-events-none" />
                            {/* "DETECTED" stamp */}
                            <div className="absolute top-2 left-2 flex items-center gap-1 bg-red-600/90 text-white text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded">
                                <span className="w-1 h-1 rounded-full bg-white animate-pulse inline-block" />
                                Manipulation Detected
                            </div>
                        </motion.div>

                        {/* ── Scan laser line sits on top of both layers ── */}
                        <motion.div
                            className="absolute left-0 right-0 z-20 pointer-events-none"
                            style={{ top: scanTopPct }}
                        >
                            {/* laser */}
                            <div className="h-px bg-red-400 shadow-[0_0_10px_3px_rgba(255,60,60,0.7)]" />
                            {/* glow sweep downward */}
                            <div className="h-10 bg-gradient-to-b from-red-500/30 to-transparent" />
                        </motion.div>

                        {/* Filename badge bottom-left */}
                        <div className="absolute bottom-3 left-3 z-30 flex items-center gap-1.5 bg-black/70 backdrop-blur-sm px-2 py-1 rounded-md border border-white/10">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                            <span className="text-[10px] font-mono text-white/60">your_sora_holiday_video.mp4</span>
                        </div>
                    </div>

                    {/* ── Right panel: analysis dashboard ─────────────────────── */}
                    <div className="w-1/2 h-full p-8 flex flex-col gap-6 bg-secondary/5">
                        <div className="flex items-center gap-3 border-b border-border/50 pb-4">
                            <Scan className="w-5 h-5 text-primary" />
                            <span className="font-mono text-sm">TruthLens Engine</span>
                        </div>

                        {/* Neural nodes */}
                        <div className="flex justify-between px-4">
                            {[1, 2, 3, 4].map(i => (
                                <motion.div
                                    key={i}
                                    style={{ scale: nodeScale, backgroundColor: nodeColor }}
                                    className="w-3 h-3 rounded-full"
                                />
                            ))}
                        </div>

                        <div className="space-y-3 font-mono text-xs text-muted-foreground pt-4">
                            <p>{'>'} Extracting frames...</p>
                            <p>{'>'} Analyzing temporal consistency...</p>
                            <p>{'>'} Checking cross-references...</p>
                        </div>

                        {/* Verdict card */}
                        <motion.div
                            style={{ x: verdictX, opacity: verdictOpacity }}
                            className="mt-auto p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-4"
                        >
                            <div className="p-2 bg-red-500 text-white rounded-lg flex-shrink-0">
                                <AlertTriangle className="w-6 h-6" />
                            </div>
                            <div>
                                <h4 className="font-bold text-red-500">High Probability Deepfake</h4>
                                <p className="text-xs text-red-400">Lip-sync artifacts detected (98.2%)</p>
                            </div>
                        </motion.div>
                    </div>
                </motion.div>
            </div>
        </section>
    );
}

import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Scan, AlertTriangle } from 'lucide-react';

export function ScrollDemo() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start end", "end start"]
    });

    // Timeline of the demo animation
    // 0.0 - 0.3: Fade in and position the "image"
    // 0.3 - 0.6: Scanning laser moves down
    // 0.6 - 0.8: Processing nodes flash
    // 0.8 - 1.0: Verdict card slides in

    const opacity = useTransform(scrollYProgress, [0, 0.2], [0, 1]);
    const scanLineTop = useTransform(scrollYProgress, [0.3, 0.6], ["0%", "100%"]);
    const nodeScale = useTransform(scrollYProgress, [0.6, 0.7], [1, 1.2]);
    const nodeColor = useTransform(scrollYProgress, [0.6, 0.7], ["#666", "#00FFC2"]);
    const verdictX = useTransform(scrollYProgress, [0.75, 0.9], [100, 0]);
    const verdictOpacity = useTransform(scrollYProgress, [0.75, 0.8], [0, 1]);

    return (
        <section id="demo-section" ref={containerRef} className="h-[200vh] relative z-20">
            {/* Sticky container to hold the view while we scroll through the 200vh height */}
            <div className="sticky top-0 h-screen w-full flex flex-col items-center justify-center bg-background border-y border-border/50 overflow-hidden">

                <div className="absolute top-20 text-center">
                    <h2 className="text-sm font-mono text-primary mb-2 uppercase tracking-widest">Interactive Demo</h2>
                    <h3 className="text-3xl font-bold">Scroll to Analyze</h3>
                </div>

                {/* The "Device" Frame */}
                <motion.div
                    style={{ opacity }}
                    className="relative w-full max-w-4xl aspect-video bg-card rounded-3xl border border-border flex shadow-2xl overflow-hidden"
                >
                    {/* Left: Input Image (Mock) */}
                    <div className="w-1/2 h-full relative border-r border-border bg-black/5">
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-muted-foreground text-sm font-mono">Suspicious_Video.mp4</span>
                        </div>

                        {/* The Scanning Laser */}
                        <motion.div
                            style={{ top: scanLineTop }}
                            className="absolute left-0 right-0 h-1 bg-red-500 shadow-[0_0_20px_rgba(255,0,0,0.5)] z-10"
                        />
                        <motion.div
                            style={{ top: scanLineTop, height: '20%' }}
                            className="absolute left-0 right-0 bg-gradient-to-t from-red-500/20 to-transparent transform -translate-y-full pointer-events-none"
                        />
                    </div>

                    {/* Right: Analysis Dashboard */}
                    <div className="w-1/2 h-full p-8 flex flex-col gap-6 bg-secondary/5">
                        <div className="flex items-center gap-3 border-b border-border/50 pb-4">
                            <Scan className="w-5 h-5 text-primary" />
                            <span className="font-mono text-sm">TruthLens Engine</span>
                        </div>

                        {/* Neural Nodes */}
                        <div className="flex justify-between px-4">
                            {[1, 2, 3, 4].map(i => (
                                <motion.div
                                    key={i}
                                    style={{ scale: nodeScale, backgroundColor: nodeColor }}
                                    className="w-3 h-3 rounded-full bg-muted-foreground/30"
                                />
                            ))}
                        </div>

                        <div className="space-y-3 font-mono text-xs text-muted-foreground pt-4">
                            <p>{'>'} Extracting frames...</p>
                            <p>{'>'} Analyzing temporal consistency...</p>
                            <p>{'>'} Checking cross-references...</p>
                        </div>

                        {/* Verdict Card - Slides in */}
                        <motion.div
                            style={{ x: verdictX, opacity: verdictOpacity }}
                            className="mt-auto p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-4"
                        >
                            <div className="p-2 bg-red-500 text-white rounded-lg">
                                <AlertTriangle className="w-6 h-6" />
                            </div>
                            <div>
                                <h4 className="font-bold text-red-500">High Probability Deepfake</h4>
                                <p className="text-xs text-red-400">Lip-synch artifacts detected (98.2%)</p>
                            </div>
                        </motion.div>
                    </div>
                </motion.div>
            </div>
        </section>
    );
}

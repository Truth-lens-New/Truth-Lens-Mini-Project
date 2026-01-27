import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Database, Network, Share2, ShieldCheck, Zap, Globe } from 'lucide-react';

export function BentoGraph() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start end", "end start"]
    });

    // Parallax for columns
    const y1 = useTransform(scrollYProgress, [0, 1], [0, -50]);
    const y2 = useTransform(scrollYProgress, [0, 1], [50, -50]);
    const y3 = useTransform(scrollYProgress, [0, 1], [0, -100]);

    return (
        <section ref={containerRef} className="py-24 relative overflow-hidden">
            {/* Background Grid */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.02)_1px,transparent_1px)] dark:bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] opacity-50" />

            <div className="max-w-7xl mx-auto px-6 relative z-10">
                <div className="mb-16">
                    <h2 className="text-4xl font-bold tracking-tight mb-4">Core Architecture</h2>
                    <p className="text-muted-foreground max-w-2xl">
                        A dense network of autonomous agents verifying truth at the speed of information.
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[800px]">
                    {/* Column 1 - Inputs */}
                    <motion.div style={{ y: y1 }} className="space-y-6 flex flex-col">
                        <GraphCard
                            icon={Network}
                            title="Search Swarm"
                            subtitle="Distributed Crawlers"
                            stat="40k/sec"
                            color="text-[#00FFC3]"
                        />
                        <GraphCard
                            icon={Database}
                            title="Knowledge Graph"
                            subtitle="fact_checking_db"
                            stat="2.4TB"
                            color="text-blue-400"
                            tall
                        />
                    </motion.div>

                    {/* Column 2 - Processing (Center) */}
                    <motion.div style={{ y: y2 }} className="space-y-6 flex flex-col pt-12">
                        <div className="relative p-8 rounded-3xl border border-primary/20 bg-primary/5 backdrop-blur-xl flex-1 flex flex-col justify-center items-center text-center">
                            <div className="w-24 h-24 rounded-full bg-primary/20 flex items-center justify-center mb-6 animate-pulse">
                                <Zap className="w-10 h-10 text-primary" />
                            </div>
                            <h3 className="text-2xl font-bold mb-2">Neural Engine</h3>
                            <p className="text-sm text-muted-foreground mb-6">Real-time inference pipeline correlating multi-modal signals.</p>

                            {/* Connecting Lines (Visual) */}
                            <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
                                <path d="M0,50 Q150,50 300,50" className="stroke-current text-primary" fill="none" />
                                <path d="M50,0 Q50,150 50,300" className="stroke-current text-primary" fill="none" />
                            </svg>
                        </div>

                        <GraphCard
                            icon={ShieldCheck}
                            title="Crypto Verification"
                            subtitle="C2PA / ContentAuth"
                            stat="Signed"
                            color="text-green-400"
                        />
                    </motion.div>

                    {/* Column 3 - Outputs */}
                    <motion.div style={{ y: y3 }} className="space-y-6 flex flex-col">
                        <GraphCard
                            icon={Globe}
                            title="Global CDN"
                            subtitle="Edge Delivery"
                            stat="<50ms"
                            color="text-purple-400"
                        />
                        <GraphCard
                            icon={Share2}
                            title="API Gateway"
                            subtitle="REST / GraphQL"
                            stat="99.99%"
                            color="text-pink-400"
                            tall
                        />
                    </motion.div>
                </div>
            </div>
        </section>
    );
}

function GraphCard({ icon: Icon, title, subtitle, stat, color, tall }: any) {
    return (
        <div className={`group relative p-6 rounded-2xl border border-black/5 dark:border-white/10 bg-white/50 dark:bg-black/20 backdrop-blur-md hover:bg-white/80 dark:hover:bg-white/5 transition-all duration-300 ${tall ? 'flex-1' : 'h-48'} flex flex-col justify-between`}>
            {/* Glow */}
            <div className={`absolute -inset-0.5 bg-gradient-to-br from-transparent to-${color.split('-')[1]}-500/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity blur-md`} />

            <div className="relative z-10">
                <div className={`w-10 h-10 rounded-xl bg-background/50 flex items-center justify-center mb-4 ${color}`}>
                    <Icon className="w-5 h-5" />
                </div>
                <h4 className="font-bold text-lg">{title}</h4>
                <p className="text-sm text-muted-foreground">{subtitle}</p>
            </div>

            <div className="relative z-10 pt-4 border-t border-border/50 flex items-center justify-between">
                <span className="text-xs font-mono text-muted-foreground">STATUS</span>
                <span className={`text-xs font-mono font-bold ${color}`}>{stat}</span>
            </div>
        </div>
    );
}

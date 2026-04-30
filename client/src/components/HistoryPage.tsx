import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search, FileText, ChevronRight, Filter, Trash2, Clock,
    Loader2, History, Image as ImageIcon, Video as VideoIcon,
    Layers, Cpu, ShieldCheck
} from 'lucide-react';
import { getHistory, deleteHistoryItem, clearAllHistory, type HistoryItem } from '../lib/api';
import type { Page } from '../App';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { Card, CardContent } from './ui/card';
import { cn } from './ui/utils';

interface HistoryPageProps {
    onNavigate?: (page: Page) => void;
}

const getVerdictColor = (verdict?: string) => {
    if (!verdict) return 'text-muted-foreground';
    const v = verdict.toLowerCase();
    if (v.includes('false') || v.includes('fake') || v.includes('misleading')) return 'text-red-400';
    if (v.includes('true') || v.includes('real') || v.includes('verified') || v.includes('accurate')) return 'text-emerald-400';
    return 'text-amber-400';
};

const formatDate = (dateStr: string) => {
    const utcDateStr = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : `${dateStr}Z`;
    const date = new Date(utcDateStr);
    return date.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: true
    });
};

export function HistoryPage({ onNavigate }: HistoryPageProps) {
    const navigate = useNavigate();
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('text');

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await getHistory();
            let items: HistoryItem[] = [];
            if (Array.isArray(response)) {
                items = response;
            } else if (response && typeof response === 'object' && 'items' in response) {
                items = (response as { items: HistoryItem[] }).items;
            }
            setHistory(items);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load history');
            setHistory([]);
        } finally {
            setLoading(false);
        }
    };

    // Categorize data
    const { textHistory, mediaHistory } = useMemo(() => {
        const query = searchQuery.toLowerCase();
        const filtered = history.filter(item =>
            (item.claim || '').toLowerCase().includes(query) ||
            (item.verdict || '').toLowerCase().includes(query)
        );

        // Detect media items: by claim_type (new records) OR legacy deepfake pipeline markers
        const isMediaItem = (item: HistoryItem) =>
            item.claim_type === 'VISUAL_MANIPULATION' ||
            (item as any).pipeline_version === 'deepfake-v1' ||
            (item.claim || '').startsWith('Deepfake Analysis:');

        return {
            textHistory: filtered.filter(item => !isMediaItem(item)),
            mediaHistory: filtered.filter(item => isMediaItem(item))
        };
    }, [history, searchQuery]);

    const handleDelete = async (id: number) => {
        try {
            await deleteHistoryItem(id);
            setHistory(prev => prev.filter(item => item.id !== id));
            if (selectedItem?.id === id) setSelectedItem(null);
        } catch (err) {
            console.error('Failed to delete:', err);
        }
    };

    const handleClearAll = async () => {
        if (confirm('Clear all history? This cannot be undone.')) {
            try {
                await clearAllHistory();
                setHistory([]);
                setSelectedItem(null);
            } catch (err) {
                console.error('Failed to clear history:', err);
            }
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-primary mx-auto mb-4 animate-spin" />
                    <p className="text-muted-foreground">Synchronizing archive...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen pb-16">
            <div className="relative z-10 max-w-7xl mx-auto px-6 pt-8">
                {/* Header */}
                <header className="mb-10 flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-xl bg-muted/50 dark:bg-white/10 flex items-center justify-center dark:ring-1 dark:ring-white/10">
                                <History className="w-5 h-5 text-muted-foreground" />
                            </div>
                            <span className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/60">Forensic Archive</span>
                        </div>
                        <h1 className="text-4xl font-light tracking-tight text-foreground">Investigation History</h1>
                    </div>
                    {history.length > 0 && (
                        <button onClick={handleClearAll} className="px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 text-sm flex items-center gap-2 transition-all">
                            <Trash2 className="w-4 h-4" /> Clear All
                        </button>
                    )}
                </header>

                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex justify-between items-center">
                        <span>{error}</span>
                        <button onClick={loadHistory} className="underline text-sm font-medium">Retry Sync</button>
                    </div>
                )}

                {/* Tabs & Search */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-fit">
                        <TabsList className="h-11 dark:bg-black/40 dark:border dark:border-white/10 p-1">
                            <TabsTrigger value="text" className="px-6 py-2 rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-all">
                                <FileText className="w-4 h-4 mr-2" /> Textual
                            </TabsTrigger>
                            <TabsTrigger value="media" className="px-6 py-2 rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-all">
                                <ImageIcon className="w-4 h-4 mr-2" /> Media
                            </TabsTrigger>
                        </TabsList>
                    </Tabs>

                    <div className="relative w-full md:max-w-md">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder={activeTab === 'text' ? "Search claims or verdicts..." : "Search media forensic results..."}
                            className="w-full pl-11 pr-4 py-2.5 rounded-xl bg-card/50 border border-border/50 focus:border-primary/50 focus:outline-none text-sm transition-all dark:bg-card/40 dark:border-white/10"
                        />
                    </div>
                </div>

                {history.length === 0 ? (
                    <div className="p-20 rounded-2xl text-center border border-dashed border-border/50 bg-card/20 flex flex-col items-center">
                        <div className="w-16 h-16 rounded-full bg-muted/20 flex items-center justify-center mb-6">
                            <Clock className="w-8 h-8 text-muted-foreground/40" />
                        </div>
                        <h2 className="text-xl font-medium mb-2">No Records Found</h2>
                        <p className="text-muted-foreground max-w-sm mb-8 text-sm">Your verified archive is currently empty. Start an investigation to populate your history.</p>
                        <button onClick={() => onNavigate?.('investigate')} className="px-8 py-3 rounded-xl bg-primary text-primary-foreground font-medium shadow-lg hover:shadow-primary/20 transition-all">
                            New Investigation
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-12 gap-8">
                        {/* History List Panels */}
                        <div className="col-span-12 lg:col-span-8">
                            <Tabs value={activeTab} className="w-full border-none p-0">
                                <TabsContent value="text" className="m-0 focus-visible:ring-0">
                                    {textHistory.length === 0 ? (
                                        <EmptyTabState message="No textual investigations found matching your search." />
                                    ) : (
                                        <div className="space-y-4">
                                            {textHistory.map((item) => (
                                                <HistoryItemRow
                                                    key={item.id}
                                                    item={item}
                                                    isSelected={selectedItem?.id === item.id}
                                                    onClick={() => setSelectedItem(item)}
                                                    onDelete={handleDelete}
                                                />
                                            ))}
                                        </div>
                                    )}
                                </TabsContent>
                                <TabsContent value="media" className="m-0 focus-visible:ring-0">
                                    {mediaHistory.length === 0 ? (
                                        <EmptyTabState message="No media forensics records found matching your search." />
                                    ) : (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            {mediaHistory.map((item) => (
                                                <MediaHistoryCard
                                                    key={item.id}
                                                    item={item}
                                                    isSelected={selectedItem?.id === item.id}
                                                    onClick={() => setSelectedItem(item)}
                                                    onDelete={handleDelete}
                                                />
                                            ))}
                                        </div>
                                    )}
                                </TabsContent>
                            </Tabs>
                        </div>

                        {/* Detail Side Panel */}
                        <div className="col-span-12 lg:col-span-4">
                            {selectedItem ? (
                                <HistoryDetailPanel
                                    item={selectedItem}
                                    navigate={navigate}
                                />
                            ) : (
                                <div className="h-[400px] rounded-2xl border border-dashed border-border/50 flex flex-col items-center justify-center p-8 text-center bg-card/10">
                                    <Filter className="w-10 h-10 text-muted-foreground/20 mb-4" />
                                    <h3 className="font-medium text-muted-foreground/60 mb-1">Detailed View</h3>
                                    <p className="text-xs text-muted-foreground/40">Select an investigation to see deep forensic insights and full explanation.</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                <footer className="mt-16 pt-8 border-t border-border/10">
                    <div className="text-center text-[10px] text-muted-foreground/40 font-mono tracking-widest uppercase">
                        TruthLens 3.0 • Unified Hybrid Infrastructure
                    </div>
                </footer>
            </div>
        </div>
    );
}

// --- Sub-Components ---

function HistoryItemRow({ item, isSelected, onClick, onDelete }: any) {
    const isFake = (item.verdict || '').toLowerCase().includes('fake') || (item.verdict || '').toLowerCase().includes('false');
    const isReal = (item.verdict || '').toLowerCase().includes('real') || (item.verdict || '').toLowerCase().includes('true') || (item.verdict || '').toLowerCase().includes('verified');
    const verdictBg = isFake ? 'bg-red-500/15 text-red-400 border-red-500/30' : isReal ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 'bg-amber-500/15 text-amber-400 border-amber-500/30';
    const confLabel = (item.confidence || '').toLowerCase();
    const confColor = confLabel === 'high' ? 'text-emerald-400' : confLabel === 'medium' ? 'text-amber-400' : 'text-red-400';

    return (
        <div
            onClick={onClick}
            className={cn(
                "group w-full p-5 rounded-2xl transition-all cursor-pointer border",
                isSelected
                    ? "bg-primary/10 border-primary/40 shadow-[0_0_30px_-10px_rgba(var(--primary),0.2)]"
                    : "bg-card/40 border-border/50 hover:bg-muted/30 hover:border-border/80"
            )}
        >
            <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="w-10 h-10 rounded-xl bg-violet-500/10 text-violet-400 flex items-center justify-center flex-shrink-0 border border-violet-500/20 mt-0.5">
                    <FileText className="w-5 h-5" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground line-clamp-2 leading-snug mb-2">
                        {item.claim || 'No claim recorded'}
                    </p>
                    <div className="flex items-center gap-2 flex-wrap">
                        {/* Verdict badge */}
                        <span className={cn("text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border", verdictBg)}>
                            {item.verdict}
                        </span>
                        {/* Confidence */}
                        {item.confidence && (
                            <span className={cn("text-[10px] font-mono capitalize", confColor)}>
                                {item.confidence} conf.
                            </span>
                        )}
                        {/* Date */}
                        <span className="text-[10px] font-mono text-muted-foreground/50 ml-auto">
                            {formatDate(item.created_at)}
                        </span>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                        onClick={(e) => { e.stopPropagation(); onDelete(item.id); }}
                        className="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-all"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                    <ChevronRight className="w-5 h-5 text-muted-foreground/40" />
                </div>
            </div>
        </div>
    );
}

function MediaHistoryCard({ item, isSelected, onClick, onDelete }: any) {
    const meta = item.metadata || {};
    const heatmap = meta.heatmap;
    const isVideo = meta.content_type?.startsWith('video');
    const realProb = meta.real_probability;
    const fakeProb = meta.fake_probability;
    const isFake = item.verdict?.toUpperCase() === 'FAKE';

    return (
        <Card
            onClick={onClick}
            className={cn(
                "group cursor-pointer transition-all overflow-hidden border-border/50",
                isSelected ? "ring-2 ring-primary/40 border-primary/40 bg-primary/[0.03]" : "hover:border-border hover:bg-muted/20"
            )}
        >
            <CardContent className="p-0">
                {/* Heatmap / placeholder */}
                <div className="relative aspect-video bg-black/40 flex items-center justify-center overflow-hidden">
                    {heatmap ? (
                        <img src={heatmap} alt="Forensic Heatmap" className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-500" />
                    ) : (
                        <div className="text-muted-foreground/20">
                            {isVideo ? <VideoIcon className="w-12 h-12" /> : <ImageIcon className="w-12 h-12" />}
                        </div>
                    )}
                    {/* Verdict badge */}
                    <div className="absolute top-3 right-3">
                        <span className={cn(
                            "text-[10px] uppercase font-bold px-2 py-0.5 rounded-full shadow-lg text-white",
                            isFake ? "bg-red-500/90" : "bg-emerald-500/90"
                        )}>
                            {item.verdict}
                        </span>
                    </div>
                    {/* Confidence pill */}
                    {(realProb !== undefined || fakeProb !== undefined) && (
                        <div className="absolute bottom-2 left-2 flex gap-1.5">
                            <span className="text-[9px] font-mono bg-black/60 backdrop-blur-sm px-1.5 py-0.5 rounded text-emerald-400">R {realProb?.toFixed(1)}%</span>
                            <span className="text-[9px] font-mono bg-black/60 backdrop-blur-sm px-1.5 py-0.5 rounded text-red-400">F {fakeProb?.toFixed(1)}%</span>
                        </div>
                    )}
                </div>

                <div className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">{formatDate(item.created_at)}</span>
                        <div className="flex gap-1">
                            <div className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                            <div className="w-1.5 h-1.5 rounded-full bg-violet-400/50" />
                        </div>
                    </div>
                    <p className="text-xs font-medium text-foreground line-clamp-2 min-h-[2.5rem] mb-3">
                        {meta.filename || item.claim || "Visual Analysis Result"}
                    </p>
                    <div className="flex items-center justify-between pt-3 border-t border-border/30">
                        <span className="text-[10px] font-medium text-muted-foreground flex items-center gap-1.5 uppercase">
                            <Layers className="w-3 h-3" /> {meta.model || 'EfficientNet-B3'}
                        </span>
                        <button
                            onClick={(e) => { e.stopPropagation(); onDelete(item.id); }}
                            className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground opacity-0 group-hover:opacity-100 transition-all"
                        >
                            <Trash2 className="w-3.5 h-3.5" />
                        </button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

function HistoryDetailPanel({ item, navigate }: any) {
    const isMedia = item.claim_type === 'VISUAL_MANIPULATION';
    const meta = item.metadata || {};
    const realProb: number | undefined = meta.real_probability;
    const fakeProb: number | undefined = meta.fake_probability;
    const metaRisk: number | undefined = meta.metadata_risk_score;
    const heatmap: string | undefined = meta.heatmap;

    return (
        <div className="p-7 rounded-2xl bg-gradient-to-br from-card to-card/50 border border-border/50 sticky top-24 shadow-xl overflow-hidden group">
            <div className="absolute -right-4 -top-4 w-24 h-24 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-all" />

            <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground/60 mb-6 flex items-center gap-2">
                <Cpu className="w-4 h-4" /> {isMedia ? 'Forensic Analysis' : 'Insight Report'}
            </h3>

            <div className="space-y-6">
                {/* Claim / filename */}
                <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground/50 block mb-1.5">
                        {isMedia ? 'File Analyzed' : 'Primary Claim'}
                    </label>
                    <p className="text-sm text-foreground leading-snug">
                        {isMedia ? (meta.filename || item.claim) : item.claim}
                    </p>
                </div>

                {/* Verdict + Confidence */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-[10px] font-mono uppercase text-muted-foreground/50 block mb-1.5">Verdict</label>
                        <span className={cn("text-xs font-bold uppercase", getVerdictColor(item.verdict))}>{item.verdict}</span>
                    </div>
                    <div>
                        <label className="text-[10px] font-mono uppercase text-muted-foreground/50 block mb-1.5">Confidence</label>
                        <span className="text-xs font-medium capitalize text-foreground">{item.confidence}</span>
                    </div>
                </div>

                {/* ── Media-specific section ── */}
                {isMedia && (
                    <>
                        {/* Probability bars */}
                        {(realProb !== undefined || fakeProb !== undefined) && (
                            <div className="p-3 rounded-xl bg-violet-500/5 border border-violet-500/10 space-y-3">
                                <label className="text-[10px] font-mono uppercase text-violet-400 block tracking-tight">Neural Probability</label>
                                <div>
                                    <div className="flex justify-between text-[10px] mb-1">
                                        <span className="text-emerald-400">Real</span>
                                        <span className="text-emerald-400 font-bold">{realProb?.toFixed(1)}%</span>
                                    </div>
                                    <div className="h-1.5 rounded-full bg-black/30 overflow-hidden">
                                        <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${realProb ?? 0}%` }} />
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-[10px] mb-1">
                                        <span className="text-red-400">Fake</span>
                                        <span className="text-red-400 font-bold">{fakeProb?.toFixed(1)}%</span>
                                    </div>
                                    <div className="h-1.5 rounded-full bg-black/30 overflow-hidden">
                                        <div className="h-full rounded-full bg-red-500 transition-all" style={{ width: `${fakeProb ?? 0}%` }} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Metadata risk */}
                        {metaRisk !== undefined && (
                            <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/20 border border-border/30">
                                <span className="text-[10px] font-mono text-muted-foreground uppercase">Metadata AI Risk</span>
                                <span className={cn(
                                    "text-xs font-bold",
                                    metaRisk >= 60 ? 'text-red-400' : metaRisk >= 30 ? 'text-amber-400' : 'text-emerald-400'
                                )}>{metaRisk}/100</span>
                            </div>
                        )}

                        {/* Heatmap thumbnail */}
                        {heatmap && (
                            <div>
                                <label className="text-[10px] font-mono uppercase text-muted-foreground/50 block mb-2">Grad-CAM Heatmap</label>
                                <img src={heatmap} alt="Grad-CAM" className="w-full rounded-xl border border-border/30 object-cover" />
                            </div>
                        )}

                        {/* Model badge */}
                        <div className="flex items-center gap-2 p-2 rounded-lg bg-muted/10 border border-border/20">
                            <Layers className="w-3 h-3 text-violet-400" />
                            <span className="text-[10px] font-mono text-muted-foreground uppercase">Model</span>
                            <span className="text-[10px] font-mono text-foreground ml-auto">{meta.model || 'EfficientNet-B3'}</span>
                        </div>
                    </>
                )}

                {/* Forensic / Evidence summary */}
                <div>
                    <label className="text-[10px] font-mono uppercase text-muted-foreground/50 block mb-1.5">Forensic Summary</label>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                        {item.explanation || "Detailed explanation currently being synchronized..."}
                    </p>
                </div>

                <button
                    onClick={() => { navigate('/investigate', { state: { archivedResult: item } }); }}
                    className="w-full py-4 rounded-xl bg-primary text-primary-foreground font-bold text-xs uppercase tracking-widest
                        shadow-lg shadow-primary/20 hover:translate-y-[-2px] hover:shadow-primary/30 active:translate-y-0 transition-all flex items-center justify-center gap-2"
                >
                    <ShieldCheck className="w-4 h-4" /> Full Investigation Report
                </button>
            </div>
        </div>
    );
}

function EmptyTabState({ message }: { message: string }) {
    return (
        <div className="p-12 rounded-2xl border border-dashed border-border/30 text-center bg-card/5">
            <p className="text-sm text-muted-foreground">{message}</p>
        </div>
    );
}

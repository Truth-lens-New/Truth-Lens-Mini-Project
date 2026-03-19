import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FileText, ChevronRight, Filter, Trash2, Clock, Loader2, History } from 'lucide-react';
import { getHistory, deleteHistoryItem, clearAllHistory, type HistoryItem } from '../lib/api';
import type { Page } from '../App';

interface HistoryPageProps {
    onNavigate?: (page: Page) => void;
}

export function HistoryPage({ onNavigate }: HistoryPageProps) {
    const navigate = useNavigate();
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

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

    const filteredData = Array.isArray(history) ? history.filter(item =>
        (item.claim || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.verdict?.toLowerCase().includes(searchQuery.toLowerCase())
    ) : [];

    const getVerdictColor = (verdict?: string) => {
        if (!verdict) return 'text-muted-foreground';
        const v = verdict.toLowerCase();
        // Check false/misleading FIRST
        if (v.includes('false') || v.includes('misleading')) return 'text-red-400';
        if (v.includes('true') || v.includes('verified') || v.includes('accurate')) return 'text-emerald-400';
        return 'text-amber-400';
    };

    const formatDate = (dateStr: string) => {
        // Ensure UTC interpretation if missing timezone
        const utcDateStr = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : `${dateStr}Z`;
        const date = new Date(utcDateStr);
        return date.toLocaleString('en-IN', {
            timeZone: 'Asia/Kolkata',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteHistoryItem(id);
            setHistory(prev => prev.filter(item => item.id !== id));
            if (selectedItem?.id === id) {
                setSelectedItem(null);
            }
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
                    <p className="text-muted-foreground">Loading history...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen pb-16">
            <div className="relative z-10 max-w-7xl mx-auto px-6 pt-8">
                {/* Header */}
                <header className="mb-10">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="flex items-center gap-3 mb-3">
                                <div className="w-10 h-10 rounded-xl bg-muted/50 dark:bg-white/10 flex items-center justify-center
                                    dark:shadow-[0_0_15px_-5px] dark:shadow-white/20 dark:ring-1 dark:ring-white/10">
                                    <History className="w-5 h-5 text-muted-foreground" />
                                </div>
                                <span className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/60">
                                    Archive
                                </span>
                            </div>
                            <h1 className="text-4xl font-light tracking-tight text-foreground">Verification History</h1>
                        </div>
                        {history.length > 0 && (
                            <button
                                onClick={handleClearAll}
                                className="px-4 py-2 rounded-xl backdrop-blur-sm text-sm flex items-center gap-2 transition-all
                                    bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20
                                    dark:shadow-[0_0_15px_-5px] dark:shadow-red-500/30"
                            >
                                <Trash2 className="w-4 h-4" />
                                Clear All
                            </button>
                        )}
                    </div>
                </header>

                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
                        {error}
                        <button onClick={loadHistory} className="ml-4 underline">Retry</button>
                    </div>
                )}

                {/* Search */}
                <div className="mb-8">
                    <div className="relative max-w-md">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search claims or verdicts..."
                            className="w-full pl-12 pr-4 py-3 rounded-xl backdrop-blur-sm transition-all
                                bg-card/50 border border-border/50 focus:border-primary/50 focus:outline-none
                                text-foreground placeholder-muted-foreground
                                dark:bg-card/60 dark:border-white/10 dark:focus:border-primary/50
                                dark:ring-1 dark:ring-white/5"
                        />
                    </div>
                </div>

                {history.length === 0 ? (
                    <div className="p-12 rounded-2xl backdrop-blur-sm text-center relative overflow-hidden
                        border border-border/50 bg-card/50
                        dark:border-border/30 dark:bg-gradient-to-br dark:from-card/60 dark:to-card/30
                        dark:shadow-[0_0_40px_-15px] dark:shadow-white/10
                        dark:ring-1 dark:ring-white/5">
                        <Clock className="w-16 h-16 text-muted-foreground/50 mx-auto mb-4" />
                        <h2 className="text-xl mb-2 text-foreground">No History Yet</h2>
                        <p className="text-muted-foreground mb-6">Your verification history will appear here after you analyze claims.</p>
                        <button
                            onClick={() => onNavigate?.('investigate')}
                            className="px-6 py-3 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-primary-foreground font-medium
                                shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 transition-all"
                        >
                            Start Your First Investigation
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-12 gap-6">
                        {/* History List */}
                        <div className="col-span-12 lg:col-span-8 p-6 rounded-2xl backdrop-blur-sm relative overflow-hidden
                            border border-border/50 bg-card/50
                            dark:border-border/30 dark:bg-gradient-to-br dark:from-card/60 dark:to-card/30
                            dark:shadow-[0_0_40px_-15px] dark:shadow-white/10
                            dark:ring-1 dark:ring-white/5">

                            {/* Dark mode edge glow */}
                            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent hidden dark:block rounded-t-2xl" />

                            <div className="space-y-2 relative">
                                {/* Header */}
                                <div className="grid grid-cols-12 gap-4 pb-3 border-b border-border/30 dark:border-white/10 text-xs font-mono uppercase tracking-wider text-muted-foreground">
                                    <div className="col-span-6">Claim</div>
                                    <div className="col-span-2">Date</div>
                                    <div className="col-span-2">Verdict</div>
                                    <div className="col-span-2 text-right">Actions</div>
                                </div>

                                {/* Rows */}
                                {filteredData.map((item) => (
                                    <div
                                        key={item.id}
                                        onClick={() => setSelectedItem(item)}
                                        className={`w-full grid grid-cols-12 gap-4 p-4 rounded-xl transition-all text-left cursor-pointer ${selectedItem?.id === item.id
                                            ? 'bg-primary/10 border border-primary/30 dark:shadow-[0_0_20px_-10px] dark:shadow-primary/40'
                                            : 'bg-card/30 dark:bg-white/5 border border-transparent hover:bg-muted/20 dark:hover:bg-white/10 hover:border-border/50 dark:hover:border-white/20'
                                            }`}
                                    >
                                        <div className="col-span-6 flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-violet-500/10 dark:bg-violet-500/20 text-violet-400 flex items-center justify-center flex-shrink-0
                                                dark:shadow-[0_0_10px_-3px] dark:shadow-violet-500/40">
                                                <FileText className="w-4 h-4" />
                                            </div>
                                            <span className="truncate text-foreground">{(item.claim || 'Unknown claim').slice(0, 80)}{(item.claim || '').length > 80 ? '...' : ''}</span>
                                        </div>
                                        <div className="col-span-2 flex items-center text-xs text-muted-foreground">
                                            {formatDate(item.created_at)}
                                        </div>
                                        <div className={`col-span-2 flex items-center text-sm font-medium ${getVerdictColor(item.verdict)}`}>
                                            {item.verdict || 'Unknown'}
                                        </div>
                                        <div className="col-span-2 flex items-center justify-end gap-2">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }}
                                                className="p-2 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-all"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                            <ChevronRight className="w-4 h-4 text-muted-foreground" />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Detail Panel */}
                        <div className="col-span-12 lg:col-span-4">
                            {selectedItem ? (
                                <div className="p-6 rounded-2xl backdrop-blur-sm sticky top-24 relative overflow-hidden
                                    border border-primary/30 bg-card/50
                                    dark:border-primary/40 dark:bg-gradient-to-br dark:from-primary/10 dark:via-card/60 dark:to-card/40
                                    dark:shadow-[0_0_40px_-15px] dark:shadow-primary/30
                                    dark:ring-1 dark:ring-white/5">

                                    {/* Dark mode edge glow */}
                                    <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent hidden dark:block rounded-t-2xl" />

                                    <h3 className="text-lg font-medium mb-4 text-foreground relative">Analysis Details</h3>
                                    <div className="space-y-4 relative">
                                        <div>
                                            <div className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1">Claim</div>
                                            <div className="text-sm text-foreground">{selectedItem.claim || 'Unknown'}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1">Date</div>
                                            <div className="text-sm text-foreground">{formatDate(selectedItem.created_at)}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1">Verdict</div>
                                            <div className={`text-sm font-medium ${getVerdictColor(selectedItem.verdict)}`}>
                                                {selectedItem.verdict || 'Unknown'}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1">Confidence</div>
                                            <div className="text-sm capitalize text-foreground">{selectedItem.confidence || 'Unknown'}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1">Explanation</div>
                                            <div className="text-sm text-muted-foreground leading-relaxed">{(selectedItem.explanation || 'N/A').slice(0, 200)}...</div>
                                        </div>

                                        <button
                                            onClick={() => {
                                                navigate('/investigate', {
                                                    state: {
                                                        archivedResult: selectedItem
                                                    }
                                                });
                                            }}
                                            className="w-full mt-4 py-3 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-primary-foreground font-medium text-sm
                                                shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 transition-all"
                                        >
                                            View Full Analysis
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="p-6 rounded-2xl backdrop-blur-sm h-[300px] flex items-center justify-center text-center
                                    border border-border/50 bg-card/50
                                    dark:border-border/30 dark:bg-gradient-to-br dark:from-card/60 dark:to-card/30
                                    dark:ring-1 dark:ring-white/5">
                                    <div>
                                        <Filter className="w-12 h-12 text-muted-foreground/40 mx-auto mb-3" />
                                        <p className="text-muted-foreground">Select an item to view details</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Footer */}
                <footer className="mt-12 pt-8 border-t border-border/30 dark:border-white/10">
                    <div className="text-center text-xs text-muted-foreground/50 font-mono">
                        TruthLens v3.0 • Hybrid Pipeline Architecture
                    </div>
                </footer>
            </div>
        </div>
    );
}

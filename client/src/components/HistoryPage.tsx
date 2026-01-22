import { useState, useEffect } from 'react';
import { Search, FileText, ChevronRight, Filter, Trash2, Clock, Loader2, Image as ImageIcon } from 'lucide-react';
import { getHistory, deleteHistoryItem, clearAllHistory, type HistoryItem } from '../lib/api';
import type { Page } from '../App';

interface HistoryPageProps {
    onNavigate?: (page: Page) => void;
}

export function HistoryPage({ onNavigate }: HistoryPageProps) {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Load history from backend on mount
    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await getHistory();
            // Ensure response is an array (API might return object with items property)
            let items: HistoryItem[] = [];
            if (Array.isArray(response)) {
                items = response;
            } else if (response && typeof response === 'object' && 'items' in response) {
                items = (response as { items: HistoryItem[] }).items;
            }
            setHistory(items);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load history');
            setHistory([]); // Reset to empty array on error
        } finally {
            setLoading(false);
        }
    };

    // Defensive check: ensure history is an array before filtering
    const filteredData = Array.isArray(history) ? history.filter(item =>
        (item.claim || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.verdict?.toLowerCase().includes(searchQuery.toLowerCase())
    ) : [];

    const getVerdictColor = (verdict?: string) => {
        if (!verdict) return 'text-[#D6D6D6]';
        const v = verdict.toLowerCase();
        if (v.includes('true') || v.includes('verified') || v.includes('accurate')) return 'text-[#00FFC3]';
        if (v.includes('false') || v.includes('misleading')) return 'text-red-400';
        return 'text-[#99F8FF]';
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        // Add timezone offset for IST (+5:30) if server returns UTC
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
            <div className="min-h-screen pt-20 pb-12 px-8 flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-[#00FFC3] mx-auto mb-4 animate-spin" />
                    <p className="text-[#D6D6D6]">Loading history...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen pt-20 pb-12 px-8">
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-40 left-1/3 w-[500px] h-[500px] bg-[#00FFC3]/5 rounded-full blur-[140px]" />
            </div>

            <div className="relative z-10 max-w-[1600px] mx-auto">
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl mb-2">Verification History</h1>
                        <p className="text-[#D6D6D6]">View and manage past analyses</p>
                    </div>
                    {history.length > 0 && (
                        <button
                            onClick={handleClearAll}
                            className="px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-all text-sm flex items-center gap-2"
                        >
                            <Trash2 className="w-4 h-4" />
                            Clear All
                        </button>
                    )}
                </div>

                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
                        {error}
                        <button onClick={loadHistory} className="ml-4 underline">Retry</button>
                    </div>
                )}

                {/* Search */}
                <div className="mb-6">
                    <div className="relative max-w-md">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#666]" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search claims or verdicts..."
                            className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-[#00FFC3]/30 focus:outline-none"
                        />
                    </div>
                </div>

                {history.length === 0 ? (
                    <div className="p-12 rounded-2xl backdrop-blur-md bg-white/5 border border-white/10 text-center">
                        <Clock className="w-16 h-16 text-[#666] mx-auto mb-4" />
                        <h2 className="text-xl mb-2">No History Yet</h2>
                        <p className="text-[#D6D6D6] mb-6">Your verification history will appear here after you analyze claims.</p>
                        <button
                            onClick={() => onNavigate?.('verify-article')}
                            className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#99F8FF] to-[#00FFC3] text-black hover:shadow-[0_0_30px_rgba(0,255,195,0.3)] transition-all"
                        >
                            Verify Your First Claim
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-3 gap-6">
                        {/* History List */}
                        <div className="col-span-2 p-6 rounded-2xl backdrop-blur-md bg-white/5 border border-white/10">
                            <div className="space-y-2">
                                {/* Header */}
                                <div className="grid grid-cols-12 gap-4 pb-3 border-b border-white/10 text-sm text-[#D6D6D6]">
                                    <div className="col-span-6">Claim</div>
                                    <div className="col-span-2">Date</div>
                                    <div className="col-span-2">Verdict</div>
                                    <div className="col-span-2">Actions</div>
                                </div>

                                {/* Rows */}
                                {filteredData.map((item) => (
                                    <div
                                        key={item.id}
                                        onClick={() => setSelectedItem(item)}
                                        className={`w-full grid grid-cols-12 gap-4 p-4 rounded-xl transition-all text-left cursor-pointer ${selectedItem?.id === item.id
                                            ? 'bg-white/10 border border-[#00FFC3]/30'
                                            : 'bg-white/5 border border-transparent hover:bg-white/10 hover:border-white/10'
                                            }`}
                                    >
                                        <div className="col-span-6 flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center flex-shrink-0">
                                                {(item.claim || '').startsWith('Deepfake Analysis') ? <ImageIcon className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                                            </div>
                                            <span className="truncate">{(item.claim || 'Unknown claim').slice(0, 80)}{(item.claim || '').length > 80 ? '...' : ''}</span>
                                        </div>
                                        <div className="col-span-2 flex items-center text-sm text-[#D6D6D6]">
                                            {formatDate(item.created_at)}
                                        </div>
                                        <div className={`col-span-2 flex items-center ${getVerdictColor(item.verdict)}`}>
                                            {item.verdict || 'Unknown'}
                                        </div>
                                        <div className="col-span-2 flex items-center justify-end gap-2">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }}
                                                className="p-2 rounded-lg hover:bg-red-500/20 text-[#666] hover:text-red-400 transition-all"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                            <ChevronRight className="w-4 h-4 text-[#666]" />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Detail Panel */}
                        <div className="col-span-1">
                            {selectedItem ? (
                                <div className="p-6 rounded-2xl backdrop-blur-md bg-white/5 border border-white/10 sticky top-24">
                                    <h3 className="text-xl mb-4">Analysis Details</h3>
                                    <div className="space-y-4">
                                        <div>
                                            <div className="text-xs text-[#D6D6D6] mb-1">Claim</div>
                                            <div className="text-sm">{selectedItem.claim || 'Unknown'}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-[#D6D6D6] mb-1">Date</div>
                                            <div className="text-sm">{formatDate(selectedItem.created_at)}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-[#D6D6D6] mb-1">Verdict</div>
                                            <div className={`text-sm ${getVerdictColor(selectedItem.verdict)}`}>
                                                {selectedItem.verdict || 'Unknown'}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-[#D6D6D6] mb-1">Confidence</div>
                                            <div className="text-sm capitalize">{selectedItem.confidence || 'Unknown'}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-[#D6D6D6] mb-1">Explanation</div>
                                            <div className="text-sm text-[#D6D6D6]">{(selectedItem.explanation || 'N/A').slice(0, 200)}...</div>
                                        </div>

                                        {/* View Full Analysis Button */}
                                        {!(selectedItem.claim || '').startsWith('Deepfake Analysis') && (
                                            <button
                                                onClick={() => {
                                                    // Save selected item to localStorage for ArticleVerification to restore
                                                    localStorage.setItem('truthlens_current_result', JSON.stringify({
                                                        claim: selectedItem.claim || '',
                                                        result: {
                                                            claim: selectedItem.claim,
                                                            verdict: selectedItem.verdict,
                                                            confidence: selectedItem.confidence,
                                                            explanation: selectedItem.explanation,
                                                            domain_trust: { domain: null, score: 'unknown' },
                                                            factcheck: { found: false },
                                                            evidence: [],
                                                            stance_summary: { supports: 0, refutes: 0, discuss: 0, unrelated: 0 }
                                                        }
                                                    }));
                                                    onNavigate?.('verify-article');
                                                }}
                                                className="w-full mt-4 py-3 rounded-xl bg-gradient-to-r from-[#99F8FF] to-[#00FFC3] text-black hover:shadow-[0_0_30px_rgba(0,255,195,0.3)] transition-all text-sm font-medium"
                                            >
                                                View Full Analysis
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <div className="p-6 rounded-2xl backdrop-blur-md bg-white/5 border border-white/10 h-[300px] flex items-center justify-center text-center">
                                    <div>
                                        <Filter className="w-12 h-12 text-[#666] mx-auto mb-3" />
                                        <p className="text-[#D6D6D6]">Select an item to view details</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

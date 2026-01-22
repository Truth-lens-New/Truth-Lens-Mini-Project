import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Image,
  History,
  ArrowUpRight,
  Loader2,
  Eye,
  Target,
  Activity,
  ChevronRight,
  Layers,
  Cpu,
  Database,
  Sparkles,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
} from "lucide-react";
import type { Page, UserMode } from "../App";
import { getHistory, getUserStats, type HistoryItem } from "../lib/api";

interface DashboardProps {
  onNavigate: (page: Page) => void;
  userMode: UserMode;
}

interface UserStats {
  total_analyses: number;
  member_since: string;
  email: string;
}

// Animated counter hook
function useAnimatedCounter(end: number, duration: number = 1500) {
  const [count, setCount] = useState(0);
  const countRef = useRef(0);

  useEffect(() => {
    if (end === 0) return;
    const startTime = Date.now();
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      countRef.current = Math.floor(end * easeOut);
      setCount(countRef.current);
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [end, duration]);

  return count;
}

// Pipeline stages for visualization
const pipelineStages = [
  { name: 'Input Gateway', icon: Layers, status: 'active' },
  { name: 'Claim Extraction', icon: Target, status: 'active' },
  { name: 'Evidence Gathering', icon: Database, status: 'active' },
  { name: 'Verdict Engine', icon: Cpu, status: 'active' },
];

// Verdict icon mapping
// Verdict icon mapping
const getVerdictIcon = (verdict: string) => {
  const v = verdict?.toLowerCase() || '';
  // Check false/misleading FIRST to avoid catching 'verified_false' as verified
  if (v.includes('false') || v.includes('misleading')) return { icon: XCircle, color: '#ef4444' };
  if (v.includes('true') || v.includes('verified')) return { icon: CheckCircle2, color: '#10b981' };
  if (v.includes('disputed') || v.includes('mixed')) return { icon: AlertTriangle, color: '#f59e0b' };
  return { icon: HelpCircle, color: '#6366f1' };
};

// Floating Particle Animation for Dark Mode (Option F)
// Floating Particle Animation for Dark Mode (Option F)
function ParticleField() {
  // Generate stable random values on mount
  const particles = Array.from({ length: 30 }, (_, i) => ({
    id: i,
    size: 3 + (i % 6), // Slightly larger: 3px-8px
    left: (i * 9) % 100, // Better spread
    top: (i * 13) % 100,
    delay: (i * 0.7) % 5,
    duration: 15 + (i % 5) * 4,
    opacity: 0.3 + (i % 5) * 0.15, // Brighter: 0.3 - 0.9
    color: i % 3 === 0 ? 'bg-cyan-400' : i % 3 === 1 ? 'bg-violet-400' : 'bg-white',
    glow: i % 3 === 0 ? 'shadow-[0_0_8px_rgba(34,211,238,0.6)]' : i % 3 === 1 ? 'shadow-[0_0_8px_rgba(167,139,250,0.6)]' : 'shadow-[0_0_6px_rgba(255,255,255,0.6)]'
  }));

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 hidden dark:block">
      {particles.map((p) => (
        <div
          key={p.id}
          className={`absolute rounded-full animate-float ${p.color} ${p.glow}`}
          style={{
            width: `${p.size}px`,
            height: `${p.size}px`,
            left: `${p.left}%`,
            top: `${p.top}%`,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
            opacity: p.opacity,
          }}
        />
      ))}
    </div>
  );
}

export function Dashboard({ onNavigate, userMode }: DashboardProps) {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleQuickSearch = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (searchQuery.trim()) {
      navigate('/investigate', { state: { initialQuery: searchQuery } });
    } else {
      onNavigate('investigate');
    }
  };

  // Use history count as the source of truth for investigations
  const totalInvestigations = historyItems.length;
  const animatedTotal = useAnimatedCounter(totalInvestigations);

  // Compute verdict distribution from real history
  const verdictDistribution = historyItems.reduce((acc, item) => {
    const verdict = item.verdict?.toLowerCase() || 'unverified';
    if (verdict.includes('true')) acc.verified_true++;
    else if (verdict.includes('false')) acc.verified_false++;
    else if (verdict.includes('disputed')) acc.disputed++;
    else acc.unverified++;
    return acc;
  }, { verified_true: 0, verified_false: 0, disputed: 0, unverified: 0 });

  useEffect(() => {
    fetchUserStats();
    fetchHistory();
  }, []);

  const fetchUserStats = async () => {
    try {
      if (!localStorage.getItem('token')) {
        setLoading(false);
        return;
      }

      const data = await getUserStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await getHistory();
      let items: HistoryItem[] = [];
      if (Array.isArray(response)) {
        items = response;
      } else if (response && typeof response === 'object' && 'items' in response) {
        items = (response as { items: HistoryItem[] }).items;
      }
      setHistoryItems(items);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const formatMemberSince = (dateStr?: string) => {
    if (!dateStr) return 'Today';
    // Ensure UTC interpretation if missing timezone
    const utcDateStr = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : `${dateStr}Z`;
    const date = new Date(utcDateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays < 1) return 'Today';
    if (diffDays < 30) return `${diffDays}d ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
    return `${Math.floor(diffDays / 365)}y ago`;
  };

  const formatTimeAgo = (dateStr: string) => {
    // Ensure UTC interpretation if missing timezone
    const utcDateStr = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : `${dateStr}Z`;
    const date = new Date(utcDateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  // Get recent 5 history items for activity feed
  const recentActivity = historyItems.slice(0, 5);

  return (
    <div className="min-h-screen pb-20 relative">
      {/* Floating Particles for Dark Mode */}
      <ParticleField />

      <div className="relative z-10 max-w-7xl mx-auto px-6 pt-8">
        {/* Header */}
        <header className="mb-12">
          <div className="flex items-end justify-between">
            <div>
              <div className="text-xs font-mono uppercase tracking-[0.3em] text-muted-foreground/60 mb-3">
                Forensic Intelligence Platform
              </div>
              <h1 className="text-4xl md:text-5xl font-light tracking-tight text-foreground">
                Command Center
              </h1>
            </div>
            <div className="text-right hidden md:block">
              <div className="text-xs font-mono text-muted-foreground/60 mb-1">OPERATOR</div>
              <div className="text-sm font-medium text-foreground">
                {stats?.email?.split('@')[0] || 'Agent'}
              </div>
            </div>
          </div>
        </header>

        {/* Bento Grid */}
        <div className="grid grid-cols-12 gap-4 mb-8">

          {/* Primary CTA - Investigate */}
          <div
            onClick={() => onNavigate('investigate')}
            className="col-span-12 md:col-span-8 group relative p-8 rounded-2xl overflow-hidden transition-all duration-500 text-left cursor-pointer
              border border-primary/30 bg-gradient-to-br from-primary/10 via-card/50 to-card/30 backdrop-blur-sm
              hover:border-primary/60 hover:shadow-xl hover:shadow-primary/10
              dark:border-primary/40 dark:bg-gradient-to-br dark:from-primary/15 dark:via-card/60 dark:to-card/40
              dark:shadow-[0_0_60px_-15px] dark:shadow-primary/30
              dark:hover:border-primary/60 dark:hover:shadow-[0_0_80px_-10px] dark:hover:shadow-primary/40
              dark:ring-1 dark:ring-primary/10 dark:ring-inset"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 pointer-events-none" />
            <div className="absolute inset-0 hidden dark:block pointer-events-none">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
              <div className="absolute inset-y-0 left-0 w-px bg-gradient-to-b from-primary/50 via-transparent to-transparent" />
            </div>

            <div className="absolute top-0 right-0 w-32 h-32 pointer-events-none">
              <div className="absolute top-4 right-4 w-20 h-20 rounded-full bg-primary/20 dark:bg-primary/30 blur-2xl group-hover:bg-primary/30 dark:group-hover:bg-primary/50 transition-colors" />
              <div className="absolute top-6 right-6 w-12 h-12 rounded-full bg-primary/10 dark:bg-primary/20 backdrop-blur-sm border border-primary/20 dark:border-primary/40 flex items-center justify-center
                dark:shadow-[0_0_20px_-5px] dark:shadow-primary/50">
                <ArrowUpRight className="w-5 h-5 text-primary group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </div>
            </div>

            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-4 pointer-events-none">
                <div className="w-10 h-10 rounded-xl bg-primary/20 dark:bg-primary/30 flex items-center justify-center
                  dark:shadow-[0_0_15px_-3px] dark:shadow-primary/50 dark:ring-1 dark:ring-primary/30">
                  <Search className="w-5 h-5 text-primary" />
                </div>
                <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/20 dark:bg-primary/30 text-primary border border-primary/30 dark:border-primary/50
                  dark:shadow-[0_0_10px_-2px] dark:shadow-primary/40">
                  V3 Engine
                </span>
              </div>

              <h2 className="text-2xl md:text-3xl font-medium text-foreground mb-2 tracking-tight pointer-events-none">
                Deep Investigation
              </h2>
              <p className="text-muted-foreground max-w-lg leading-relaxed mb-6 pointer-events-none">
                Multi-source evidence synthesis with Wikidata verification, DuckDuckGo search,
                and real-time stance detection.
              </p>

              <form
                onSubmit={handleQuickSearch}
                className="relative max-w-lg flex items-center gap-2"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="relative flex-1 group/input">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Paste a URL or claim to investigate..."
                    className="w-full bg-background/50 dark:bg-black/20 border border-primary/20 dark:border-primary/30 rounded-xl px-4 py-3 pl-11
                      focus:outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/60
                      placeholder:text-muted-foreground/50 text-foreground transition-all duration-300
                      hover:bg-background/60 dark:hover:bg-black/30 hover:border-primary/40"
                    onKeyDown={(e) => e.stopPropagation()}
                  />
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/50 group-focus-within/input:text-primary transition-colors" />
                </div>
                <button
                  type="submit"
                  className="px-5 py-3 rounded-xl bg-primary/10 hover:bg-primary/20 border border-primary/20 text-primary font-medium transition-all duration-300
                    hover:scale-105 active:scale-95 flex items-center gap-2"
                >
                  <span>Analyze</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>

          {/* Personal Stats Ring (Option B) */}
          <div className="col-span-6 md:col-span-4 row-span-2 p-6 rounded-2xl backdrop-blur-sm
            border border-border/50 bg-card/50
            dark:border-border/30 dark:bg-gradient-to-br dark:from-card/80 dark:to-card/40
            dark:shadow-[0_0_40px_-10px] dark:shadow-primary/20
            dark:ring-1 dark:ring-white/5 dark:ring-inset">

            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent hidden dark:block rounded-t-2xl" />

            <div className="h-full flex flex-col relative">
              <div className="flex items-center gap-2 mb-6">
                <Activity className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">Analytics</span>
              </div>

              <div className="flex-1 flex flex-col">
                <div className="mb-6">
                  <div className="text-5xl md:text-6xl font-extralight tracking-tighter mb-1
                    text-foreground dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-br dark:from-white dark:via-white dark:to-white/70">
                    {loading || historyLoading ? (
                      <Loader2 className="w-8 h-8 text-primary animate-spin" />
                    ) : (
                      animatedTotal
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">Total Investigations</div>
                </div>

                {/* Activity Feed Inside Analytics */}
                <div className="flex-1 min-h-0 overflow-hidden flex flex-col mb-4">
                  <div className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                    <Clock className="w-3 h-3" />
                    Recent Activity
                  </div>
                  <div className="space-y-2 overflow-y-auto pr-1 custom-scrollbar -mr-1">
                    {recentActivity.map((item, i) => {
                      const { color } = getVerdictIcon(item.verdict);
                      return (
                        <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-muted/10 dark:bg-white/5 border border-transparent hover:border-white/10 transition-all cursor-pointer" onClick={() => onNavigate('history')}>
                          <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-baseline">
                              <p className="text-xs text-foreground truncate max-w-[120px]">{item.claim}</p>
                              <span className="text-[9px] text-muted-foreground whitespace-nowrap ml-2">{formatTimeAgo(item.created_at)}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="pt-4 border-t border-border/50 dark:border-white/10 mt-auto">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xl font-light text-foreground dark:text-primary">
                        {verdictDistribution.verified_true + verdictDistribution.verified_false}
                      </div>
                      <div className="text-xs text-muted-foreground/60">Resolved</div>
                    </div>
                    <div>
                      <div className="text-xl font-light text-foreground">{formatMemberSince(stats?.member_since)}</div>
                      <div className="text-xs text-muted-foreground/60">Member</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Verify Media */}
          <button
            onClick={() => onNavigate('verify-media')}
            className="col-span-6 md:col-span-4 group p-6 rounded-2xl backdrop-blur-sm transition-all duration-300 text-left relative
              border border-border/50 bg-card/50 hover:border-violet-400/50 hover:bg-card/80 hover:shadow-lg hover:shadow-violet-500/10
              dark:border-violet-500/20 dark:bg-gradient-to-br dark:from-violet-500/10 dark:via-card/60 dark:to-card/40
              dark:hover:border-violet-400/50 dark:hover:shadow-[0_0_40px_-10px] dark:hover:shadow-violet-500/30
              dark:ring-1 dark:ring-white/5 dark:ring-inset"
          >
            <div className="absolute top-4 right-4">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-violet-500/20 dark:bg-violet-500/30 text-violet-400 border border-violet-500/30 dark:border-violet-500/50
                dark:shadow-[0_0_10px_-2px] dark:shadow-violet-500/40">
                Soon
              </span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 dark:bg-violet-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform
              dark:shadow-[0_0_20px_-5px] dark:shadow-violet-500/40 dark:ring-1 dark:ring-violet-500/20">
              <Image className="w-5 h-5 text-violet-400" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-1">Verify Media</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Deepfake & manipulation detection
            </p>
          </button>

          {/* View History */}
          {/* History Button (Restored to Slot) */}
          <button
            onClick={() => onNavigate('history')}
            className="col-span-6 md:col-span-4 group p-6 rounded-2xl backdrop-blur-sm transition-all duration-300 text-left relative flex flex-col justify-between
              border border-border/50 bg-card/50 hover:border-border hover:shadow-lg
              dark:border-border/30 dark:bg-gradient-to-br dark:from-card/60 dark:to-card/30
              dark:hover:border-white/20 dark:hover:shadow-[0_0_30px_-10px] dark:hover:shadow-white/10
              dark:ring-1 dark:ring-white/5 dark:ring-inset"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-muted/50 dark:bg-white/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform
                dark:shadow-[0_0_15px_-5px] dark:shadow-white/20 dark:ring-1 dark:ring-white/10">
                <History className="w-5 h-5 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium text-foreground mb-1">History</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Browse archive
              </p>
            </div>

            <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
              <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
            </div>
          </button>
        </div>

        {/* Bottom Row - Activity Feed + Pipeline + Verdict Distribution */}
        <div className="grid grid-cols-12 gap-4">


          {/* Pipeline Visualization */}
          <div className="col-span-12 p-6 rounded-2xl backdrop-blur-sm relative
            border border-border/50 bg-card/30
            dark:border-primary/20 dark:bg-gradient-to-br dark:from-primary/5 dark:via-card/50 dark:to-card/30
            dark:shadow-[0_0_50px_-15px] dark:shadow-primary/25
            dark:ring-1 dark:ring-white/5 dark:ring-inset">

            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent hidden dark:block rounded-t-2xl" />

            <div className="flex items-center justify-between mb-6 relative">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">V3 Pipeline Status</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse dark:shadow-[0_0_10px_2px] dark:shadow-emerald-400/50" />
                <span className="text-xs text-emerald-400">Operational</span>
              </div>
            </div>

            <div className="flex items-center justify-between relative">
              {pipelineStages.map((stage, i) => (
                <div key={stage.name} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 dark:from-primary/30 dark:to-primary/10 border border-primary/20 dark:border-primary/40 flex items-center justify-center mb-2
                      dark:shadow-[0_0_25px_-5px] dark:shadow-primary/40 dark:ring-1 dark:ring-primary/20">
                      <stage.icon className="w-5 h-5 text-primary" />
                    </div>
                    <span className="text-[10px] text-center text-muted-foreground max-w-[80px] leading-tight">
                      {stage.name}
                    </span>
                  </div>
                  {i < pipelineStages.length - 1 && (
                    <div className="w-8 md:w-16 h-px mx-2 relative">
                      <div className="absolute inset-0 bg-gradient-to-r from-primary/40 to-primary/10 dark:from-primary/60 dark:to-primary/20" />
                      <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-transparent blur-sm hidden dark:block" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Verdict Distribution */}
          <div className="col-span-12 p-6 rounded-2xl backdrop-blur-sm relative
            border border-border/50 bg-card/30
            dark:border-border/30 dark:bg-gradient-to-br dark:from-card/60 dark:to-card/30
            dark:shadow-[0_0_40px_-15px] dark:shadow-white/10
            dark:ring-1 dark:ring-white/5 dark:ring-inset">

            <div className="flex items-center gap-2 mb-6">
              <Eye className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">Verdict Distribution</span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Verified True', count: verdictDistribution.verified_true, color: '#10b981' },
                { label: 'Verified False', count: verdictDistribution.verified_false, color: '#ef4444' },
                { label: 'Disputed', count: verdictDistribution.disputed, color: '#f59e0b' },
                { label: 'Unverified', count: verdictDistribution.unverified, color: '#6366f1' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-3 p-3 rounded-xl bg-muted/20 dark:bg-white/5">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center dark:shadow-lg"
                    style={{ backgroundColor: `${item.color}20` }}>
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  </div>
                  <div>
                    <div className="text-2xl font-light text-foreground">{item.count}</div>
                    <div className="text-[10px] text-muted-foreground">{item.label}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 pt-8 border-t border-border/30 dark:border-white/10">
          <div className="flex items-center justify-between text-xs text-muted-foreground/50">
            <div className="font-mono">TruthLens v3.0 • Hybrid Pipeline Architecture</div>
            <div className="flex items-center gap-4">
              <button onClick={() => onNavigate('settings')} className="hover:text-foreground transition-colors">
                Settings
              </button>
              {userMode !== 'Professional' && (
                <button className="text-primary hover:text-primary/80 transition-colors flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  Upgrade to Pro
                </button>
              )}
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
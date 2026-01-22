import { useState, useEffect } from 'react';
import { User, Shield, LogOut, Loader2, Calendar, BarChart3, Settings } from 'lucide-react';
import type { Page } from '../App';

interface SettingsPageProps {
  onNavigate: (page: Page) => void;
  onLogout?: () => void;
}

interface UserProfile {
  id: number;
  email: string;
  member_since: string;
  total_analyses: number;
}

export function SettingsPage({ onLogout }: SettingsPageProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Not authenticated');
        setLoading(false);
        return;
      }

      const response = await fetch('http://localhost:7000/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch profile');
      }

      const data = await response.json();
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-16">
      <div className="relative z-10 max-w-2xl mx-auto px-6 pt-8">
        {/* Header */}
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-muted/50 dark:bg-white/10 flex items-center justify-center
              dark:shadow-[0_0_15px_-5px] dark:shadow-white/20 dark:ring-1 dark:ring-white/10">
              <Settings className="w-5 h-5 text-muted-foreground" />
            </div>
            <span className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground/60">
              Account
            </span>
          </div>
          <h1 className="text-4xl font-light tracking-tight text-foreground">Settings</h1>
        </header>

        <div className="space-y-6">
          {/* Profile Card */}
          <div className="p-6 rounded-2xl backdrop-blur-sm relative overflow-hidden
            border border-border/50 bg-card/50
            dark:border-primary/20 dark:bg-gradient-to-br dark:from-primary/10 dark:via-card/60 dark:to-card/40
            dark:shadow-[0_0_40px_-15px] dark:shadow-primary/25
            dark:ring-1 dark:ring-white/5">

            {/* Dark mode edge glow */}
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent hidden dark:block rounded-t-2xl" />

            <div className="flex items-center gap-4 mb-6 relative">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center
                shadow-lg shadow-primary/25 dark:shadow-primary/40">
                <User className="w-8 h-8 text-primary-foreground" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-foreground">
                  {profile?.email || 'Unknown User'}
                </h2>
                <p className="text-muted-foreground text-sm">TruthLens Researcher</p>
              </div>
            </div>

            {error ? (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
                {error}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4 relative">
                {/* Member Since */}
                <div className="p-4 rounded-xl backdrop-blur-sm
                  bg-muted/20 border border-border/50
                  dark:bg-white/5 dark:border-white/10 dark:ring-1 dark:ring-white/5">
                  <div className="flex items-center gap-2 text-muted-foreground mb-2">
                    <Calendar className="w-4 h-4" />
                    <span className="text-xs font-mono uppercase tracking-wider">Member Since</span>
                  </div>
                  <div className="text-lg font-medium text-foreground dark:text-primary">
                    {profile?.member_since ? formatDate(profile.member_since) : '—'}
                  </div>
                </div>

                {/* Total Analyses */}
                <div className="p-4 rounded-xl backdrop-blur-sm
                  bg-muted/20 border border-border/50
                  dark:bg-white/5 dark:border-white/10 dark:ring-1 dark:ring-white/5">
                  <div className="flex items-center gap-2 text-muted-foreground mb-2">
                    <BarChart3 className="w-4 h-4" />
                    <span className="text-xs font-mono uppercase tracking-wider">Analyses</span>
                  </div>
                  <div className="text-lg font-medium text-foreground dark:text-primary">
                    {profile?.total_analyses ?? 0}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Security Notice */}
          <div className="p-6 rounded-2xl backdrop-blur-sm relative overflow-hidden
            border border-border/50 bg-card/50
            dark:border-border/30 dark:bg-gradient-to-br dark:from-card/60 dark:to-card/30
            dark:shadow-[0_0_30px_-15px] dark:shadow-white/10
            dark:ring-1 dark:ring-white/5">

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 border border-primary/30 dark:border-primary/40 flex items-center justify-center
                dark:shadow-[0_0_15px_-5px] dark:shadow-primary/40">
                <Shield className="w-5 h-5 text-primary" />
              </div>
              <h3 className="text-lg font-medium text-foreground">Security</h3>
            </div>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Your data is encrypted and securely stored. For password changes,
              please contact support.
            </p>
          </div>

          {/* Logout Button */}
          <button
            onClick={onLogout}
            className="w-full p-4 rounded-2xl backdrop-blur-sm transition-all flex items-center justify-center gap-3 group
              bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 text-red-400
              dark:bg-red-500/10 dark:border-red-500/30 dark:hover:bg-red-500/20
              dark:shadow-[0_0_20px_-10px] dark:shadow-red-500/30
              dark:hover:shadow-[0_0_30px_-10px] dark:hover:shadow-red-500/40"
          >
            <LogOut className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            <span className="font-semibold">Sign Out</span>
          </button>
        </div>

        {/* Version */}
        <footer className="mt-12 pt-8 border-t border-border/30 dark:border-white/10">
          <div className="text-center text-xs text-muted-foreground/50 font-mono">
            TruthLens v3.0 • Hybrid Pipeline Architecture
          </div>
        </footer>
      </div>
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import { flushSync } from 'react-dom';
import { User, LogOut, ChevronDown, Lock, Sun, Moon, LogIn, UserPlus, LayoutDashboard } from 'lucide-react';
import { useTheme } from 'next-themes';
import type { Page, UserMode } from '../App';

interface NavigationProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
  userMode: UserMode;
  onModeChange: (mode: UserMode) => void;
  userEmail?: string;
  onLogout?: () => void;
  isAuthenticated?: boolean;
}

const comingSoonPages: Page[] = ['projects', 'organization'];


export function Navigation({ currentPage, onNavigate, userMode, onModeChange, userEmail, onLogout, isAuthenticated = false }: NavigationProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const menuItems: { label: string; page: Page }[] = [
    { label: 'Dashboard', page: 'dashboard' },
    { label: 'Investigate', page: 'investigate' },
    { label: 'Verify Media', page: 'verify-media' },
    { label: 'History', page: 'history' },
    { label: 'Projects', page: 'projects' },
    { label: 'Enterprise', page: 'organization' },
  ];

  const modes: UserMode[] = ['Basic', 'Creator', 'Professional'];
  const isComingSoon = (page: Page) => comingSoonPages.includes(page);
  const toggleTheme = (e?: React.MouseEvent) => {
    // Fallback if browser doesn't support View Transitions
    if (!document.startViewTransition) {
      setTheme(theme === 'dark' ? 'light' : 'dark');
      return;
    }

    // Get click coordinates or center if triggered programmatically
    const x = e?.clientX ?? window.innerWidth / 2;
    const y = e?.clientY ?? window.innerHeight / 2;

    // Calculate distance to furthest corner to ensure full coverage
    const endRadius = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y)
    );

    const isSwitchingToDark = theme === 'light'; // Current is light, so next is dark

    const transition = document.startViewTransition(() => {
      flushSync(() => {
        setTheme(theme === 'dark' ? 'light' : 'dark');
      });
    });

    // Wait for the pseudo-elements to be created
    transition.ready.then(() => {
      // Logic:
      // If switching to Dark: The OLD view is Light. We shrink it down to the button.
      // If switching to Light: The NEW view is Light. We expand it from the button.
      // This creates a consistent "Light" layer that expands/contracts.

      const clipPath = [
        `circle(0px at ${x}px ${y}px)`,
        `circle(${endRadius}px at ${x}px ${y}px)`,
      ];

      document.documentElement.animate(
        {
          clipPath: isSwitchingToDark ? [...clipPath].reverse() : clipPath,
        },
        {
          duration: 700,
          easing: 'cubic-bezier(0.25, 1, 0.5, 1)',
          // Target the Light layer (Old if going to Dark, New if going to Light)
          pseudoElement: isSwitchingToDark ? '::view-transition-old(root)' : '::view-transition-new(root)',
        }
      );
    });
  };

  // Special handling for Landing/Auth pages:
  // In Dark Mode: standardized dark glass.
  // In Light Mode: "Antigravity" clean glass (dark text).
  const isTransparentPage = ['landing', 'login', 'register'].includes(currentPage);
  const isDark = theme === 'dark';

  // Track scroll for dynamic navbar transparency
  const [isScrolled, setIsScrolled] = useState(false);
  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navContainerClass = `mx-auto rounded-full backdrop-blur-2xl transition-all duration-300
    ${isTransparentPage && !isScrolled ? 'bg-transparent border-transparent shadow-none' : ''}
    ${isTransparentPage && isScrolled && isDark ? 'bg-black/40 border-white/10' : ''}
    ${isTransparentPage && isScrolled && !isDark ? 'bg-white/60 border-black/5 shadow-sm' : ''}
    ${!isTransparentPage ? 'bg-background/80 border-border/50 shadow-lg' : ''}
  `;

  // Text colors based on background
  const logoGradient = isTransparentPage && isDark
    ? 'bg-gradient-to-r from-[#00FFC3] to-[#99F8FF]'
    : 'bg-gradient-to-r from-primary to-secondary'; // Dark text for Light mode landing

  const textColor = isTransparentPage && isDark && !isScrolled
    ? 'text-white/80 hover:text-white'
    : 'text-muted-foreground hover:text-foreground';

  // Click outside handler for user menu
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-4xl px-4">
      <nav className={navContainerClass}>
        <div className="px-5 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div
              onClick={() => onNavigate('landing')}
              className={`text-lg font-bold bg-clip-text text-transparent cursor-pointer ${logoGradient}`}
            >
              TruthLens
            </div>

            {isAuthenticated && !isTransparentPage && (
              <div className="hidden md:flex items-center gap-1">
                {menuItems.map((item) => {
                  const isSoon = isComingSoon(item.page);
                  const isNew = item.page === 'investigate';
                  const isActive = currentPage === item.page;

                  return (
                    <button
                      key={item.page}
                      onClick={() => onNavigate(item.page)}
                      className={`relative px-3 py-1.5 text-sm rounded-full transition-all duration-200 group ${isActive
                        ? 'text-foreground font-medium bg-foreground/10'
                        : isSoon
                          ? 'text-muted-foreground hover:text-foreground opacity-60'
                          : 'text-muted-foreground hover:text-foreground hover:bg-foreground/5'
                        }`}
                    >
                      <span className="relative z-10 flex items-center gap-1.5">
                        {item.label}
                        {isSoon && <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/30" />}
                        {isNew && <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {!isTransparentPage && <div className="h-4 w-px bg-border/50 mx-1 hidden sm:block" />}

            {/* Theme Toggle (Always visible now) */}
            <button
              onClick={toggleTheme}
              className="p-2 text-muted-foreground hover:text-foreground rounded-full hover:bg-foreground/5 transition-colors"
              title="Toggle Theme"
            >
              {mounted && theme === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>

            {!isAuthenticated ? (
              <div className="flex items-center gap-2 ml-1">
                <button
                  onClick={() => onNavigate('login')}
                  className={`px-4 py-1.5 text-xs font-medium rounded-full transition-all flex items-center gap-1.5 ${currentPage === 'login' ? 'hidden' : ''} ${textColor}`}
                >
                  <LogIn className="w-3.5 h-3.5" />
                  Sign In
                </button>
                <button
                  onClick={() => onNavigate('register')}
                  className={`px-4 py-1.5 text-xs font-bold rounded-full transition-all shadow-sm flex items-center gap-1.5 ${currentPage === 'register' ? 'hidden' : ''} ${isTransparentPage && isDark ? 'bg-gradient-to-r from-[#00FFC3] to-[#99F8FF] text-black hover:shadow-[0_0_15px_rgba(0,255,195,0.3)]' : 'text-primary-foreground bg-primary hover:bg-primary/90 shadow-primary/20'}`}
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  Sign Up
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                {/* On Landing/Auth Pages: Show Dashboard Button */}
                {isTransparentPage && (
                  <button
                    onClick={() => onNavigate('dashboard')}
                    className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-foreground/80 hover:text-foreground bg-foreground/5 hover:bg-foreground/10 rounded-full border border-foreground/5 transition-all"
                  >
                    <LayoutDashboard className="w-3.5 h-3.5" />
                    Dashboard
                  </button>
                )}

                <div className="relative ml-1" ref={menuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className={`flex items-center gap-2 pl-1 pr-2 py-1 rounded-full border transition-all ${isTransparentPage && isDark ? 'hover:bg-white/10 border-transparent hover:border-white/20' : 'hover:bg-foreground/5 border-transparent hover:border-border/20'}`}
                  >
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center border ring-1 ring-offset-0 ${isTransparentPage && isDark ? 'bg-gradient-to-tr from-[#00FFC3]/20 via-[#00FFC3]/10 to-[#99F8FF]/20 border-[#00FFC3]/20 ring-black' : 'bg-gradient-to-tr from-primary/20 via-primary/10 to-secondary/20 border-primary/20 ring-background'}`}>
                      <User className={`w-3.5 h-3.5 ${isTransparentPage && isDark ? 'text-[#00FFC3]' : 'text-foreground'}`} />
                    </div>
                    <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${showUserMenu ? 'rotate-180' : ''} ${isTransparentPage && isDark ? 'text-white/60' : 'text-muted-foreground'}`} />
                  </button>

                  {showUserMenu && (
                    <div className={`absolute right-0 mt-3 w-64 rounded-2xl backdrop-blur-3xl border shadow-2xl overflow-hidden z-50 transform origin-top-right animate-in fade-in zoom-in-95 duration-200 
                      ${isTransparentPage && isDark
                        ? 'bg-[#0a0a0a]/95 border-white/10 shadow-black/50'
                        : 'bg-white/95 dark:bg-zinc-900/95 border-zinc-200 dark:border-zinc-800 shadow-xl dark:shadow-black/50'
                      }`}>

                      {userEmail && (
                        <div className={`px-5 py-4 border-b 
                          ${isTransparentPage && isDark
                            ? 'border-white/10 bg-white/5'
                            : 'border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/50'
                          }`}>
                          <div className={`text-[10px] uppercase font-bold tracking-wider mb-1 
                            ${isTransparentPage && isDark ? 'text-zinc-400' : 'text-zinc-500 dark:text-zinc-400'}`}>
                            Signed in as
                          </div>
                          <div className={`text-sm truncate font-medium 
                            ${isTransparentPage && isDark ? 'text-white' : 'text-zinc-900 dark:text-zinc-100'}`}>
                            {userEmail}
                          </div>
                        </div>
                      )}

                      {/* Mode Switcher in Dropdown */}
                      <div className={`p-3 border-b ${isTransparentPage && isDark ? 'border-white/10' : 'border-zinc-100 dark:border-zinc-800'}`}>
                        <div className={`text-[10px] uppercase font-bold tracking-wider mb-2 px-2 
                          ${isTransparentPage && isDark ? 'text-zinc-400' : 'text-zinc-500 dark:text-zinc-400'}`}>
                          Account Type
                        </div>
                        <div className="grid grid-cols-1 gap-1">
                          {modes.map((mode) => {
                            const isLocked = mode !== 'Basic';
                            const isActive = userMode === mode && !isLocked;
                            return (
                              <button
                                key={mode}
                                onClick={() => !isLocked && onModeChange(mode)}
                                disabled={isLocked}
                                className={`px-3 py-2 rounded-lg text-xs flex items-center justify-between transition-all 
                                  ${isActive
                                    ? 'bg-primary/10 text-primary font-medium border border-primary/20'
                                    : isLocked
                                      ? isTransparentPage && isDark
                                        ? 'text-zinc-600 cursor-not-allowed hover:bg-white/5'
                                        : 'text-zinc-300 dark:text-zinc-700 cursor-not-allowed hover:bg-black/5 dark:hover:bg-white/5'
                                      : isTransparentPage && isDark
                                        ? 'text-zinc-300 hover:text-white hover:bg-white/10'
                                        : 'text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/10'
                                  }`}
                              >
                                <span>{mode}</span>
                                {isLocked && <Lock className="w-3 h-3" />}
                                {isActive && <div className="w-1.5 h-1.5 rounded-full bg-primary" />}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div className="p-1.5 space-y-0.5">
                        <button
                          onClick={() => onNavigate('settings')}
                          className={`w-full px-3 py-2 text-left text-sm rounded-xl transition-colors font-medium
                            ${isTransparentPage && isDark
                              ? 'text-zinc-300 hover:bg-white/10 hover:text-white'
                              : 'text-zinc-700 dark:text-zinc-300 hover:bg-black/5 dark:hover:bg-white/10 hover:text-zinc-900 dark:hover:text-white'
                            }`}
                        >
                          Settings
                        </button>
                        <button
                          onClick={() => {
                            setShowUserMenu(false);
                            onLogout?.();
                          }}
                          className={`w-full px-3 py-2 text-left text-sm rounded-xl flex items-center gap-2 transition-colors font-medium
                            ${isTransparentPage && isDark
                              ? 'text-red-400/90 hover:bg-red-500/10 hover:text-red-400'
                              : 'text-red-600/90 dark:text-red-400/90 hover:bg-red-50 dark:hover:bg-red-500/10 hover:text-red-700 dark:hover:text-red-400'
                            }`}
                        >
                          <LogOut className="w-3.5 h-3.5" />
                          Sign out
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </nav>
    </div>
  );
}

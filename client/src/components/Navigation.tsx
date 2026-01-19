import { useState } from 'react';
import { Search, Bell, User, LogOut, ChevronDown, Lock } from 'lucide-react';
import type { Page, UserMode } from '../App';

interface NavigationProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
  userMode: UserMode;
  onModeChange: (mode: UserMode) => void;
  userEmail?: string;
  onLogout?: () => void;
}

const comingSoonPages: Page[] = ['projects', 'organization'];

export function Navigation({ currentPage, onNavigate, userMode, onModeChange, userEmail, onLogout }: NavigationProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);

  const menuItems: { label: string; page: Page }[] = [
    { label: 'Home', page: 'landing' },
    { label: 'Dashboard', page: 'dashboard' },
    { label: 'Verify Media', page: 'verify-media' },
    { label: 'Verify Article', page: 'verify-article' },
    { label: 'History', page: 'history' },
    { label: 'Projects', page: 'projects' },
    { label: 'Enterprise', page: 'organization' },
  ];

  const modes: UserMode[] = ['Basic', 'Creator', 'Professional'];
  const isComingSoon = (page: Page) => comingSoonPages.includes(page);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-black/80 border-b border-white/5">
      <div className="px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-12">
          <div className="text-lg font-semibold text-white">TruthLens</div>
          <div className="flex items-center gap-1">
            {menuItems.map((item) => {
              const isSoon = isComingSoon(item.page);
              return (
                <button
                  key={item.page}
                  onClick={() => onNavigate(item.page)}
                  className={`px-3 py-2 text-sm rounded-lg transition-colors ${currentPage === item.page
                    ? 'text-white bg-white/10'
                    : isSoon
                      ? 'text-gray-500 hover:text-gray-400'
                      : 'text-gray-400 hover:text-white'
                    }`}
                >
                  {item.label}
                  {isSoon && <span className="ml-1.5 text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-gray-500 uppercase">Soon</span>}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center bg-white/5 rounded-lg p-0.5">
            {modes.map((mode) => {
              const isLocked = mode !== 'Basic';
              return (
                <button
                  key={mode}
                  onClick={() => !isLocked && onModeChange(mode)}
                  disabled={isLocked}
                  className={`px-3 py-1.5 rounded-md text-xs flex items-center gap-1 ${userMode === mode && !isLocked
                    ? 'bg-[#00FFC3] text-black'
                    : isLocked
                      ? 'text-gray-600 cursor-not-allowed'
                      : 'text-gray-400 hover:text-white'
                    }`}
                >
                  {mode}
                  {isLocked && <Lock className="w-3 h-3" />}
                </button>
              );
            })}
          </div>

          <button className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/5">
            <Search className="w-4 h-4" />
          </button>
          <button className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 relative">
            <Bell className="w-4 h-4" />
            <div className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-[#00FFC3] rounded-full" />
          </button>

          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 p-1 rounded-lg hover:bg-white/5"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00FFC3]/20 to-[#99F8FF]/20 flex items-center justify-center">
                <User className="w-4 h-4 text-gray-300" />
              </div>
              <ChevronDown className={`w-3 h-3 text-gray-500 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-56 rounded-xl bg-[#141414] border border-white/10 shadow-xl overflow-hidden">
                {userEmail && (
                  <div className="px-4 py-3 border-b border-white/5">
                    <div className="text-[10px] text-gray-500 uppercase">Account</div>
                    <div className="text-sm text-gray-300 truncate">{userEmail}</div>
                  </div>
                )}
                <button
                  onClick={() => onNavigate('settings')}
                  className="w-full px-4 py-2.5 text-left text-sm text-gray-400 hover:bg-white/5 hover:text-white"
                >
                  Settings
                </button>
                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    onLogout?.();
                  }}
                  className="w-full px-4 py-2.5 text-left text-sm text-gray-500 hover:bg-red-500/10 hover:text-red-400 flex items-center gap-2"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

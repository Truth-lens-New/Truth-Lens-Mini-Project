import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { LandingPage } from './components/LandingPage';
import { LoginPage } from './components/LoginPage';
import { RegisterPage } from './components/RegisterPage';
import { Dashboard } from './components/Dashboard';
import { ImageVideoUpload } from './components/ImageVideoUpload';
import { ArticleVerification } from './components/ArticleVerification';
import { HistoryPage } from './components/HistoryPage';
import { ProjectsPage } from './components/ProjectsPage';
import { OrganizationPage } from './components/OrganizationPage';
import { SettingsPage } from './components/SettingsPage';
import { Navigation } from './components/Navigation';
import { ComingSoonOverlay } from './components/ComingSoonOverlay';
import { InvestigationPage } from './components/InvestigationPage';
import { isAuthenticated, logout } from './lib/api';
import { ThemeProvider } from 'next-themes';

export type UserMode = 'Basic' | 'Creator' | 'Professional';
export type Page = 'landing' | 'login' | 'register' | 'dashboard' | 'verify-media' | 'verify-article' | 'investigate' | 'history' | 'projects' | 'organization' | 'settings';

// Map page names to URL paths
const pageToPath: Record<Page, string> = {
  'landing': '/',
  'login': '/login',
  'register': '/register',
  'dashboard': '/dashboard',
  'verify-media': '/verify-media',
  'verify-article': '/verify-article',
  'investigate': '/investigate',
  'history': '/history',
  'projects': '/projects',
  'organization': '/organization',
  'settings': '/settings',
};

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const [userMode, setUserMode] = useState<UserMode>('Basic');
  const [authenticated, setAuthenticated] = useState(isAuthenticated());
  const [userEmail, setUserEmail] = useState<string | undefined>();

  useEffect(() => {
    setAuthenticated(isAuthenticated());
  }, []);

  // Handle navigation with auth protection
  const handleNavigate = (page: Page) => {
    const protectedPages: Page[] = ['dashboard', 'verify-media', 'verify-article', 'history', 'projects', 'organization', 'settings'];

    if (protectedPages.includes(page) && !authenticated) {
      navigate('/login');
      return;
    }

    navigate(pageToPath[page]);
  };

  const handleLogin = (email: string) => {
    setAuthenticated(true);
    setUserEmail(email);
  };

  const handleLogout = () => {
    logout();
    setAuthenticated(false);
    setUserEmail(undefined);
    navigate('/');
  };

  // Determine current page from URL
  const getCurrentPage = (): Page => {
    const path = location.pathname;
    for (const [page, pagePath] of Object.entries(pageToPath)) {
      if (path === pagePath) return page as Page;
    }
    return 'landing';
  };

  const currentPage = getCurrentPage();
  const showNav = authenticated || location.pathname === '/investigate' || ['/', '/login', '/register'].includes(location.pathname);

  return (
    <div className={`min-h-screen bg-background text-foreground transition-colors duration-300 ${['landing', 'login', 'register'].includes(currentPage) ? '' : 'pt-24'}`}>
      {/* Global Background Effects */}
      {!['landing', 'login', 'register'].includes(currentPage) && (
        <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
          {/* Subtle grid pattern */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.02)_1px,transparent_1px)] dark:bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px]" />

          {/* Light mode gradient */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1200px] h-[600px] bg-gradient-to-b from-primary/5 via-primary/2 to-transparent blur-[100px] dark:hidden" />

          {/* Dark mode animated orbs */}
          <div className="hidden dark:block">
            <div className="absolute top-20 left-1/4 w-[600px] h-[600px] bg-gradient-to-br from-cyan-500/15 via-teal-500/8 to-transparent rounded-full blur-[120px] animate-pulse" style={{ animationDuration: '8s' }} />
            <div className="absolute bottom-20 right-1/4 w-[500px] h-[500px] bg-gradient-to-tl from-violet-500/15 via-purple-500/8 to-transparent rounded-full blur-[100px] animate-pulse" style={{ animationDuration: '10s' }} />
          </div>
        </div>
      )}

      {showNav && (
        <Navigation
          currentPage={currentPage}
          onNavigate={handleNavigate}
          userMode={userMode}
          onModeChange={setUserMode}
          userEmail={userEmail}
          onLogout={handleLogout}
          isAuthenticated={authenticated}
        />
      )}
      <div className="relative z-10">
        <Routes>
          <Route path="/" element={<LandingPage onNavigate={handleNavigate} isAuthenticated={authenticated} onLogout={handleLogout} />} />
          <Route path="/login" element={<LoginPage onNavigate={handleNavigate} onLogin={handleLogin} />} />
          <Route path="/register" element={<RegisterPage onNavigate={handleNavigate} onLogin={handleLogin} />} />
          <Route path="/dashboard" element={<Dashboard onNavigate={handleNavigate} userMode={userMode} />} />
          <Route path="/verify-media" element={<ImageVideoUpload userMode={userMode} />} />
          <Route path="/verify-article" element={<ArticleVerification userMode={userMode} onNavigate={handleNavigate} isAuthenticated={authenticated} />} />
          <Route path="/investigate" element={<InvestigationPage />} />
          <Route path="/history" element={<HistoryPage onNavigate={handleNavigate} />} />
          <Route path="/projects" element={
            <ComingSoonOverlay title="Projects">
              <ProjectsPage userMode={userMode} />
            </ComingSoonOverlay>
          } />
          <Route path="/organization" element={
            <ComingSoonOverlay title="Enterprise">
              <OrganizationPage />
            </ComingSoonOverlay>
          } />
          <Route path="/settings" element={<SettingsPage onNavigate={handleNavigate} />} />
        </Routes>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <AppContent />
      </ThemeProvider>
    </BrowserRouter>
  );
}

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
  const showNav = authenticated && !['/', '/login', '/register'].includes(location.pathname);

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white">
      {showNav && (
        <Navigation
          currentPage={currentPage}
          onNavigate={handleNavigate}
          userMode={userMode}
          onModeChange={setUserMode}
          userEmail={userEmail}
          onLogout={handleLogout}
        />
      )}
      <Routes>
        <Route path="/" element={<LandingPage onNavigate={handleNavigate} isAuthenticated={authenticated} onLogout={handleLogout} />} />
        <Route path="/login" element={<LoginPage onNavigate={handleNavigate} onLogin={handleLogin} />} />
        <Route path="/register" element={<RegisterPage onNavigate={handleNavigate} onLogin={handleLogin} />} />
        <Route path="/dashboard" element={<Dashboard onNavigate={handleNavigate} userMode={userMode} />} />
        <Route path="/verify-media" element={
          <ComingSoonOverlay title="Media Verification">
            <ImageVideoUpload userMode={userMode} />
          </ComingSoonOverlay>
        } />
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
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

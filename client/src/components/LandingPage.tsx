import { LandingScrollProvider } from './landing/LandingScrollContext';
import { SmoothScroll } from './landing/SmoothScroll';
import { HeroSection } from './landing/HeroSection';
import { BentoGraph } from './landing/BentoGraph';
import { FinalHybridStoryComponent } from './landing/FinalHybridStoryComponent';
import { ScrollDemo } from './landing/ScrollDemo';
import { SiteFooter } from './landing/SiteFooter';
import type { Page } from '../App';

interface LandingPageProps {
  onNavigate: (page: Page) => void;
  isAuthenticated?: boolean;
  onLogout?: () => void;
}

export function LandingPage({ onNavigate, isAuthenticated: _, onLogout: __ }: LandingPageProps) {
  return (
    <LandingScrollProvider>
      <SmoothScroll>
        <HeroSection onNavigate={onNavigate} />
        <FinalHybridStoryComponent />
        <BentoGraph />
        <ScrollDemo />
        <SiteFooter />
      </SmoothScroll>
    </LandingScrollProvider>
  );
}

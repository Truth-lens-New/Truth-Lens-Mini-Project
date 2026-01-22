import { Upload, FileText, ChevronDown, LogIn, UserPlus } from 'lucide-react';
import type { Page } from '../App';

interface LandingPageProps {
  onNavigate: (page: Page) => void;
  isAuthenticated?: boolean;
  onLogout?: () => void;
}

export function LandingPage({ onNavigate, isAuthenticated, onLogout }: LandingPageProps) {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Navbar Removed (Using Global Navigation) */}
      {/* Atmospheric Background */}
      <div className="absolute inset-0 z-0">
        {/* Base gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0A0A0A] via-[#0F1419] to-[#0A0A0A]" />

        {/* Fog-like glows */}
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-[#00FFC3]/10 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-40 right-1/4 w-[500px] h-[500px] bg-[#99F8FF]/8 rounded-full blur-[150px] animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-green-500/5 rounded-full blur-[100px]" />

        {/* Particle network */}
        <svg className="absolute inset-0 w-full h-full opacity-30">
          {[...Array(50)].map((_, i) => {
            const cx = Math.random() * 100;
            const cy = Math.random() * 100;
            const r = Math.random() * 2 + 0.5;
            return (
              <circle
                key={i}
                cx={`${cx}%`}
                cy={`${cy}%`}
                r={r}
                fill="#00FFC3"
                className="animate-pulse"
                style={{ animationDelay: `${Math.random() * 3}s` }}
              />
            );
          })}
          {[...Array(20)].map((_, i) => {
            const x1 = Math.random() * 100;
            const y1 = Math.random() * 100;
            const x2 = Math.random() * 100;
            const y2 = Math.random() * 100;
            return (
              <line
                key={i}
                x1={`${x1}%`}
                y1={`${y1}%`}
                x2={`${x2}%`}
                y2={`${y2}%`}
                stroke="#00FFC3"
                strokeWidth="0.5"
                opacity="0.1"
              />
            );
          })}
        </svg>
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-8">
        {/* Hero Section */}
        <div className="text-center max-w-5xl">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 backdrop-blur-sm border border-white/10 mb-8">
            <div className="w-2 h-2 bg-[#00FFC3] rounded-full animate-pulse" />
            <span className="text-sm text-[#D6D6D6]">Next-Gen Forensic AI</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-7xl mb-6 tracking-tight">
            <span className="block mb-2">Instant Multi-Modal</span>
            <span className="block bg-gradient-to-r from-[#00FFC3] via-white to-[#99F8FF] bg-clip-text text-transparent">
              Truth Verification
            </span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl text-[#D6D6D6] mb-12 max-w-2xl mx-auto">
            Analyze images, videos, and articles with forensic-grade AI.
            <br />
            Detect deepfakes, manipulations, and misinformation instantly.
          </p>

          {/* CTAs */}
          <div className="flex items-center justify-center gap-6 mb-16">
            <button
              onClick={() => onNavigate('verify-media')}
              className="group relative px-8 py-4 rounded-xl bg-gradient-to-r from-[#00FFC3] to-[#99F8FF] text-black overflow-hidden transition-all hover:shadow-[0_0_40px_rgba(0,255,195,0.4)] hover:scale-105"
            >
              <div className="flex items-center gap-3">
                <Upload className="w-5 h-5" />
                <span>Upload Media</span>
              </div>
            </button>

            <button
              onClick={() => onNavigate('verify-article')}
              className="px-8 py-4 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10 hover:bg-white/10 hover:border-[#00FFC3]/30 transition-all flex items-center gap-3"
            >
              <FileText className="w-5 h-5" />
              <span>Verify Article</span>
            </button>
          </div>

          {/* Scroll Indicator */}
          {/* <div className="flex flex-col items-center gap-2 animate-bounce"> */}
          {/* <span className="text-xs text-[#D6D6D6]">Scroll down</span> */}
          {/* <ChevronDown className="w-4 h-4 text-[#00FFC3]" /> */}
          {/* </div> */}
        </div>

        {/* Tech Logos */}
        <div className="absolute bottom-12 left-0 right-0">
          <div className="flex items-center justify-center gap-12 text-[#666] text-sm">
            <div className="opacity-40 hover:opacity-70 transition-opacity">Google Fact Check</div>
            <div className="opacity-40 hover:opacity-70 transition-opacity">HuggingFace</div>
            <div className="opacity-40 hover:opacity-70 transition-opacity">PyTorch</div>
            <div className="opacity-40 hover:opacity-70 transition-opacity">FFmpeg</div>
          </div>
        </div>
      </div>

      {/* Floating orbs */}
      <div className="absolute top-1/4 right-1/4 w-4 h-4 bg-[#00FFC3] rounded-full blur-sm animate-pulse" />
      <div className="absolute bottom-1/3 left-1/3 w-3 h-3 bg-[#99F8FF] rounded-full blur-sm animate-pulse" style={{ animationDelay: '0.5s' }} />
      <div className="absolute top-1/3 left-1/4 w-2 h-2 bg-white rounded-full blur-sm animate-pulse" style={{ animationDelay: '1.5s' }} />
    </div>
  );
}

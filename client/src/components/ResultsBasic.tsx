import { ArrowLeft, Download, CheckCircle2, ShieldAlert, ShieldCheck } from 'lucide-react';
import type { MediaAnalysisResponse } from '../lib/api';
import { ComparisonSlider } from './ComparisonSlider';

interface ResultsBasicProps {
  preview: string | null;
  onBack: () => void;
  analysisResult: MediaAnalysisResponse;
  file: File;
}

export function ResultsBasic({ preview, onBack, analysisResult, file }: ResultsBasicProps) {
  // Slider handles its own state

  const isReal = analysisResult.verdict === 'REAL';
  const verdictText = isReal ? 'LIKELY AUTHENTIC' : 'LIKELY MANIPULATED';
  const VerdictIcon = isReal ? ShieldCheck : ShieldAlert;
  const verdictColor = isReal ? '#00FFC3' : '#FF6B6B';
  const statusText = isReal ? 'Authenticity Verified' : 'Anomalies Detected';

  return (
    <div className="min-h-screen pt-20 pb-12 px-8 bg-gray-50 dark:bg-black transition-colors">
      <div className="fixed inset-0 pointer-events-none">
        <div className={`absolute top-40 left-1/4 w-[500px] h-[500px] ${isReal ? 'bg-[#00FFC3]/10 dark:bg-[#00FFC3]/5' : 'bg-[#FF6B6B]/10 dark:bg-[#FF6B6B]/5'} rounded-full blur-[140px] mix-blend-multiply dark:mix-blend-screen transition-colors duration-700`} />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto">
        <button
          onClick={onBack}
          className="mb-6 px-4 py-2 rounded-lg bg-white/80 dark:bg-white/5 border border-black/5 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/10 transition-colors flex items-center gap-2 text-gray-700 dark:text-gray-200 shadow-sm dark:shadow-none"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        {/* Verdict */}
        <div className="text-center mb-12">
          <div
            className="inline-flex items-center gap-3 px-6 py-3 rounded-full mb-4 bg-white/50 dark:bg-transparent backdrop-blur-sm border transition-colors"
            style={{
              backgroundColor: `${verdictColor}15`,
              borderColor: `${verdictColor}50`,
            }}
          >
            <VerdictIcon className="w-5 h-5" style={{ color: verdictColor }} />
            <span style={{ color: verdictColor, fontWeight: 500 }}>{statusText}</span>
          </div>
          <h1 className="text-5xl mb-4 font-bold tracking-tight" style={{ color: verdictColor }}>{verdictText}</h1>
          <p className="text-lg text-gray-600 dark:text-[#D6D6D6]">Our forensic AI has analyzed your media using {analysisResult.model}</p>
        </div>

        {/* Media Display with Slider */}
        <div className="mb-8 p-1 rounded-3xl backdrop-blur-md bg-white/40 dark:bg-gradient-to-br dark:from-white/10 dark:to-white/5 border border-white/20 dark:border-white/10 overflow-hidden flex justify-center shadow-xl dark:shadow-none min-h-[400px] transition-all">
          {analysisResult.heatmap && preview ? (
            <ComparisonSlider
              original={preview}
              overlay={analysisResult.heatmap}
              labelOriginal="Original Media"
              labelOverlay="AI Heatmap Analysis"
              isVideo={file.type.startsWith('video/')}
            />
          ) : (
            file.type.startsWith('video/') ? (
              <video
                src={preview || ''}
                controls
                className="h-auto max-h-[70vh] w-auto max-w-full object-contain rounded-2xl"
              />
            ) : (
              <img
                src={preview || ''}
                alt="Analysis"
                className="h-auto max-h-[70vh] w-auto max-w-full object-contain rounded-2xl"
              />
            )
          )}
        </div>

        {/* Key Findings */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-center md:text-left">
          <div className="p-6 rounded-2xl backdrop-blur-md bg-white/60 dark:bg-white/5 border border-black/5 dark:border-white/10 shadow-sm dark:shadow-none transition-colors">
            <div className="text-sm text-gray-500 dark:text-muted-foreground mb-2">Model Confidence</div>
            <div className="text-3xl mb-1 font-mono text-gray-900 dark:text-white">{analysisResult.confidence}%</div>
            <div className="text-xs font-semibold" style={{ color: verdictColor }}>
              {analysisResult.confidence_level.charAt(0).toUpperCase() + analysisResult.confidence_level.slice(1)} confidence
            </div>
          </div>

          <div className="p-6 rounded-2xl backdrop-blur-md bg-white/60 dark:bg-white/5 border border-black/5 dark:border-white/10 shadow-sm dark:shadow-none transition-colors">
            <div className="text-sm text-gray-500 dark:text-muted-foreground mb-2">Real Probability</div>
            <div className="text-3xl mb-1 font-mono text-gray-900 dark:text-white">{analysisResult.real_probability}%</div>
            <div className="text-xs text-gray-500 dark:text-muted-foreground">Likelihood of authenticity</div>
          </div>

          <div className="p-6 rounded-2xl backdrop-blur-md bg-white/60 dark:bg-white/5 border border-black/5 dark:border-white/10 shadow-sm dark:shadow-none transition-colors">
            <div className="text-sm text-gray-500 dark:text-muted-foreground mb-2">Fake Probability</div>
            <div className="text-3xl mb-1 font-mono text-gray-900 dark:text-white">{analysisResult.fake_probability}%</div>
            <div className="text-xs text-gray-500 dark:text-muted-foreground">Likelihood of manipulation</div>
          </div>
        </div>

        {/* Recommendation & Evidence */}
        <div
          className="p-8 rounded-2xl backdrop-blur-md border mb-8 bg-white/40 dark:bg-transparent transition-colors"
          style={{
            background: `linear-gradient(to bottom right, ${verdictColor}10, transparent)`,
            borderColor: `${verdictColor}50`
          }}
        >
          <div className="flex items-start gap-4">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: `${verdictColor}30` }}
            >
              <VerdictIcon className="w-5 h-5" style={{ color: verdictColor }} />
            </div>
            <div className="flex-1">
              <h3 className="text-xl mb-2 font-bold" style={{ color: verdictColor }}>{isReal ? 'REAL' : 'FAKE'}</h3>
              <p className="text-gray-700 dark:text-[#D6D6D6] mb-4">
                {isReal
                  ? 'This media shows no signs of manipulation or deepfake artifacts. The image appears to be authentic.'
                  : 'This media shows signs of manipulation or AI-generated content.'}
              </p>

              {/* Evidence List */}
              {analysisResult.evidence && analysisResult.evidence.length > 0 && (
                <div className="mt-4 pt-4 border-t border-black/10 dark:border-white/10">
                  <h4 className="text-sm text-gray-500 dark:text-gray-400 mb-2">Detailed Evidence:</h4>
                  <ul className="space-y-2">
                    {analysisResult.evidence.map((item, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                        <span className="text-[#00FFC3] mt-1">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Feature 4: Real Forensic Metadata */}
        <div className="mb-8 p-8 rounded-2xl backdrop-blur-md bg-white/60 dark:bg-white/5 border border-black/5 dark:border-white/10 shadow-sm dark:shadow-none transition-colors">
          <h3 className="text-xl mb-4 text-gray-900 dark:text-white">Forensic Metadata</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Real File Metadata */}
            <div className="p-3 rounded-lg bg-black/5 dark:bg-black/20 border border-black/5 dark:border-white/5">
              <div className="text-xs text-gray-500 dark:text-muted-foreground uppercase tracking-wider mb-1">File Name</div>
              <div className="text-sm font-mono text-gray-900 dark:text-[#00FFC3] truncate" title={file.name}>{file.name}</div>
            </div>
            <div className="p-3 rounded-lg bg-black/5 dark:bg-black/20 border border-black/5 dark:border-white/5">
              <div className="text-xs text-gray-500 dark:text-muted-foreground uppercase tracking-wider mb-1">File Size</div>
              <div className="text-sm font-mono text-gray-900 dark:text-[#00FFC3]">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
            </div>
            <div className="p-3 rounded-lg bg-black/5 dark:bg-black/20 border border-black/5 dark:border-white/5">
              <div className="text-xs text-gray-500 dark:text-muted-foreground uppercase tracking-wider mb-1">File Type</div>
              <div className="text-sm font-mono text-gray-900 dark:text-[#00FFC3]">{file.type || 'Unknown'}</div>
            </div>
            <div className="p-3 rounded-lg bg-black/5 dark:bg-black/20 border border-black/5 dark:border-white/5">
              <div className="text-xs text-gray-500 dark:text-muted-foreground uppercase tracking-wider mb-1">Last Modified</div>
              <div className="text-sm font-mono text-gray-900 dark:text-[#00FFC3]">{new Date(file.lastModified).toLocaleDateString()}</div>
            </div>

            {/* Backend Metadata (if any) */}
            {analysisResult.metadata && Object.entries(analysisResult.metadata)
              .filter(([key, value]) => {
                // Filter out confusing mock metadata for videos
                if (file.type.startsWith('video/')) {
                  if (key.toLowerCase() === 'format' && ['jpeg', 'png', 'jpg'].includes(String(value).toLowerCase())) return false;
                  if (key.toLowerCase() === 'size') return false; // We already show real size
                }
                return true;
              })
              .map(([key, value]) => (
                <div key={key} className="p-3 rounded-lg bg-black/5 dark:bg-black/20 border border-black/5 dark:border-white/5">
                  <div className="text-xs text-gray-500 dark:text-muted-foreground uppercase tracking-wider mb-1">{key}</div>
                  <div className="text-sm font-mono text-gray-900 dark:text-[#00FFC3] truncate" title={String(value)}>{String(value)}</div>
                </div>
              ))}
          </div>
        </div>

        {/* Export */}
        <button className="w-full py-4 rounded-xl bg-gradient-to-r from-[#00FFC3] to-[#99F8FF] text-black hover:shadow-[0_0_40px_rgba(0,255,195,0.4)] transition-all flex items-center justify-center gap-2 shadow-sm">
          <Download className="w-5 h-5" />
          <span>Export Forensic Report</span>
        </button>
      </div>
    </div>
  );
}

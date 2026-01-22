import { useState } from 'react';
import { ArrowLeft, Download, Eye, EyeOff, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import type { MediaAnalysisResponse } from '../lib/api';

interface ResultsBasicProps {
  preview: string | null;
  onBack: () => void;
  analysisResult: MediaAnalysisResponse;
}

export function ResultsBasic({ preview, onBack, analysisResult }: ResultsBasicProps) {
  const [showHeatmap, setShowHeatmap] = useState(false);

  const isReal = analysisResult.verdict === 'REAL';
  const verdictText = isReal ? 'LIKELY AUTHENTIC' : 'LIKELY MANIPULATED';
  const VerdictIcon = isReal ? CheckCircle2 : XCircle;
  const verdictColor = isReal ? '#00FFC3' : '#FF6B6B';

  return (
    <div className="min-h-screen pt-20 pb-12 px-8">
      <div className="fixed inset-0 pointer-events-none">
        <div className={`absolute top-40 left-1/4 w-[500px] h-[500px] ${isReal ? 'bg-[#00FFC3]/5' : 'bg-[#FF6B6B]/5'} rounded-full blur-[140px]`} />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto">
        <button
          onClick={onBack}
          className="mb-6 px-4 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        {/* Verdict */}
        <div className="text-center mb-12">
          <div
            className="inline-flex items-center gap-3 px-6 py-3 rounded-full mb-4"
            style={{
              backgroundColor: `${verdictColor}15`,
              borderColor: `${verdictColor}50`,
              borderWidth: 1
            }}
          >
            <VerdictIcon className="w-5 h-5" style={{ color: verdictColor }} />
            <span style={{ color: verdictColor }}>Verification Complete</span>
          </div>
          <h1 className="text-5xl mb-4" style={{ color: verdictColor }}>{verdictText}</h1>
          <p className="text-[#D6D6D6]">Our forensic AI has analyzed your media using {analysisResult.model}</p>
        </div>

        {/* Media Display */}
        <div className="mb-8 p-8 rounded-3xl backdrop-blur-md bg-gradient-to-br from-white/10 to-white/5 border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl">Analysis Preview</h2>
            <button
              onClick={() => setShowHeatmap(!showHeatmap)}
              className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors flex items-center gap-2"
            >
              {showHeatmap ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              <span>{showHeatmap ? 'Hide' : 'Show'} Heatmap</span>
            </button>
          </div>

          <div className="relative rounded-xl overflow-hidden">
            <img src={preview || ''} alt="Analysis" className="w-full h-[500px] object-cover" />
            {showHeatmap && (
              <div className={`absolute inset-0 ${isReal ? 'bg-gradient-to-br from-green-500/30 via-green-400/20 to-green-500/30' : 'bg-gradient-to-br from-red-500/30 via-yellow-500/20 to-red-500/30'} backdrop-blur-sm`}>
                <div className="absolute top-4 right-4 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-sm text-xs">
                  Manipulation Probability Heatmap
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Key Findings */}
        <div className="grid grid-cols-3 gap-6 mb-8">
          <div className="p-6 rounded-2xl backdrop-blur-md bg-white/5 border border-white/10">
            <div className="text-sm text-[#D6D6D6] mb-2">Model Confidence</div>
            <div className="text-3xl mb-1">{analysisResult.confidence}%</div>
            <div className="text-xs" style={{ color: verdictColor }}>
              {analysisResult.confidence_level.charAt(0).toUpperCase() + analysisResult.confidence_level.slice(1)} confidence
            </div>
          </div>

          <div className="p-6 rounded-2xl backdrop-blur-md bg-white/5 border border-white/10">
            <div className="text-sm text-[#D6D6D6] mb-2">Real Probability</div>
            <div className="text-3xl mb-1">{analysisResult.real_probability}%</div>
            <div className="text-xs text-[#D6D6D6]">Likelihood of authenticity</div>
          </div>

          <div className="p-6 rounded-2xl backdrop-blur-md bg-white/5 border border-white/10">
            <div className="text-sm text-[#D6D6D6] mb-2">Fake Probability</div>
            <div className="text-3xl mb-1">{analysisResult.fake_probability}%</div>
            <div className="text-xs text-[#D6D6D6]">Likelihood of manipulation</div>
          </div>
        </div>

        {/* Recommendation */}
        <div
          className="p-8 rounded-2xl backdrop-blur-md border mb-8"
          style={{
            background: `linear-gradient(to bottom right, ${verdictColor}15, transparent)`,
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
              <h3 className="text-xl mb-2" style={{ color: verdictColor }}>{isReal ? 'REAL' : 'FAKE'}</h3>
              <p className="text-[#D6D6D6] mb-4">
                {isReal
                  ? 'This media shows no signs of manipulation or deepfake artifacts. The image appears to be authentic.'
                  : 'This media shows signs of manipulation or AI-generated content.'}
              </p>

              {/* Evidence List */}
              {analysisResult.evidence && analysisResult.evidence.length > 0 && (
                <div className="mt-4 pt-4 border-t border-white/10">
                  <h4 className="text-sm text-gray-400 mb-2">Evidence:</h4>
                  <ul className="space-y-2">
                    {analysisResult.evidence.map((item, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-300">
                        <span className="text-[#00FFC3] mt-1">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Heatmap Visualization */}
              {analysisResult.heatmap && (
                <div className="mt-6 pt-4 border-t border-white/10">
                  <h4 className="text-sm text-gray-400 mb-3">Analysis Visualization:</h4>
                  <div className="rounded-xl overflow-hidden border border-white/10 relative group">
                    <img
                      src={analysisResult.heatmap}
                      alt="AI Detection Heatmap"
                      className="w-full h-auto"
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-black/70 p-2 text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity">
                      Heatmap highlights regions that contributed most to the decision
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    * Red/Warm colors indicate areas the model found most suspicious or significant.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Export */}
        <button className="w-full py-4 rounded-xl bg-gradient-to-r from-[#00FFC3] to-[#99F8FF] text-black hover:shadow-[0_0_40px_rgba(0,255,195,0.4)] transition-all flex items-center justify-center gap-2">
          <Download className="w-5 h-5" />
          <span>Export Simple Report</span>
        </button>
      </div>
    </div>
  );
}

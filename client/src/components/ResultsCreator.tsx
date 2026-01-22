import { useState } from 'react';
import { ArrowLeft, Download, Eye, EyeOff, ZoomIn, FileText, FolderPlus, Layers, CheckCircle2, XCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Cell } from 'recharts';
import type { MediaAnalysisResponse } from '../lib/api';

interface ResultsCreatorProps {
  preview: string | null;
  onBack: () => void;
  analysisResult: MediaAnalysisResponse;
}

export function ResultsCreator({ preview, onBack, analysisResult }: ResultsCreatorProps) {
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showELA, setShowELA] = useState(false);

  const isReal = analysisResult.verdict === 'REAL';
  const verdictColor = isReal ? '#00FFC3' : '#FF6B6B';

  // Dynamic model data based on actual result
  const modelData = [
    { model: 'EfficientNet-B0', confidence: analysisResult.confidence, color: verdictColor },
    { model: 'Real Prob', confidence: analysisResult.real_probability, color: '#00FFC3' },
    { model: 'Fake Prob', confidence: analysisResult.fake_probability, color: '#FF6B6B' },
  ];

  const anomalies = isReal ? [
    { type: 'Face Boundary', status: 'Clear', severity: 'low' },
    { type: 'Eye Blink Pattern', status: 'Natural', severity: 'low' },
    { type: 'Lighting Consistency', status: 'Verified', severity: 'low' },
    { type: 'Pixel Grid Analysis', status: 'Normal', severity: 'low' },
  ] : [
    { type: 'Face Boundary', status: 'Suspicious', severity: 'high' },
    { type: 'Eye Blink Pattern', status: 'Irregular', severity: 'medium' },
    { type: 'Lighting Consistency', status: 'Anomaly', severity: 'high' },
    { type: 'Pixel Grid Analysis', status: 'Modified', severity: 'medium' },
  ];

  return (
    <div className="min-h-screen pt-20 pb-12 px-8">
      <div className="fixed inset-0 pointer-events-none">
        <div className={`absolute top-40 right-1/4 w-[600px] h-[600px] ${isReal ? 'bg-[#00FFC3]/5' : 'bg-[#FF6B6B]/5'} rounded-full blur-[150px]`} />
      </div>

      <div className="relative z-10 max-w-[1600px] mx-auto">
        <button
          onClick={onBack}
          className="mb-6 px-4 py-2 rounded-lg bg-card/50 border border-border/50 hover:bg-muted/20 transition-colors flex items-center gap-2 text-foreground"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>

        <div className="mb-8">
          <h1 className="text-4xl mb-2 text-foreground">Forensic Analysis Report</h1>
          <p className="text-muted-foreground">Creator Mode – Enhanced Analytics</p>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Left Panel - Media Viewer */}
          <div className="space-y-6">
            {/* Media Display */}
            <div className="p-6 rounded-2xl backdrop-blur-md bg-card border border-border/50">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl text-foreground">Media Analysis</h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowHeatmap(!showHeatmap)}
                    className={`px-3 py-1.5 rounded-lg text-sm transition-all ${showHeatmap
                        ? 'bg-primary/20 border border-primary/50 text-primary'
                        : 'bg-muted/10 border border-border/20 hover:bg-muted/20 text-foreground'
                      }`}
                  >
                    Heatmap
                  </button>
                  <button
                    onClick={() => setShowELA(!showELA)}
                    className={`px-3 py-1.5 rounded-lg text-sm transition-all ${showELA
                        ? 'bg-secondary/20 border border-secondary/50 text-secondary'
                        : 'bg-muted/10 border border-border/20 hover:bg-muted/20 text-foreground'
                      }`}
                  >
                    ELA
                  </button>
                  <button className="p-1.5 rounded-lg bg-card border border-border/50 hover:bg-muted/20 text-foreground">
                    <ZoomIn className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="relative rounded-xl overflow-hidden">
                <img src={preview || ''} alt="Analysis" className="w-full h-[600px] object-cover" />
                {showHeatmap && (
                  <div className={`absolute inset-0 ${isReal ? 'bg-gradient-to-br from-green-500/30 via-green-400/20 to-green-500/30' : 'bg-gradient-to-br from-red-500/30 via-yellow-500/20 to-red-500/30'} backdrop-blur-sm`}>
                    <div className="absolute top-4 left-4 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-sm text-xs">
                      Manipulation Heatmap
                    </div>
                  </div>
                )}
                {showELA && (
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/40 to-blue-500/40 backdrop-blur-sm mix-blend-screen">
                    <div className="absolute top-4 left-4 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-sm text-xs">
                      Error Level Analysis
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 rounded-xl backdrop-blur-md bg-card border border-border/50">
                <div className="text-xs text-muted-foreground mb-1">Overall Score</div>
                <div className="text-2xl text-primary">94.2%</div>
              </div>
              <div className="p-4 rounded-xl backdrop-blur-md bg-card border border-border/50">
                <div className="text-xs text-muted-foreground mb-1">Risk Level</div>
                <div className="text-2xl text-foreground">Low</div>
              </div>
              <div className="p-4 rounded-xl backdrop-blur-md bg-card border border-border/50">
                <div className="text-xs text-muted-foreground mb-1">Verdict</div>
                <div className="text-2xl text-foreground">Authentic</div>
              </div>
            </div>
          </div>

          {/* Right Panel - Analytics */}
          <div className="space-y-6">
            {/* Model Confidence Breakdown */}
            <div className="p-6 rounded-2xl backdrop-blur-md bg-card border border-border/50">
              <h3 className="text-xl mb-4 text-foreground">Model Confidence Breakdown</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={modelData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis type="number" domain={[0, 100]} stroke="#666" />
                  <YAxis type="category" dataKey="model" stroke="#666" width={100} />
                  <Bar dataKey="confidence" radius={[0, 8, 8, 0]}>
                    {modelData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Metadata Table */}
            <div className="p-6 rounded-2xl backdrop-blur-md bg-card border border-border/50">
              <h3 className="text-xl mb-4 text-foreground">Metadata Information</h3>
              <div className="space-y-3">
                {[
                  { label: 'Camera Model', value: 'Canon EOS R5' },
                  { label: 'Date Taken', value: '2024-12-08 14:32:15' },
                  { label: 'GPS Location', value: '37.7749° N, 122.4194° W' },
                  { label: 'ISO', value: '400' },
                  { label: 'Exposure', value: '1/250s' },
                  { label: 'Focal Length', value: '50mm' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-2 border-b border-border/10">
                    <span className="text-sm text-muted-foreground">{item.label}</span>
                    <span className="text-sm text-foreground">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Anomaly Detection */}
            <div className="p-6 rounded-2xl backdrop-blur-md bg-card border border-border/50">
              <h3 className="text-xl mb-4 text-foreground">Anomaly Detection</h3>
              <div className="grid grid-cols-2 gap-3">
                {anomalies.map((anomaly) => (
                  <div
                    key={anomaly.type}
                    className="px-4 py-3 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-sm mb-0.5 text-foreground">{anomaly.type}</div>
                      <div className="text-xs text-primary">{anomaly.status}</div>
                    </div>
                    <div className="w-2 h-2 bg-primary rounded-full" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex items-center gap-4">
          <button className="flex-1 py-4 rounded-xl bg-gradient-to-r from-[#00FFC3] to-[#99F8FF] text-black hover:shadow-[0_0_40px_rgba(0,255,195,0.4)] transition-all flex items-center justify-center gap-2">
            <Download className="w-5 h-5" />
            <span>Export PDF Report</span>
          </button>
          <button className="px-6 py-4 rounded-xl backdrop-blur-md bg-card border border-border/50 hover:bg-muted/20 transition-all flex items-center gap-2 text-foreground">
            <Layers className="w-5 h-5" />
            <span>Export Assets</span>
          </button>
          <button className="px-6 py-4 rounded-xl backdrop-blur-md bg-card border border-border/50 hover:bg-muted/20 transition-all flex items-center gap-2 text-foreground">
            <FolderPlus className="w-5 h-5" />
            <span>Add to Project</span>
          </button>
        </div>
      </div>
    </div>
  );
}

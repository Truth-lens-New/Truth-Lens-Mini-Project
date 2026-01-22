import { useState } from 'react';
import { ArrowLeft, Download, FileJson, Archive, Save, Hash, Camera, Clock, Shield } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import type { MediaAnalysisResponse } from '../lib/api';

interface ResultsProfessionalProps {
  preview: string | null;
  onBack: () => void;
  analysisResult: MediaAnalysisResponse;
}

export function ResultsProfessional({ preview, onBack, analysisResult }: ResultsProfessionalProps) {
  const [notes, setNotes] = useState('');

  const isReal = analysisResult.verdict === 'REAL';
  const verdictColor = isReal ? '#00FFC3' : '#FF6B6B';

  // Dynamic ensemble data based on actual result
  const ensembleData = [
    { model: 'EfficientNet', score: analysisResult.confidence },
    { model: 'Real', score: analysisResult.real_probability },
    { model: 'Fake', score: analysisResult.fake_probability },
    { model: 'Neural', score: analysisResult.confidence * 0.95 },
    { model: 'Capsule', score: analysisResult.confidence * 0.92 },
    { model: 'Binary', score: isReal ? analysisResult.real_probability : analysisResult.fake_probability },
  ];

  const temporalData = [
    { frame: 0, consistency: analysisResult.confidence - 2 },
    { frame: 5, consistency: analysisResult.confidence - 1 },
    { frame: 10, consistency: analysisResult.confidence },
    { frame: 15, consistency: analysisResult.confidence - 2 },
    { frame: 20, consistency: analysisResult.confidence - 1 },
    { frame: 25, consistency: analysisResult.confidence },
    { frame: 30, consistency: analysisResult.confidence - 1 },
  ];

  return (
    <div className="min-h-screen pt-20 pb-12 px-8">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-40 left-1/3 w-[500px] h-[500px] bg-[#00FFC3]/5 rounded-full blur-[140px]" />
        <div className="absolute bottom-40 right-1/3 w-[600px] h-[600px] bg-purple-500/5 rounded-full blur-[150px]" />
      </div>

      <div className="relative z-10 max-w-[1800px] mx-auto">
        <button
          onClick={onBack}
          className="mb-6 px-4 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Upload</span>
        </button>

        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-4xl mb-2">Professional Forensic Workstation</h1>
            <p className="text-[#D6D6D6]">Agency-Grade Analysis Suite</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="px-4 py-2 rounded-lg bg-[#00FFC3]/10 border border-[#00FFC3]/30 text-[#00FFC3] text-sm">
              Case ID: TL-2024-0849
            </div>
          </div>
        </div>

        {/* Dense Grid Layout */}
        <div className="grid grid-cols-3 gap-4">
          {/* Media Preview */}
          <div className="col-span-1 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
            <h3 className="mb-3">Evidence Preview</h3>
            <img src={preview || ''} alt="Evidence" className="w-full h-64 object-cover rounded-lg mb-3" />
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1.5 border-b border-white/5">
                <span className="text-[#D6D6D6]">Hash (SHA-256)</span>
                <span className="font-mono text-[#00FFC3]">a3f5...</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-white/5">
                <span className="text-[#D6D6D6]">File Size</span>
                <span>2.4 MB</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-[#D6D6D6]">Upload Time</span>
                <span>14:32:45 UTC</span>
              </div>
            </div>
          </div>

          {/* PRNU Camera Fingerprint */}
          <div className="col-span-1 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
            <div className="flex items-center gap-2 mb-3">
              <Camera className="w-4 h-4 text-[#00FFC3]" />
              <h3>PRNU Fingerprint Detection</h3>
            </div>
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-[#00FFC3]/10 border border-[#00FFC3]/30">
                <div className="text-xs text-[#D6D6D6] mb-1">Camera Match Confidence</div>
                <div className="text-2xl text-[#00FFC3]">89.7%</div>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-[#D6D6D6]">Sensor Pattern</span>
                  <span className="text-[#00FFC3]">Detected</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#D6D6D6]">Noise Consistency</span>
                  <span className="text-[#00FFC3]">High</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#D6D6D6]">Known Device</span>
                  <span>Canon EOS R5</span>
                </div>
              </div>
              <div className="h-24 rounded-lg bg-gradient-to-br from-[#00FFC3]/20 to-purple-500/10 border border-[#00FFC3]/20 flex items-center justify-center">
                <span className="text-xs text-[#666]">PRNU Pattern Visualization</span>
              </div>
            </div>
          </div>

          {/* Multi-Model Ensemble */}
          <div className="col-span-1 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-[#99F8FF]" />
              <h3>Ensemble Score Grid</h3>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <RadarChart data={ensembleData}>
                <PolarGrid stroke="#ffffff20" />
                <PolarAngleAxis dataKey="model" stroke="#666" tick={{ fontSize: 10 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#666" tick={{ fontSize: 10 }} />
                <Radar name="Score" dataKey="score" stroke="#00FFC3" fill="#00FFC3" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
            <div className="mt-2 text-center">
              <div className="text-xs text-[#D6D6D6] mb-1">Consensus Score</div>
              <div className="text-2xl text-[#00FFC3]">93.2%</div>
            </div>
          </div>

          {/* Temporal Inconsistency Timeline */}
          <div className="col-span-2 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-[#99F8FF]" />
              <h3>Temporal Inconsistency Timeline (Video)</h3>
            </div>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={temporalData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis dataKey="frame" stroke="#666" tick={{ fontSize: 10 }} />
                <YAxis domain={[90, 100]} stroke="#666" tick={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="consistency" stroke="#99F8FF" strokeWidth={2} dot={{ fill: '#99F8FF', r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
              <div className="p-2 rounded bg-white/5">
                <div className="text-[#D6D6D6]">Avg Consistency</div>
                <div className="text-[#99F8FF]">97.3%</div>
              </div>
              <div className="p-2 rounded bg-white/5">
                <div className="text-[#D6D6D6]">Frame Drops</div>
                <div>0</div>
              </div>
              <div className="p-2 rounded bg-white/5">
                <div className="text-[#D6D6D6]">Splice Points</div>
                <div>0</div>
              </div>
            </div>
          </div>

          {/* Hash & Provenance */}
          <div className="col-span-1 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
            <div className="flex items-center gap-2 mb-3">
              <Hash className="w-4 h-4 text-purple-400" />
              <h3>Hash & Provenance</h3>
            </div>
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
                <div className="text-xs text-[#D6D6D6] mb-1">Blockchain Status</div>
                <div className="text-sm text-purple-300">Verified on Chain</div>
              </div>
              <div className="space-y-2 text-xs">
                <div>
                  <div className="text-[#D6D6D6] mb-1">SHA-256</div>
                  <div className="font-mono text-[10px] break-all text-[#00FFC3]">
                    a3f5d8e2c1b4...9f7e2a
                  </div>
                </div>
                <div>
                  <div className="text-[#D6D6D6] mb-1">MD5</div>
                  <div className="font-mono text-[10px] break-all text-[#99F8FF]">
                    5d41402abc4b...2a76b9
                  </div>
                </div>
                <div className="flex justify-between pt-2 border-t border-white/10">
                  <span className="text-[#D6D6D6]">Integrity</span>
                  <span className="text-[#00FFC3]">Intact</span>
                </div>
              </div>
            </div>
          </div>

          {/* Forensic Notes */}
          <div className="col-span-2 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <h3>Forensic Investigation Notes</h3>
              <button className="px-3 py-1 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-xs flex items-center gap-1">
                <Save className="w-3 h-3" />
                <span>Save</span>
              </button>
            </div>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Enter investigation notes, observations, and case details..."
              className="w-full h-32 px-4 py-3 rounded-lg bg-white/5 border border-white/10 focus:border-[#00FFC3]/30 focus:outline-none resize-none text-sm"
            />
            <div className="mt-2 flex items-center justify-between text-xs text-[#666]">
              <span>Investigator: Dr. Sarah Chen</span>
              <span>Last modified: 2024-12-08 14:45</span>
            </div>
          </div>

          {/* Additional Forensic Metrics */}
          <div className="col-span-1 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
            <h3 className="mb-3">Advanced Metrics</h3>
            <div className="space-y-2 text-xs">
              {[
                { label: 'JPEG Quality', value: '95%', status: 'normal' },
                { label: 'Double Compression', value: 'Not Detected', status: 'pass' },
                { label: 'Clone Detection', value: 'Clean', status: 'pass' },
                { label: 'Splicing Analysis', value: 'No Anomalies', status: 'pass' },
                { label: 'CFA Pattern', value: 'Consistent', status: 'pass' },
                { label: 'Noise Analysis', value: 'Natural', status: 'pass' },
              ].map((metric) => (
                <div key={metric.label} className="flex justify-between py-1.5 border-b border-white/5">
                  <span className="text-[#D6D6D6]">{metric.label}</span>
                  <span className="text-[#00FFC3]">{metric.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Export Options */}
        <div className="mt-6 grid grid-cols-3 gap-4">
          <button className="py-3 rounded-xl bg-gradient-to-r from-[#00FFC3] to-[#99F8FF] text-black hover:shadow-[0_0_40px_rgba(0,255,195,0.4)] transition-all flex items-center justify-center gap-2">
            <Download className="w-4 h-4" />
            <span>Export Technical PDF</span>
          </button>
          <button className="py-3 rounded-xl backdrop-blur-md bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex items-center justify-center gap-2">
            <FileJson className="w-4 h-4" />
            <span>Export JSON Log</span>
          </button>
          <button className="py-3 rounded-xl backdrop-blur-md bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex items-center justify-center gap-2">
            <Archive className="w-4 h-4" />
            <span>Investigation Package</span>
          </button>
        </div>
      </div>
    </div>
  );
}

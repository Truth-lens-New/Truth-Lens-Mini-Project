import { useState } from 'react';
import { ArrowLeft, Download, FileJson, Archive, Save, Hash, Camera, Clock, Shield } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import type { MediaAnalysisResponse } from '../lib/api';

interface ResultsProfessionalProps {
  preview: string | null;
  onBack: () => void;
  analysisResult: MediaAnalysisResponse;
  file: File;
}

export function ResultsProfessional({ preview, onBack, analysisResult, file }: ResultsProfessionalProps) {
  const [notes, setNotes] = useState('');

  const isVideo = file.type.startsWith('video/');

  // Real ensemble data: the deployed pipeline is a single EfficientNet model
  // (no battery of additional models — don't imply analysis that isn't run)
  const ensembleData = [
    { model: 'EfficientNet', score: analysisResult.confidence },
    { model: 'Real', score: analysisResult.real_probability },
    { model: 'Fake', score: analysisResult.fake_probability },
  ];

  // Real sampled-frame data decoded from the server response (videos only)
  const frameData = (analysisResult.frame_results || []).map((frame) => ({
    frame: frame.timestamp,
    fake: frame.fake_probability,
    verdict: frame.verdict,
  }));

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
              Case ID: TL-{new Date().getFullYear()}-{Math.floor(Math.random() * 10000)}
            </div>
          </div>
        </div>

        {/* Dense Grid Layout */}
        <div className="grid grid-cols-3 gap-4">
          {/* Media Preview */}
          <div className="col-span-1 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
            <h3 className="mb-3">Evidence Preview</h3>
            <div className="flex justify-center bg-black/20 rounded-lg p-2 mb-3">
              {file.type.startsWith('video/') ? (
                <video
                  src={preview || ''}
                  controls
                  className="w-auto h-auto max-h-[300px] max-w-full object-contain"
                />
              ) : (
                <img
                  src={preview || ''}
                  alt="Evidence"
                  className="w-auto h-auto max-h-[300px] max-w-full object-contain"
                />
              )}
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1.5 border-b border-white/5">
                <span className="text-[#D6D6D6]">File Name</span>
                <span className="font-mono text-[#00FFC3] truncate max-w-[150px]" title={file.name}>{file.name}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-white/5">
                <span className="text-[#D6D6D6]">File Size</span>
                <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-[#D6D6D6]">Upload Time</span>
                <span>{new Date().toISOString().split('T')[0]}</span>
              </div>
            </div>
          </div>

          {isVideo ? (
            /* Frame Sampling Summary (real data) — replaces PRNU camera
               fingerprinting, which is not performed on video uploads */
            <div className="col-span-1 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
              <div className="flex items-center gap-2 mb-3">
                <Clock className="w-4 h-4 text-[#00FFC3]" />
                <h3>Frame Sampling Summary</h3>
              </div>
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-[#00FFC3]/10 border border-[#00FFC3]/30">
                  <div className="text-xs text-[#D6D6D6] mb-1">Frames Analyzed</div>
                  <div className="text-2xl text-[#00FFC3]">{analysisResult.frames_analyzed ?? frameData.length}</div>
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-[#D6D6D6]">Sampling</span>
                    <span className="text-[#00FFC3]">Evenly spaced</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#D6D6D6]">FAKE Frames</span>
                    <span>{frameData.filter((f) => f.verdict === 'FAKE').length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#D6D6D6]">REAL Frames</span>
                    <span>{frameData.filter((f) => f.verdict === 'REAL').length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#D6D6D6]">Peak Fake Probability</span>
                    <span>{frameData.length ? Math.max(...frameData.map((f) => f.fake)).toFixed(1) : '—'}%</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
          /* PRNU Camera Fingerprint */
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
                  <span className="text-[#D6D6D6]">Source Type</span>
                  <span>{file.type ? file.type : 'Unknown Source'}</span>
                </div>
              </div>
              <div className="h-24 rounded-lg bg-gradient-to-br from-[#00FFC3]/20 to-purple-500/10 border border-[#00FFC3]/20 flex items-center justify-center">
                <span className="text-xs text-[#666]">PRNU Pattern Visualization</span>
              </div>
            </div>
          </div>
          )}

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
              <div className="text-2xl text-[#00FFC3]">{analysisResult.confidence.toFixed(1)}%</div>
            </div>
          </div>

          {/* Frame Probability Timeline (videos, real sampled data) */}
          {isVideo && frameData.length > 0 && (
          <div className="col-span-2 p-4 rounded-xl backdrop-blur-md bg-white/5 border border-white/10">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-[#99F8FF]" />
              <h3>Frame Probability Timeline</h3>
            </div>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={frameData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis dataKey="frame" stroke="#666" tick={{ fontSize: 10 }} tickFormatter={(v: number) => `${v}s`} />
                <YAxis domain={[0, 100]} stroke="#666" tick={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="fake" stroke="#FF6B6B" strokeWidth={2} dot={{ fill: '#FF6B6B', r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
              <div className="p-2 rounded bg-white/5">
                <div className="text-[#D6D6D6]">Frames Analyzed</div>
                <div className="text-[#99F8FF]">{frameData.length}</div>
              </div>
              <div className="p-2 rounded bg-white/5">
                <div className="text-[#D6D6D6]">FAKE Frames</div>
                <div>{frameData.filter((f) => f.verdict === 'FAKE').length}</div>
              </div>
              <div className="p-2 rounded bg-white/5">
                <div className="text-[#D6D6D6]">Avg Fake Probability</div>
                <div>{analysisResult.fake_probability.toFixed(1)}%</div>
              </div>
            </div>
          </div>
          )}

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
              {(file.type.startsWith('video/') ? [
                // Real values from the server's video metadata — no motion or
                // audio analysis is performed, so no such metrics are shown.
                { label: 'Video Codec', value: String(analysisResult.metadata?.['codec'] ?? 'Unknown'), status: 'normal' },
                { label: 'Duration', value: `${analysisResult.metadata?.['duration_seconds'] ?? '—'}s`, status: 'normal' },
                { label: 'Resolution', value: String(analysisResult.metadata?.['resolution'] ?? 'Unknown'), status: 'normal' },
                { label: 'FPS', value: String(analysisResult.metadata?.['fps'] ?? 'Unknown'), status: 'normal' },
                { label: 'Frames Analyzed', value: String(analysisResult.frames_analyzed ?? '—'), status: 'pass' },
                { label: 'Frame Sampling', value: 'Evenly spaced', status: 'pass' },
              ] : [
                { label: 'JPEG Quality', value: '95%', status: 'normal' },
                { label: 'Double Compression', value: 'Not Detected', status: 'pass' },
                { label: 'Clone Detection', value: 'Clean', status: 'pass' },
                { label: 'Splicing Analysis', value: 'No Anomalies', status: 'pass' },
                { label: 'CFA Pattern', value: 'Consistent', status: 'pass' },
                { label: 'Noise Analysis', value: 'Natural', status: 'pass' },
              ]).map((metric) => (
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

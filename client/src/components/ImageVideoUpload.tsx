import { useState } from 'react';
import { Upload, Image, Video, X, Loader2, AlertCircle } from 'lucide-react';
import { ResultsBasic } from './ResultsBasic';
import { ResultsCreator } from './ResultsCreator';
import { ResultsProfessional } from './ResultsProfessional';
import type { UserMode } from '../App';
import { analyzeMedia, type MediaAnalysisResponse } from '../lib/api';

interface ImageVideoUploadProps {
  userMode: UserMode;
}

type ProcessingStep = 'preprocessing' | 'deepfake' | 'forensic' | 'heatmap' | 'verdict';

const steps: { id: ProcessingStep; label: string }[] = [
  { id: 'preprocessing', label: 'Preprocessing' },
  { id: 'deepfake', label: 'Deepfake Model' },
  { id: 'forensic', label: 'Forensic Checks' },
  { id: 'heatmap', label: 'Heatmap Generation' },
  { id: 'verdict', label: 'Final Verdict' },
];

export function ImageVideoUpload({ userMode }: ImageVideoUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState<ProcessingStep>('preprocessing');
  const [showResults, setShowResults] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<MediaAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file: File) => {
    setFile(file);
    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setProcessing(true);
    setError(null);
    setCurrentStep('preprocessing');

    try {
      // Show preprocessing step
      await new Promise(resolve => setTimeout(resolve, 500));
      setCurrentStep('deepfake');

      // Call the real API
      const result = await analyzeMedia(file);

      // Show remaining steps for UX
      await new Promise(resolve => setTimeout(resolve, 300));
      setCurrentStep('forensic');
      await new Promise(resolve => setTimeout(resolve, 300));
      setCurrentStep('heatmap');
      await new Promise(resolve => setTimeout(resolve, 300));
      setCurrentStep('verdict');
      await new Promise(resolve => setTimeout(resolve, 300));

      setAnalysisResult(result);
      setShowResults(true);
    } catch (err) {
      console.error('Analysis failed:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const handleBack = () => {
    setShowResults(false);
    setAnalysisResult(null);
  };

  if (showResults && file && analysisResult) {
    if (userMode === 'Basic') {
      return <ResultsBasic preview={preview} onBack={handleBack} analysisResult={analysisResult} />;
    } else if (userMode === 'Creator') {
      return <ResultsCreator preview={preview} onBack={handleBack} analysisResult={analysisResult} />;
    } else {
      return <ResultsProfessional preview={preview} onBack={handleBack} analysisResult={analysisResult} />;
    }
  }

  return (
    <div className="min-h-screen pt-20 pb-12 px-8">
      {/* Background effects */}


      <div className="relative z-10 max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl mb-3 text-foreground">Media Verification</h1>
          <p className="text-muted-foreground">Upload an image or video for forensic analysis</p>
        </div>

        {processing ? (
          // Processing Screen
          <div className="p-12 rounded-3xl backdrop-blur-md bg-gradient-to-br from-card/80 to-card/40 border border-border/50">
            <div className="text-center mb-12">
              <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-black animate-spin" />
              </div>
              <h2 className="text-2xl mb-2 text-foreground">Analyzing Media</h2>
              <p className="text-muted-foreground">Running forensic verification pipeline...</p>
            </div>

            {/* Processing Steps */}
            <div className="space-y-3">
              {steps.map((step, index) => {
                const isActive = step.id === currentStep;
                const isComplete = steps.findIndex(s => s.id === currentStep) > index;

                return (
                  <div
                    key={step.id}
                    className={`p-4 rounded-xl backdrop-blur-sm transition-all ${isActive
                      ? 'bg-white/10 border border-[#00FFC3]/30'
                      : isComplete
                        ? 'bg-white/5 border border-white/10'
                        : 'bg-white/[0.02] border border-white/5'
                      }`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isActive
                        ? 'bg-gradient-to-br from-[#00FFC3] to-[#99F8FF]'
                        : isComplete
                          ? 'bg-[#00FFC3]/20 border border-[#00FFC3]'
                          : 'bg-white/5'
                        }`}>
                        {isActive ? (
                          <Loader2 className="w-5 h-5 text-black animate-spin" />
                        ) : isComplete ? (
                          <div className="w-2 h-2 bg-[#00FFC3] rounded-full" />
                        ) : (
                          <span className="text-sm text-[#666]">{index + 1}</span>
                        )}
                      </div>
                      <div className="flex-1">
                        <div className={`${isActive || isComplete ? 'text-foreground' : 'text-muted-foreground'}`}>
                          {step.label}
                        </div>
                      </div>
                      {isActive && (
                        <div className="flex gap-1">
                          {[...Array(3)].map((_, i) => (
                            <div
                              key={i}
                              className="w-1.5 h-1.5 bg-[#00FFC3] rounded-full animate-pulse"
                              style={{ animationDelay: `${i * 0.2}s` }}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                    {isActive && (
                      <div className="mt-3 ml-14">
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-[#00FFC3] to-[#99F8FF] rounded-full animate-pulse" style={{ width: '70%' }} />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ) : file && preview ? (
          // File Selected
          <div className="space-y-6">
            <div className="p-8 rounded-3xl backdrop-blur-md bg-gradient-to-br from-white/10 to-white/5 border border-white/10 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-[#00FFC3]/5 to-transparent" />

              <div className="relative flex items-start gap-6">
                <div className="flex-1">
                  <img
                    src={preview}
                    alt="Preview"
                    className="w-full h-80 object-cover rounded-xl"
                  />
                </div>
                <div className="flex-1 space-y-4">
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">File Name</div>
                    <div className="text-lg text-foreground">{file.name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">File Size</div>
                    <div className="text-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                  </div>
                  <div>
                    <div className="text-sm text-[#D6D6D6] mb-1">Type</div>
                    <div>{file.type.includes('video') ? 'Video' : 'Image'}</div>
                  </div>

                  <button
                    onClick={() => {
                      setFile(null);
                      setPreview(null);
                    }}
                    className="mt-6 px-4 py-2 rounded-lg bg-card/50 border border-border/50 hover:bg-muted/20 transition-colors flex items-center gap-2 text-foreground"
                  >
                    <X className="w-4 h-4" />
                    <span>Remove</span>
                  </button>
                </div>
              </div>
            </div>

            <button
              onClick={handleAnalyze}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-[#00FFC3] to-[#99F8FF] text-black hover:shadow-[0_0_40px_rgba(0,255,195,0.4)] transition-all"
            >
              Start Forensic Analysis
            </button>
          </div>
        ) : (
          // Upload Area
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`p-20 rounded-3xl backdrop-blur-md bg-gradient-to-br from-white/10 to-white/5 border-2 border-dashed transition-all relative overflow-hidden ${dragActive ? 'border-[#00FFC3] bg-[#00FFC3]/5' : 'border-white/20'
              }`}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-[#00FFC3]/5 via-transparent to-[#99F8FF]/5 opacity-50" />

            <div className="relative text-center">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[#00FFC3]/20 to-[#99F8FF]/20 border border-[#00FFC3]/30 flex items-center justify-center">
                <Upload className="w-10 h-10 text-[#00FFC3]" />
              </div>

              <h2 className="text-2xl mb-3">Drop your media here</h2>
              <p className="text-[#D6D6D6] mb-6">or click to browse files</p>

              <input
                type="file"
                accept="image/*,video/*"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-flex items-center gap-3 px-6 py-3 rounded-xl bg-card border border-border/50 hover:bg-muted/20 cursor-pointer transition-all text-foreground"
              >
                <Image className="w-5 h-5" />
                <span>Select Image</span>
              </label>

              <div className="mt-8 flex items-center justify-center gap-6 text-xs text-[#666]">
                <div className="flex items-center gap-2">
                  <Image className="w-4 h-4" />
                  <span>JPG, PNG</span>
                </div>
                <div className="flex items-center gap-2">
                  <Video className="w-4 h-4" />
                  <span>MP4, 0–30s videos</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

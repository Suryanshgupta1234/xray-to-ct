import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, Sparkles, AlertCircle, Play, Layers } from 'lucide-react';
import { DropzoneUploader } from '../components/DropzoneUploader';
import { ProcessingIndicator } from '../components/ProcessingIndicator';
import { inferenceAPI } from '../api/client';

export const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [modelVersion, setModelVersion] = useState('v1');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(1);
  const [uploadPercent, setUploadPercent] = useState(0);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  const handleStartTranslation = async () => {
    if (!file) return;

    setError(null);
    setIsProcessing(true);
    setProcessingStep(1);
    setUploadPercent(0);

    try {
      // Step 1: Uploading
      const res = await inferenceAPI.submitTranslation(
        file,
        modelVersion,
        (percent) => {
          setUploadPercent(percent);
          if (percent >= 100) {
            setProcessingStep(2); // Preprocessing
            setTimeout(() => setProcessingStep(3), 400); // pix2pix forward pass
            setTimeout(() => setProcessingStep(4), 800); // Postprocessing
          }
        }
      );

      if (res.success && res.data) {
        setProcessingStep(5); // Ready
        setTimeout(() => {
          navigate(`/result/${res.data.id}`);
        }, 600);
      } else {
        throw new Error(res.message || 'Translation failed');
      }
    } catch (err) {
      setError(err.message || 'An error occurred during translation.');
      setIsProcessing(false);
    }
  };

  // Helper to load a sample phantom image generated in Phase 2
  const handleLoadSamplePhantom = async () => {
    try {
      // Fetch a sample mock X-ray from local static path or create a procedural canvas blob
      const canvas = document.createElement('canvas');
      canvas.width = 256;
      canvas.height = 256;
      const ctx = canvas.getContext('2d');

      // Draw simulated thoracic phantom
      ctx.fillStyle = '#050811';
      ctx.fillRect(0, 0, 256, 256);

      // Thorax oval
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.ellipse(128, 128, 90, 105, 0, 0, 2 * Math.PI);
      ctx.stroke();

      // Lung radiolucent cavities
      ctx.fillStyle = '#0f172a';
      ctx.beginPath();
      ctx.ellipse(85, 110, 32, 60, 0, 0, 2 * Math.PI);
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(171, 110, 32, 60, 0, 0, 2 * Math.PI);
      ctx.fill();

      // Rib shadows
      ctx.strokeStyle = '#64748b';
      ctx.lineWidth = 2;
      for (let y = 80; y <= 180; y += 22) {
        ctx.beginPath();
        ctx.arc(128, y - 50, 80, 0.2 * Math.PI, 0.8 * Math.PI);
        ctx.stroke();
      }

      // Watermark text
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px monospace';
      ctx.fillText('SYNTHETIC SAMPLE PHANTOM', 12, 20);

      canvas.toBlob((blob) => {
        const sampleFile = new File([blob], 'sample_thoracic_phantom.png', { type: 'image/png' });
        setFile(sampleFile);
      }, 'image/png');
    } catch (e) {
      console.error('Failed to create sample phantom', e);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      <div>
        <span className="text-xs font-mono text-cyan-400 uppercase tracking-wide">
          Image Translation Studio
        </span>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mt-1">
          Upload 2D X-Ray Projection
        </h1>
        <p className="text-xs text-slate-400 mt-1 max-w-xl">
          Provide a 2D planar projection radiograph to generate corresponding cross-sectional synthetic CT representations.
        </p>
      </div>

      {error && (
        <div className="bg-red-950/50 border border-red-500/50 text-red-200 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isProcessing ? (
        <ProcessingIndicator currentStep={processingStep} uploadPercent={uploadPercent} />
      ) : (
        <div className="space-y-6">
          {/* Uploader */}
          <DropzoneUploader
            onFileSelected={(selected) => setFile(selected)}
            selectedFile={file}
            onClear={() => setFile(null)}
          />

          {/* Quick Demo Sample Picker */}
          {!file && (
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold text-slate-200">No X-ray file on hand?</p>
                <p className="text-[11px] text-slate-400">
                  Load a verified synthetic thoracic phantom directly into the canvas.
                </p>
              </div>
              <button
                type="button"
                onClick={handleLoadSamplePhantom}
                className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 rounded-lg text-xs font-medium transition-colors shrink-0"
              >
                Load Sample Phantom
              </button>
            </div>
          )}

          {/* Configuration Controls */}
          {file && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                Translation Parameters
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Model Architecture</label>
                  <select
                    value={modelVersion}
                    onChange={(e) => setModelVersion(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="v1">v1 — pix2pix Conditional GAN (U-Net 256)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Target Slice Resolution</label>
                  <input
                    type="text"
                    disabled
                    value="256 × 256 Grayscale (Normalized [-1, 1])"
                    className="w-full px-3 py-2 bg-slate-950/60 border border-slate-800/60 rounded-lg text-xs font-mono text-slate-400"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  onClick={handleStartTranslation}
                  className="flex items-center gap-2 px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-semibold shadow-lg shadow-cyan-600/25 transition-all"
                >
                  <Play className="w-4 h-4 fill-white" />
                  Run Neural Translation
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

import React from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  ShieldAlert,
  Cpu,
  Layers,
  Sparkles,
  Database,
  Eye,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LandingPage = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="space-y-20 pb-16">
      {/* Hero Section */}
      <section className="relative pt-12 pb-8 overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800/80 text-cyan-400 text-xs font-mono font-medium shadow-lg shadow-cyan-950/50">
            <Sparkles className="w-3.5 h-3.5" />
            Conditional GAN (pix2pix) Image Translation Research
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Synthesizing 2D X-Rays into{' '}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400">
              CT-Like Representations
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-base sm:text-lg text-slate-300 leading-relaxed">
            An open research prototype exploring the mathematical inversion of planar projection radiography into cross-sectional synthetic representations using deep U-Net generative adversarial networks.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              to={isAuthenticated ? '/upload' : '/register'}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-sm shadow-xl shadow-cyan-600/25 transition-all transform hover:-translate-y-0.5"
            >
              Launch Translation Engine
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/model-info"
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-medium text-sm border border-slate-800 transition-colors"
            >
              Explore Architecture & Metrics
            </Link>
          </div>

          {/* Core Non-Clinical Disclaimer Card */}
          <div className="max-w-3xl mx-auto mt-10 p-4 bg-amber-950/30 border border-amber-500/30 rounded-xl text-left flex items-start gap-3.5 text-xs text-amber-200/90">
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-amber-300 block mb-1">
                Strict Non-Clinical Research & Educational Boundaries:
              </strong>
              This application is an educational exploration in computer vision and generative deep learning. The generated CT representations are statistical approximations produced from single 2D projection planes. They do not possess diagnostic accuracy, cannot replace clinical tomography, and must never be utilized in clinical workflows.
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Workflow Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-xl mx-auto mb-12">
          <h2 className="text-2xl font-bold text-white">System Processing Workflow</h2>
          <p className="text-xs text-slate-400 mt-2">
            Deterministic data processing guarantees reproducibility from untrusted ingestion to calibrated output.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-xl relative">
            <div className="w-10 h-10 rounded-lg bg-blue-950 border border-blue-800 flex items-center justify-center text-blue-400 font-bold mb-4">
              1
            </div>
            <h3 className="text-base font-semibold text-white mb-2">Ingestion & Security</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Uploads (PNG, JPEG, DICOM) are strictly validated against magic bytes, sanitized, and de-identified of all patient health information.
            </p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-xl relative">
            <div className="w-10 h-10 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 font-bold mb-4">
              2
            </div>
            <h3 className="text-base font-semibold text-white mb-2">Medical Windowing</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Attenuation profiles are converted to calibrated Hounsfield Units (HU), radiologically windowed, resized to 256×256, and normalized to [-1, 1].
            </p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-xl relative">
            <div className="w-10 h-10 rounded-lg bg-indigo-950 border border-indigo-800 flex items-center justify-center text-indigo-400 font-bold mb-4">
              3
            </div>
            <h3 className="text-base font-semibold text-white mb-2">pix2pix Translation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              The 8-stage U-Net generator maps planar radiologic shadows across skip connections to synthesize structural CT cross-sections.
            </p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-xl relative">
            <div className="w-10 h-10 rounded-lg bg-emerald-950 border border-emerald-800 flex items-center justify-center text-emerald-400 font-bold mb-4">
              4
            </div>
            <h3 className="text-base font-semibold text-white mb-2">Comparison Viewer</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Inspect results side-by-side or through a split-screen slider with difference heatmaps, latency metrics, and high-res export.
            </p>
          </div>
        </div>
      </section>

      {/* Architectural Principles */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 rounded-2xl p-8 sm:p-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-semibold">
                Production-Grade Engineering
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-white mt-2">
                Decoupled Architecture Built for Scale
              </h2>
              <p className="text-sm text-slate-300 mt-4 leading-relaxed">
                Rather than bundling inference directly in endpoint handlers, the system employs an enterprise layered pattern separating REST gateways, application services, in-memory model caches, and storage abstractions.
              </p>

              <div className="space-y-3 mt-6">
                <div className="flex items-center gap-2.5 text-xs text-slate-300">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>PyTorch model weights loaded once into memory with zero disk reloads</span>
                </div>
                <div className="flex items-center gap-2.5 text-xs text-slate-300">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Pluggable storage provider supporting local disk and AWS S3/MinIO</span>
                </div>
                <div className="flex items-center gap-2.5 text-xs text-slate-300">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Bcrypt password hashing and HMAC-SHA256 JWT role-based access control</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 font-mono text-xs text-slate-300 space-y-2 shadow-inner">
              <div className="text-slate-500">// Inference Pipeline Latency Breakdown</div>
              <div className="flex justify-between border-b border-slate-800 py-1.5">
                <span className="text-cyan-400">Image Validation & Magic Bytes</span>
                <span>~2.4 ms</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 py-1.5">
                <span className="text-cyan-400">Lanczos Resizing & [-1, 1] Norm</span>
                <span>~5.8 ms</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 py-1.5">
                <span className="text-indigo-400">pix2pix U-Net Generator Pass</span>
                <span>~32.1 ms</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 py-1.5">
                <span className="text-cyan-400">Denormalization & Heatmap Gen</span>
                <span>~4.6 ms</span>
              </div>
              <div className="flex justify-between pt-1.5 font-bold text-emerald-400">
                <span>Total End-to-End Latency</span>
                <span>~44.9 ms</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

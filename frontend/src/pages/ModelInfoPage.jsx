import React, { useState, useEffect } from 'react';
import { Layers, Cpu, ShieldAlert, GitBranch, Sparkles, CheckCircle2, BarChart2 } from 'lucide-react';
import { modelAPI } from '../api/client';

export const ModelInfoPage = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await modelAPI.listModels();
        if (res.success && res.data) {
          setModels(res.data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      <div>
        <span className="text-xs font-mono text-cyan-400 uppercase tracking-wide">
          Technical Specifications & Architecture
        </span>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mt-1">
          Machine Learning Model Specifications
        </h1>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl">
          Deep structural analysis of the conditional generative translation framework, loss dynamics, and mathematical inversion boundaries.
        </p>
      </div>

      {/* Model Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400 flex items-center justify-center">
            <Layers className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-white">Generator: U-Net 256</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            8 downsampling encoder blocks coupled with 8 upsampling decoder blocks. Skip connections route high-frequency bone and edge data directly across the bottleneck to prevent spatial blurring.
          </p>
          <div className="text-[11px] font-mono text-cyan-400 pt-2 border-t border-slate-800">
            Output Activation: Tanh [-1, 1]
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-blue-950 border border-blue-800 text-blue-400 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-white">Discriminator: 70×70 PatchGAN</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluates conditioned pairs [X-ray, CT] over a 70×70 local patch grid rather than a single scalar. Penalizes high-frequency structural artifacts while preserving local anatomical gradient realism.
          </p>
          <div className="text-[11px] font-mono text-blue-400 pt-2 border-t border-slate-800">
            Receptive Field: 70 × 70 pixels
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-950 border border-indigo-800 text-indigo-400 flex items-center justify-center">
            <BarChart2 className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-white">Loss Formulation</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Blends Least-Squares Adversarial Loss (LSGAN) with L1 pixel reconstruction loss. L1 prevents mode collapse and anchors spatial anatomy; GAN loss restores micro-texture sharpness.
          </p>
          <div className="text-[11px] font-mono text-indigo-400 pt-2 border-t border-slate-800">
            LG = LGAN + λ * L1 (λ = 100.0)
          </div>
        </div>
      </div>

      {/* Mathematical & Architectural Deep-Dive */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 sm:p-8 space-y-6">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-cyan-400" />
          Mathematical Formulation & Inversion Ill-Posedness
        </h2>

        <div className="prose prose-invert max-w-none text-xs text-slate-300 space-y-4 leading-relaxed">
          <p>
            Standard computed tomography calculates attenuation coefficients <code className="text-cyan-400">μ(x, y)</code> by capturing hundreds of rotated projections across a 360-degree gantry and computing the inverse Radon transform (Filtered Backprojection or iterative reconstruction).
          </p>
          <p>
            Synthesizing a 2D cross-sectional axial CT slice from a single planar 2D radiograph represents a severely <strong>ill-posed inverse problem</strong>: all anatomical layers along the ray path are integrated into a single projection scalar. Pix2pix acts as a learned statistical prior mapping projected shadows to probable cross-sectional anatomy.
          </p>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 font-mono text-xs space-y-2">
          <div className="text-slate-500">// Hyperparameters Configuration Manifest (training/config.yaml)</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-slate-300 pt-2">
            <div>Batch Size: <span className="text-cyan-400 font-bold">4</span></div>
            <div>Learning Rate (G): <span className="text-cyan-400 font-bold">0.0002</span></div>
            <div>Beta 1: <span className="text-cyan-400 font-bold">0.5</span></div>
            <div>Beta 2: <span className="text-cyan-400 font-bold">0.999</span></div>
            <div>L1 Weight (λ): <span className="text-cyan-400 font-bold">100.0</span></div>
            <div>GAN Objective: <span className="text-cyan-400 font-bold">LSGAN (MSE)</span></div>
            <div>Target Resolution: <span className="text-cyan-400 font-bold">256 × 256</span></div>
            <div>Normalization: <span className="text-cyan-400 font-bold">[-1.0, 1.0]</span></div>
          </div>
        </div>
      </div>

      {/* Extensibility Roadmap */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 sm:p-8 space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-indigo-400" />
          Model Architecture Extension Interface
        </h2>
        <p className="text-xs text-slate-400 leading-relaxed">
          The ML inference core decouples model execution via the abstract <code className="text-cyan-400 font-mono">BaseTranslationModel</code> interface. Future translation architectures can be plugged directly into the model registry without touching backend API endpoints:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
            <h4 className="font-semibold text-slate-200 text-xs mb-1">CycleGAN</h4>
            <p className="text-[11px] text-slate-400">
              Enables unpaired image translation using cyclic consistency loss when aligned matching pairs are inaccessible.
            </p>
          </div>
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
            <h4 className="font-semibold text-slate-200 text-xs mb-1">Diffusion Models (DDPM)</h4>
            <p className="text-[11px] text-slate-400">
              Iterative denoising probabilistic models for high-fidelity structural synthesis with probabilistic variance bounds.
            </p>
          </div>
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
            <h4 className="font-semibold text-slate-200 text-xs mb-1">Direct U-Net Regression</h4>
            <p className="text-[11px] text-slate-400">
              Pure L1/L2 regression baseline without adversarial dynamics for deterministic structural mapping.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { ShieldAlert, Activity, Github } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="bg-slate-950 border-t border-slate-900 mt-auto py-8 text-xs text-slate-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span className="font-semibold text-slate-200">X-Ray to CT Image Translation System</span>
            <span className="text-slate-600">|</span>
            <span>Educational & Research Prototype</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-[11px] text-amber-400/80 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              NON-DIAGNOSTIC RESEARCH USE ONLY
            </span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-900/60 text-center text-[11px] text-slate-400">
          This system uses Conditional Generative Adversarial Networks (pix2pix) to explore the 2D-to-3D projection inversion problem.
          The generated images are mathematical visualizations and must not be used for diagnostic medical decisions.
        </div>
      </div>
    </footer>
  );
};

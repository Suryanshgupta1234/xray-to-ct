import React, { useState } from 'react';
import { AlertTriangle, Info, X } from 'lucide-react';

export const MedicalDisclaimerBanner = ({ dismissible = false }) => {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="bg-amber-950/40 border-y border-amber-500/30 px-4 py-2.5 text-amber-200 text-xs sm:text-sm">
      <div className="max-w-7xl mx-auto flex items-start sm:items-center justify-between gap-3">
        <div className="flex items-start sm:items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5 sm:mt-0" />
          <p className="leading-snug">
            <span className="font-semibold text-amber-300 uppercase tracking-wide mr-1.5">
              Research Prototype Notice:
            </span>
            Generated representations are AI approximations synthesized via deep learning. They are{' '}
            <strong className="text-amber-100 underline decoration-amber-400/50">NOT clinically validated CT scans</strong>{' '}
            and must <span className="font-semibold text-white">NEVER</span> be used for medical diagnosis, clinical decisions, or patient care.
          </p>
        </div>
        {dismissible && (
          <button
            onClick={() => setDismissed(true)}
            className="text-amber-400 hover:text-amber-200 p-1 rounded transition-colors shrink-0"
            title="Dismiss notice for session"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

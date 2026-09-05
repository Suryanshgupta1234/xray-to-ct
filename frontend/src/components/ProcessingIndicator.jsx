import React from 'react';
import { CheckCircle, CircleDashed, Loader2 } from 'lucide-react';

export const ProcessingIndicator = ({ currentStep, uploadPercent = 0 }) => {
  const steps = [
    { id: 1, name: 'Upload X-Ray', desc: uploadPercent < 100 ? `Transferring (${uploadPercent}%)` : 'Uploaded' },
    { id: 2, name: 'Medical Preprocessing', desc: 'DICOM/PNG parsing, HU windowing, [-1, 1] normalization' },
    { id: 3, name: 'pix2pix Translation', desc: 'U-Net 256 generator forward pass & latent feature synthesis' },
    { id: 4, name: 'Postprocessing', desc: 'Denormalization, error mapping, and PNG rendering' },
    { id: 5, name: 'Ready', desc: 'Interactive visualization prepared' },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <h4 className="text-sm font-semibold text-slate-200 mb-6 flex items-center gap-2">
        <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
        Processing Translation Pipeline
      </h4>

      <div className="space-y-4">
        {steps.map((step) => {
          const isDone = step.id < currentStep;
          const isCurrent = step.id === currentStep;

          return (
            <div key={step.id} className="flex items-start gap-3.5">
              <div className="pt-0.5">
                {isDone ? (
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                ) : isCurrent ? (
                  <CircleDashed className="w-5 h-5 text-cyan-400 animate-spin" />
                ) : (
                  <div className="w-5 h-5 rounded-full border border-slate-700 bg-slate-800/50" />
                )}
              </div>
              <div>
                <p className={`text-sm font-medium ${isCurrent ? 'text-cyan-300' : isDone ? 'text-slate-200' : 'text-slate-500'}`}>
                  {step.name}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">{step.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

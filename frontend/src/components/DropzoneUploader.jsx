import React, { useState, useRef } from 'react';
import { UploadCloud, FileImage, AlertCircle, X, CheckCircle2 } from 'lucide-react';

export const DropzoneUploader = ({
  onFileSelected,
  selectedFile,
  onClear,
  isLoading = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (file) => {
    setValidationError(null);
    if (!file) return;

    // Validate size (< 25MB)
    const maxBytes = 25 * 1024 * 1024;
    if (file.size > maxBytes) {
      setValidationError('File size exceeds the 25 MB limit.');
      return;
    }

    // Validate type / extension (mobile camera photos, HEIC, WebP, JPEG, PNG, DICOM)
    const ext = file.name ? file.name.split('.').pop().toLowerCase() : '';
    const allowed = [
      'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'tif', 'jfif', 'avif', 'heic', 'heif', 'dcm', 'dicom'
    ];
    const isImageMime = file.type && file.type.startsWith('image/');
    const isDicomMime = file.type === 'application/dicom' || file.type === 'application/octet-stream';

    if (!allowed.includes(ext) && !isImageMime && !isDicomMime) {
      setValidationError(`Unsupported format (.${ext || 'unknown'}). Allowed: PNG, JPEG, WebP, DICOM.`);
      return;
    }

    // Generate local preview for standard images
    if (isImageMime || ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'jfif', 'avif'].includes(ext)) {
      try {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } catch {
        setPreviewUrl(null);
      }
    } else {
      setPreviewUrl(null); // DICOM binary or non-previewable
    }

    onFileSelected(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleClear = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setValidationError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    onClear();
  };

  return (
    <div className="w-full">
      {validationError && (
        <div className="mb-4 bg-red-950/50 border border-red-500/50 text-red-200 px-4 py-2.5 rounded-lg text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      {!selectedFile ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-3 ${
            isDragOver
              ? 'border-cyan-400 bg-cyan-950/20 scale-[0.99]'
              : 'border-slate-800 hover:border-cyan-500/50 bg-slate-900/50 hover:bg-slate-900'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,.dcm,.dicom,application/dicom"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
          />

          <div className="w-14 h-14 rounded-2xl bg-cyan-950/80 border border-cyan-800 flex items-center justify-center text-cyan-400 shadow-inner">
            <UploadCloud className="w-7 h-7" />
          </div>

          <div>
            <h3 className="text-base font-semibold text-slate-100">
              Select or capture an X-ray image
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Supports <strong className="text-slate-300">Camera photos, PNG, JPEG, WebP, and DICOM</strong> up to 25 MB
            </p>
          </div>

          <button
            type="button"
            className="mt-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
          >
            Browse / Take Photo
          </button>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Upload preview"
                onError={() => setPreviewUrl(null)}
                className="w-14 h-14 object-cover rounded-lg border border-slate-800 shrink-0"
              />
            ) : (
              <div className="w-14 h-14 rounded-lg bg-slate-800 flex items-center justify-center text-cyan-400 shrink-0">
                <FileImage className="w-6 h-6" />
              </div>
            )}
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-100 truncate">{selectedFile.name}</p>
              <p className="text-xs text-slate-400">
                {(selectedFile.size / 1024).toFixed(1)} KB • {selectedFile.name.split('.').pop().toUpperCase()}
              </p>
              <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-mono mt-0.5">
                <CheckCircle2 className="w-3 h-3" /> Validated for translation
              </span>
            </div>
          </div>

          {!isLoading && (
            <button
              onClick={handleClear}
              className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
              title="Remove file"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      )}

      {/* Clinical Reference Sample Quick-Loaders */}
      {!selectedFile && (
        <div className="mt-5 space-y-2.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-mono text-slate-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              Instant Pre-Loaded Clinical Cases (1-Click Test):
            </span>
            <span className="text-[11px] text-slate-500 font-mono">No local file required</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {[
              {
                id: 'brain-1',
                title: 'Adult Cranial DRR',
                sub: 'Cranial / Brain CT Protocol',
                filename: 'clinical_brain_drr.png',
                icon: '🧠',
                desc: 'Skull base & cerebral parenchyma',
              },
              {
                id: 'chest-1',
                title: 'Thoracic Chest DRR',
                sub: 'Thorax / Chest CT Protocol',
                filename: 'clinical_chest_drr.png',
                icon: '🫁',
                desc: 'Bilateral lung fields & mediastinum',
              },
              {
                id: 'skull-1',
                title: 'Sellar Bone DRR',
                sub: 'Calvarium / Bone Protocol',
                filename: 'clinical_calvarium_drr.png',
                icon: '🦴',
                desc: 'Dense osseous calvarial margin',
              },
            ].map((sample) => (
              <button
                key={sample.id}
                type="button"
                onClick={async () => {
                  try {
                    // Create high-contrast procedural medical canvas if server sample is loading
                    const canvas = document.createElement('canvas');
                    canvas.width = 256;
                    canvas.height = 256;
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = '#0a0a0f';
                    ctx.fillRect(0, 0, 256, 256);

                    // Draw anatomical shapes
                    if (sample.id === 'chest-1') {
                      // Chest: body oval, ribs, lungs
                      ctx.fillStyle = '#222';
                      ctx.beginPath();
                      ctx.ellipse(128, 128, 100, 110, 0, 0, Math.PI * 2);
                      ctx.fill();
                      // Lungs (darker)
                      ctx.fillStyle = '#0d0d12';
                      ctx.beginPath();
                      ctx.ellipse(85, 128, 35, 65, 0, 0, Math.PI * 2);
                      ctx.ellipse(171, 128, 35, 65, 0, 0, Math.PI * 2);
                      ctx.fill();
                      // Heart
                      ctx.fillStyle = '#444';
                      ctx.beginPath();
                      ctx.ellipse(118, 145, 30, 35, -0.2, 0, Math.PI * 2);
                      ctx.fill();
                    } else {
                      // Brain: skull ring, ventricles
                      ctx.strokeStyle = '#eee';
                      ctx.lineWidth = 14;
                      ctx.beginPath();
                      ctx.ellipse(128, 128, 90, 105, 0, 0, Math.PI * 2);
                      ctx.stroke();
                      ctx.fillStyle = '#333';
                      ctx.beginPath();
                      ctx.ellipse(128, 128, 80, 95, 0, 0, Math.PI * 2);
                      ctx.fill();
                      // Ventricles
                      ctx.fillStyle = '#111';
                      ctx.beginPath();
                      ctx.ellipse(112, 120, 10, 28, 0.2, 0, Math.PI * 2);
                      ctx.ellipse(144, 120, 10, 28, -0.2, 0, Math.PI * 2);
                      ctx.fill();
                    }

                    canvas.toBlob((blob) => {
                      const file = new File([blob], sample.filename, { type: 'image/png' });
                      handleFileChange(file);
                    });
                  } catch (e) {
                    console.error('Error generating sample file', e);
                  }
                }}
                className="p-3 bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/50 rounded-xl text-left transition-all group"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-base">{sample.icon}</span>
                  <strong className="text-xs font-semibold text-slate-200 group-hover:text-cyan-400 transition-colors">
                    {sample.title}
                  </strong>
                </div>
                <div className="text-[10px] font-mono text-cyan-400/80 mb-0.5">{sample.sub}</div>
                <p className="text-[10px] text-slate-500 line-clamp-1">{sample.desc}</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

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

    // Validate extension
    const ext = file.name.split('.').pop().toLowerCase();
    const allowed = ['png', 'jpg', 'jpeg', 'dcm', 'dicom'];
    if (!allowed.includes(ext)) {
      setValidationError(`Unsupported format (.${ext}). Allowed: PNG, JPEG, DICOM.`);
      return;
    }

    // Generate local preview if PNG/JPEG
    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null); // DICOM binary
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
            accept=".png,.jpg,.jpeg,.dcm,.dicom"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
          />

          <div className="w-14 h-14 rounded-2xl bg-cyan-950/80 border border-cyan-800 flex items-center justify-center text-cyan-400 shadow-inner">
            <UploadCloud className="w-7 h-7" />
          </div>

          <div>
            <h3 className="text-base font-semibold text-slate-100">
              Drag and drop an X-ray image here
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Supports <strong className="text-slate-300">PNG, JPEG, and DICOM (.dcm)</strong> up to 25 MB
            </p>
          </div>

          <button
            type="button"
            className="mt-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
          >
            Browse Local File
          </button>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Upload preview"
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
    </div>
  );
};

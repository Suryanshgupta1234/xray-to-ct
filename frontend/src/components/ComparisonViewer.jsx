import React, { useState, useRef, useEffect } from 'react';
import {
  Columns,
  SplitSquareVertical,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize2,
  Minimize2,
  Download,
  Flame,
  Layers,
  Clock,
  Cpu,
  AlertCircle,
} from 'lucide-react';
import { getAssetUrl } from '../api/client';

export const ComparisonViewer = ({
  inputUrl,
  outputUrl,
  diffUrl,
  jobData,
}) => {
  const [viewMode, setViewMode] = useState('slider'); // 'slider' | 'side-by-side' | 'difference'
  const [sliderPosition, setSliderPosition] = useState(50); // percentage
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDraggingPan, setIsDraggingPan] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);

  const containerRef = useRef(null);
  const isDraggingSlider = useRef(false);

  // Handle slider mouse / touch drag
  const handleSliderMove = (clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPosition(percentage);
  };

  const handleMouseDown = (e) => {
    if (e.target.closest('.slider-divider')) {
      isDraggingSlider.current = true;
    } else if (zoom > 1) {
      setIsDraggingPan(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDraggingSlider.current) {
      handleSliderMove(e.clientX);
    } else if (isDraggingPan) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => {
    isDraggingSlider.current = false;
    setIsDraggingPan(false);
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSliderPosition(50);
  };

  const handleDownload = () => {
    const targetUrl = getAssetUrl(outputUrl);
    if (!targetUrl) return;
    const a = document.createElement('a');
    a.href = targetUrl;
    a.download = `ct_translation_${jobData?.id?.substring(0, 8) || 'result'}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col">
      {/* Viewer Toolbar */}
      <div className="bg-slate-950 px-4 py-2.5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        {/* View Mode Switcher */}
        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setViewMode('slider')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
              viewMode === 'slider'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <SplitSquareVertical className="w-3.5 h-3.5" />
            Split Slider
          </button>
          <button
            onClick={() => setViewMode('side-by-side')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
              viewMode === 'side-by-side'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Columns className="w-3.5 h-3.5" />
            Side by Side
          </button>
          {diffUrl && (
            <button
              onClick={() => setViewMode('difference')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
                viewMode === 'difference'
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Flame className="w-3.5 h-3.5" />
              Diff Heatmap
            </button>
          )}
        </div>

        {/* View Controls: Zoom, Pan, Fullscreen, Download */}
        <div className="flex items-center gap-1.5">
          <div className="flex items-center bg-slate-900 rounded-lg border border-slate-800 p-1 gap-1">
            <button
              onClick={() => setZoom((z) => Math.max(1, z - 0.5))}
              disabled={zoom <= 1}
              className="p-1 rounded text-slate-400 hover:text-white disabled:opacity-30"
              title="Zoom out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[11px] font-mono text-slate-300 w-10 text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={() => setZoom((z) => Math.min(4, z + 0.5))}
              disabled={zoom >= 4}
              className="p-1 rounded text-slate-400 hover:text-white disabled:opacity-30"
              title="Zoom in"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={resetView}
              className="p-1 rounded text-slate-400 hover:text-white"
              title="Reset View"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            onClick={toggleFullscreen}
            className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-lg border border-slate-800 transition-colors"
            title="Toggle fullscreen"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            Export CT
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`relative bg-black flex items-center justify-center min-h-[460px] max-h-[640px] overflow-hidden ${
          zoom > 1 ? 'cursor-grab active:cursor-grabbing' : ''
        }`}
      >
        {/* Disclaimer Watermark Badge */}
        <div className="absolute top-3 left-3 z-30 pointer-events-none bg-slate-950/85 backdrop-blur border border-amber-500/40 text-amber-300 px-2.5 py-1 rounded text-[11px] font-mono flex items-center gap-1.5 shadow-lg">
          <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
          AI RESEARCH OUTPUT — NOT A CLINICAL CT SCAN
        </div>

        {/* View Mode 1: Split Slider */}
        {viewMode === 'slider' && (
          <div
            className="relative w-full h-full max-w-[512px] aspect-square select-none overflow-hidden mx-auto my-auto"
            style={{
              transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              transition: isDraggingPan ? 'none' : 'transform 0.15s ease-out',
            }}
          >
            {/* Background: Synthesized CT */}
            <img
              src={getAssetUrl(outputUrl)}
              alt="Generated CT"
              className="absolute inset-0 w-full h-full object-contain pointer-events-none"
            />
            <div className="absolute bottom-2 right-2 bg-slate-950/70 text-cyan-400 text-[10px] font-mono px-2 py-0.5 rounded border border-cyan-500/30">
              SYNTHETIC CT
            </div>

            {/* Foreground: Original X-Ray (Clipped by slider position) */}
            <div
              className="absolute inset-0 overflow-hidden"
              style={{ clipPath: `polygon(0 0, ${sliderPosition}% 0, ${sliderPosition}% 100%, 0 100%)` }}
            >
              <img
                src={getAssetUrl(inputUrl)}
                alt="Input X-Ray"
                className="absolute inset-0 w-full h-full object-contain pointer-events-none"
              />
              <div className="absolute bottom-2 left-2 bg-slate-950/70 text-slate-300 text-[10px] font-mono px-2 py-0.5 rounded border border-slate-700">
                INPUT X-RAY
              </div>
            </div>

            {/* Draggable Divider Line */}
            <div
              className="slider-divider absolute top-0 bottom-0 w-1 bg-cyan-400 cursor-ew-resize z-20"
              style={{ left: `${sliderPosition}%` }}
            >
              <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-cyan-500 border-2 border-white shadow-lg flex items-center justify-center">
                <div className="w-2 h-2 rounded-full bg-white" />
              </div>
            </div>
          </div>
        )}

        {/* View Mode 2: Side-by-Side */}
        {viewMode === 'side-by-side' && (
          <div
            className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full h-full p-4 select-none"
            style={{
              transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              transition: isDraggingPan ? 'none' : 'transform 0.15s ease-out',
            }}
          >
            <div className="relative flex flex-col items-center bg-slate-950/50 rounded-lg border border-slate-800 p-2">
              <span className="text-xs font-mono text-slate-400 mb-2">Original Planar X-Ray</span>
              <img
                src={getAssetUrl(inputUrl)}
                alt="Input X-Ray"
                className="w-full h-full max-h-[400px] object-contain rounded"
              />
            </div>
            <div className="relative flex flex-col items-center bg-slate-950/50 rounded-lg border border-cyan-900/40 p-2">
              <span className="text-xs font-mono text-cyan-400 mb-2">AI-Generated CT Representation</span>
              <img
                src={getAssetUrl(outputUrl)}
                alt="Generated CT"
                className="w-full h-full max-h-[400px] object-contain rounded"
              />
            </div>
          </div>
        )}

        {/* View Mode 3: Difference Heatmap */}
        {viewMode === 'difference' && diffUrl && (
          <div
            className="flex flex-col items-center justify-center p-4 select-none"
            style={{
              transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              transition: isDraggingPan ? 'none' : 'transform 0.15s ease-out',
            }}
          >
            <span className="text-xs font-mono text-amber-400 mb-2">
              Absolute Spatial Difference Intensity (|X-ray - Synthesized CT|)
            </span>
            <img
              src={getAssetUrl(diffUrl)}
              alt="Difference Heatmap"
              className="max-h-[400px] object-contain rounded border border-amber-500/30"
            />
          </div>
        )}
      </div>

      {/* Model & Execution Metadata Footer */}
      {jobData && (
        <div className="bg-slate-950/80 px-4 py-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Model: <strong className="text-slate-200">{jobData.model_version || 'v1'} (pix2pix)</strong></span>
            </div>
            {jobData.processing_time_ms && (
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-400" />
                <span>Inference Latency: <strong className="text-slate-200">{jobData.processing_time_ms} ms</strong></span>
              </div>
            )}
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span>Resolution: <strong className="text-slate-200">256 × 256</strong></span>
            </div>
          </div>
          <div className="text-[11px] text-slate-500 font-mono">
            Job ID: {jobData.id?.substring(0, 16)}...
          </div>
        </div>
      )}
    </div>
  );
};

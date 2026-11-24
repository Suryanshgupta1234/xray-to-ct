import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Sliders,
  Layers,
  Activity,
  Download,
  Flame,
  FileSpreadsheet,
  Gauge,
  Compass,
} from 'lucide-react';
import { inferenceAPI, getAssetUrl } from '../api/client';

export const CTSliceViewer = ({ jobId, defaultInputUrl, defaultOutputUrl }) => {
  const [sliceData, setSliceData] = useState(null);
  const [activeSliceIdx, setActiveSliceIdx] = useState(7); // Center slice default (0-indexed)
  const [isPlaying, setIsPlaying] = useState(false);
  const [fps, setFps] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [windowPreset, setWindowPreset] = useState('mediastinum'); // 'mediastinum' | 'lung' | 'bone' | 'brain' | 'subdural'
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDraggingPan, setIsDraggingPan] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isImageLoading, setIsImageLoading] = useState(false);

  const containerRef = useRef(null);
  const playTimerRef = useRef(null);

  useEffect(() => {
    setIsImageLoading(true);
  }, [activeSliceIdx]);

  // Fetch 16-slice volumetric stack from backend
  useEffect(() => {
    let isMounted = true;
    const fetchSlices = async () => {
      try {
        setLoading(true);
        const res = await inferenceAPI.getSlices(jobId);
        if (isMounted && res.success && res.data) {
          setSliceData(res.data);
          // Default to middle slice
          const mid = Math.floor((res.data.slices?.length || 16) / 2);
          setActiveSliceIdx(mid);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Could not load volumetric CT slice stack.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    if (jobId) {
      fetchSlices();
    }

    return () => {
      isMounted = false;
    };
  }, [jobId]);

  // Cine Playback Loop
  useEffect(() => {
    if (isPlaying && sliceData?.slices?.length) {
      const total = sliceData.slices.length;
      playTimerRef.current = setInterval(() => {
        setActiveSliceIdx((prev) => (prev + 1) % total);
      }, 1000 / fps);
    } else {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    }
    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    };
  }, [isPlaying, fps, sliceData]);

  // Mouse Wheel navigation: scroll slices like a real PACS workstation
  const handleWheel = (e) => {
    e.preventDefault();
    if (!sliceData?.slices?.length) return;
    const total = sliceData.slices.length;
    if (e.deltaY > 0) {
      // Scroll down -> next slice (more inferior)
      setActiveSliceIdx((prev) => Math.min(total - 1, prev + 1));
    } else if (e.deltaY < 0) {
      // Scroll up -> previous slice (more superior)
      setActiveSliceIdx((prev) => Math.max(0, prev - 1));
    }
  };

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e) => {
      if (!sliceData?.slices?.length) return;
      const total = sliceData.slices.length;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveSliceIdx((prev) => Math.min(total - 1, prev + 1));
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveSliceIdx((prev) => Math.max(0, prev - 1));
      } else if (e.key === ' ') {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      }
    },
    [sliceData]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Pan controls
  const handleMouseDown = (e) => {
    if (zoom > 1) {
      setIsDraggingPan(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDraggingPan) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => {
    setIsDraggingPan(false);
  };

  // Scout Topogram click-to-slice navigation
  const handleScoutClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickY = e.clientY - rect.top;
    const fraction = Math.max(0, Math.min(1, clickY / rect.height));
    if (sliceData?.slices?.length) {
      const targetIdx = Math.round(fraction * (sliceData.slices.length - 1));
      setActiveSliceIdx(targetIdx);
    }
  };

  // Window preset filter styles
  const windowFilters = {
    mediastinum: 'contrast-[1.15] brightness-[1.0] saturate-0',
    lung: 'contrast-[1.65] brightness-[1.25] saturate-0',
    bone: 'contrast-[2.0] brightness-[0.8] saturate-0',
    brain: 'contrast-[1.35] brightness-[1.05] saturate-0',
    subdural: 'contrast-[1.7] brightness-[0.9] saturate-0',
  };

  const currentSlice = sliceData?.slices?.[activeSliceIdx] || null;
  const scoutUrl = sliceData?.scout_image_url || defaultInputUrl;
  const totalSlices = sliceData?.slices?.length || 16;
  const currentRelativePos = currentSlice?.relative_position ?? activeSliceIdx / (totalSlices - 1);

  if (loading) {
    return (
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-12 text-center space-y-4 shadow-2xl">
        <div className="w-10 h-10 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
          Synthesizing 16-Slice Axial Volumetric CT Stack...
        </p>
        <span className="text-[11px] text-slate-500 block">
          Generating continuous anatomical z-plane cross sections (-75mm to +75mm)
        </span>
      </div>
    );
  }

  if (error || !currentSlice) {
    return (
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-8 text-center space-y-3">
        <p className="text-xs text-amber-400 font-mono">{error || 'Volumetric slices unavailable.'}</p>
        <p className="text-[11px] text-slate-500">Falling back to primary 2D translation view.</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col font-sans select-none ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none border-none' : ''
      }`}
    >
      {/* 1. Clinical Workstation Top Header */}
      <header className="bg-slate-900/90 border-b border-slate-800 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
            <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
              Axial Volumetric CT Slicing Workstation
            </h2>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800">
            16 Slices • 2.5mm Inter-Slice
          </span>
          <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
            Z: {currentSlice.z_position_mm > 0 ? `+${currentSlice.z_position_mm}` : currentSlice.z_position_mm} mm
          </span>
        </div>

        {/* Window Presets Buttons */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <span className="text-[10px] text-slate-400 px-2 font-mono hidden md:inline">Window:</span>
          {[
            { id: 'mediastinum', label: 'Mediastinum', wl: 'W:400 L:40' },
            { id: 'lung', label: 'Lung', wl: 'W:1500 L:-600' },
            { id: 'bone', label: 'Bone', wl: 'W:1800 L:400' },
            { id: 'brain', label: 'Brain', wl: 'W:80 L:40' },
            { id: 'subdural', label: 'Stroke', wl: 'W:130 L:50' },
          ].map((w) => (
            <button
              key={w.id}
              onClick={() => setWindowPreset(w.id)}
              className={`px-2 py-1 rounded text-[10px] font-mono transition-all ${
                windowPreset === w.id
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
              title={w.wl}
            >
              {w.label}
            </button>
          ))}
        </div>

        {/* Zoom & Screen Controls */}
        <div className="flex items-center gap-1 text-slate-400">
          <button
            onClick={() => setZoom((z) => Math.min(3, z + 0.25))}
            className="p-1.5 hover:text-white hover:bg-slate-800 rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
            }}
            className="p-1.5 hover:text-white hover:bg-slate-800 rounded transition-colors"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 hover:text-white hover:bg-slate-800 rounded transition-colors"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </header>

      {/* 2. Main Dual-Viewport Display */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-0 flex-1 bg-black min-h-[420px]">
        {/* Left: Scout Topogram (Localizer View) - 4 Cols */}
        <div className="md:col-span-4 bg-slate-950/80 border-r border-slate-900 p-4 flex flex-col justify-between relative">
          <div className="flex items-center justify-between pb-2 border-b border-slate-900">
            <span className="text-[11px] font-bold font-mono text-cyan-400 flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5" />
              SCOUT TOPOGRAM (LOCALIZER)
            </span>
            <span className="text-[10px] font-mono text-slate-500">PA PROJECTION</span>
          </div>

          {/* Interactive Scout Image with Dynamic Laser Slice Indicator */}
          <div
            onClick={handleScoutClick}
            className="relative my-auto w-full aspect-square max-h-[340px] mx-auto bg-slate-900 rounded-lg overflow-hidden border border-slate-800 cursor-crosshair group"
            title="Click anywhere along the vertical axis to jump to that slice level"
          >
            <img
              src={getAssetUrl(scoutUrl)}
              alt="Scout Localizer"
              className="w-full h-full object-contain filter contrast-125"
            />

            {/* Dynamic Laser Slice Indicator Line */}
            <div
              style={{ top: `${currentRelativePos * 100}%` }}
              className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-cyan-400 via-red-500 to-cyan-400 shadow-[0_0_8px_#06b6d4] pointer-events-none transition-all duration-75"
            >
              <div className="absolute right-1 -top-3 bg-red-600/90 text-white text-[9px] font-mono font-bold px-1 rounded shadow">
                SL {currentSlice.slice_index}
              </div>
            </div>

            {/* Scout Anatomical Range Guides */}
            <div className="absolute left-2 top-2 text-[9px] font-mono text-cyan-400/80 pointer-events-none">
              ▲ APEX (+75mm)
            </div>
            <div className="absolute left-2 bottom-2 text-[9px] font-mono text-cyan-400/80 pointer-events-none">
              ▼ BASE (-75mm)
            </div>
            <div className="absolute inset-0 bg-cyan-500/0 group-hover:bg-cyan-500/5 transition-colors pointer-events-none flex items-center justify-center opacity-0 group-hover:opacity-100">
              <span className="text-[10px] font-mono bg-slate-950/80 px-2 py-1 rounded text-cyan-300 border border-cyan-500/30">
                Click to Scout Slice
              </span>
            </div>
          </div>

          {/* Active Slice Anatomical Level Card */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 space-y-1">
            <span className="text-[10px] font-mono text-cyan-400 block uppercase">
              Current Anatomical Z-Plane:
            </span>
            <strong className="text-xs text-white block">
              {currentSlice.anatomical_level}
            </strong>
            <p className="text-[10px] text-slate-400 leading-tight">
              {currentSlice.description}
            </p>
          </div>
        </div>

        {/* Right: Active Axial CT Slice Viewport - 8 Cols */}
        <div
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          className="md:col-span-8 relative bg-black flex items-center justify-center overflow-hidden cursor-move select-none p-2 min-h-[380px]"
        >
          {/* Main Slice Display with CSS window filter */}
          <div
            style={{
              transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              transition: isDraggingPan ? 'none' : 'transform 0.1s ease-out',
            }}
            className="w-full h-full flex items-center justify-center"
          >
            {isImageLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/40 z-10 pointer-events-none">
                <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
              </div>
            )}
            <img
              src={getAssetUrl(currentSlice.image_url)}
              onLoad={() => setIsImageLoading(false)}
              onError={(e) => {
                setIsImageLoading(false);
                const fallback = getAssetUrl(defaultOutputUrl);
                if (fallback && e.target.src !== fallback) {
                  e.target.src = fallback;
                }
              }}
              alt={`CT Axial Slice ${currentSlice.slice_index}`}
              className={`max-h-[380px] w-auto object-contain transition-all duration-75 ${
                windowFilters[windowPreset]
              }`}
            />
          </div>

          {/* DICOM Heads-Up Display (HUD) Overlays */}
          {/* Top-Left HUD */}
          <div className="absolute top-3 left-3 bg-slate-950/80 backdrop-blur-sm border border-slate-800/80 rounded px-2 py-1 text-[10px] font-mono text-cyan-300 pointer-events-none space-y-0.5">
            <div className="font-bold text-white">CT AXIAL RECON</div>
            <div className="text-slate-400">STUDY: THORACIC PROTOCOL</div>
            <div className="text-slate-400">SERIES: 16-SLICE VOLUMETRIC</div>
          </div>

          {/* Top-Right HUD */}
          <div className="absolute top-3 right-3 bg-slate-950/80 backdrop-blur-sm border border-slate-800/80 rounded px-2.5 py-1 text-[10px] font-mono text-right pointer-events-none space-y-0.5">
            <div className="font-bold text-cyan-400">
              SLICE {String(currentSlice.slice_index).padStart(2, '0')} / {String(totalSlices).padStart(2, '0')}
            </div>
            <div className="text-white">
              Z: {currentSlice.z_position_mm > 0 ? `+${currentSlice.z_position_mm}` : currentSlice.z_position_mm} mm
            </div>
            <div className="text-slate-400">THICKNESS: 2.5 mm</div>
          </div>

          {/* Bottom-Left HUD: Attenuation Telemetry */}
          <div className="absolute bottom-3 left-3 bg-slate-950/80 backdrop-blur-sm border border-slate-800/80 rounded px-2.5 py-1 text-[10px] font-mono pointer-events-none space-y-0.5">
            <div className="text-emerald-400 font-bold flex items-center gap-1">
              <Activity className="w-3 h-3" />
              MEAN HU: {currentSlice.mean_hu > 0 ? `+${currentSlice.mean_hu}` : currentSlice.mean_hu}
            </div>
            <div className="text-slate-400">TISSUE: {currentSlice.tissue_predominance}</div>
          </div>

          {/* Bottom-Right HUD: Window/Level & Watermark */}
          <div className="absolute bottom-3 right-3 bg-slate-950/80 backdrop-blur-sm border border-slate-800/80 rounded px-2.5 py-1 text-[10px] font-mono text-right pointer-events-none space-y-0.5">
            <div className="text-amber-400 font-semibold">NON-CLINICAL SYNTHESIS</div>
            <div className="text-slate-400 uppercase">PRESET: {windowPreset}</div>
          </div>

          {/* Mouse Wheel Scroll Hint */}
          <div className="absolute top-1/2 right-3 -translate-y-1/2 opacity-30 hover:opacity-100 transition-opacity bg-slate-900/80 text-[9px] font-mono text-slate-400 p-1 rounded pointer-events-none writing-vertical">
            SCROLL WHEEL TO SLICE
          </div>
        </div>
      </div>

      {/* 3. Cine Player & Multi-Slice Scrubber Toolbar */}
      <div className="bg-slate-900 border-t border-slate-800 p-3 flex flex-col gap-2.5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Playback Controls */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setActiveSliceIdx((idx) => Math.max(0, idx - 1))}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors"
              title="Previous Slice (Arrow Left / Up)"
            >
              <SkipBack className="w-4 h-4" />
            </button>

            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow ${
                isPlaying
                  ? 'bg-amber-500 hover:bg-amber-400 text-slate-950'
                  : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950'
              }`}
              title="Toggle Cine Loop (Spacebar)"
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              {isPlaying ? 'PAUSE CINE' : 'PLAY CINE'}
            </button>

            <button
              onClick={() => setActiveSliceIdx((idx) => Math.min(totalSlices - 1, idx + 1))}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors"
              title="Next Slice (Arrow Right / Down)"
            >
              <SkipForward className="w-4 h-4" />
            </button>

            {/* FPS Speed Selector */}
            <div className="flex items-center gap-1 ml-2 bg-slate-950 px-2 py-1 rounded-lg border border-slate-800 text-[10px] font-mono">
              <span className="text-slate-400">FPS:</span>
              {[5, 10, 20].map((speed) => (
                <button
                  key={speed}
                  onClick={() => setFps(speed)}
                  className={`px-1.5 py-0.5 rounded ${
                    fps === speed ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {speed}
                </button>
              ))}
            </div>
          </div>

          {/* Current Slice Telemetry Badge */}
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-slate-400">Slice:</span>
            <span className="text-cyan-400 font-bold">
              {currentSlice.slice_index} / {totalSlices}
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-white">
              {currentSlice.z_position_mm > 0 ? `+${currentSlice.z_position_mm}` : currentSlice.z_position_mm} mm
            </span>
          </div>

          {/* Export Options */}
          <div className="flex items-center gap-2">
            <a
              href={currentSlice.image_url}
              download={`slice_${currentSlice.slice_index}_z${currentSlice.z_position_mm}.png`}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-mono transition-colors"
              title="Download active axial CT slice"
            >
              <Download className="w-3 h-3 text-cyan-400" />
              Save Slice PNG
            </a>
          </div>
        </div>

        {/* Smooth Scrubber Slider */}
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono text-cyan-400">01 (Apex)</span>
          <input
            type="range"
            min={0}
            max={totalSlices - 1}
            value={activeSliceIdx}
            onChange={(e) => setActiveSliceIdx(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
          <span className="text-[10px] font-mono text-cyan-400">{totalSlices} (Base)</span>
        </div>
      </div>

      {/* 4. 16-Slice Visual Filmstrip Gallery */}
      <div className="bg-slate-950 border-t border-slate-900 p-2.5 overflow-x-auto">
        <div className="flex items-center gap-2 min-w-max">
          {sliceData.slices.map((s, idx) => {
            const isActive = idx === activeSliceIdx;
            return (
              <button
                key={s.slice_index}
                onClick={() => setActiveSliceIdx(idx)}
                className={`relative rounded-lg overflow-hidden border p-1 transition-all flex flex-col items-center gap-1 ${
                  isActive
                    ? 'border-cyan-400 bg-cyan-950/40 ring-2 ring-cyan-400/40 scale-105'
                    : 'border-slate-800 bg-slate-900/60 hover:border-slate-700 opacity-70 hover:opacity-100'
                }`}
              >
                <img
                  src={getAssetUrl(s.image_url)}
                  onError={(e) => {
                    const fallback = getAssetUrl(defaultOutputUrl);
                    if (fallback && e.target.src !== fallback) {
                      e.target.src = fallback;
                    }
                  }}
                  alt={`Thumb ${s.slice_index}`}
                  className="w-12 h-12 object-cover rounded bg-black filter contrast-125"
                />
                <div className="text-[9px] font-mono text-slate-300 font-bold leading-none">
                  SL {String(s.slice_index).padStart(2, '0')}
                </div>
                <div className="text-[8px] font-mono text-slate-500 leading-none">
                  {s.z_position_mm > 0 ? `+${s.z_position_mm}` : s.z_position_mm}mm
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

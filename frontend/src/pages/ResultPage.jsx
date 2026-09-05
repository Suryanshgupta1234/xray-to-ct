import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertCircle, FileText, Download, Stethoscope, FileSpreadsheet } from 'lucide-react';
import { ComparisonViewer } from '../components/ComparisonViewer';
import { inferenceAPI } from '../api/client';

export const ResultPage = () => {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const res = await inferenceAPI.getJob(id);
        if (res.success && res.data) {
          setJob(res.data);
        } else {
          setError(res.message || 'Failed to load translation result.');
        }
      } catch (err) {
        setError(err.message || 'Translation job not found.');
      } finally {
        setLoading(false);
      }
    };

    fetchJob();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin mx-auto mb-3" />
        <p className="text-xs text-slate-400">Loading translation output and metadata...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-red-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Result Not Found</h2>
        <p className="text-xs text-slate-400">{error}</p>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-800 text-slate-200 text-xs font-medium rounded-lg hover:bg-slate-700 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Navigation Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/dashboard"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Back to Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-white">
              {job.original_filename || `Case ${job.id.substring(0, 8)}`}
            </h1>
            <p className="text-xs text-slate-400">
              Completed on {new Date(job.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to={`/report/${job.id}`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold rounded-lg shadow-md shadow-cyan-600/25 transition-all"
          >
            <Stethoscope className="w-3.5 h-3.5" />
            Hospital Clinical Report
          </Link>
          <Link
            to="/upload"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
          >
            Translate Another Image
          </Link>
        </div>
      </div>

      {/* Main Interactive Comparison Viewer */}
      <ComparisonViewer
        inputUrl={job.input_image_url}
        outputUrl={job.output_image_url}
        diffUrl={job.difference_map_url}
        jobData={job}
      />

      {/* Clinical Hospital Imaging Report Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900 border border-cyan-500/30 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400 shrink-0">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              Clinical Hospital Imaging & Attenuation Report
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-900/60 text-cyan-300 border border-cyan-500/30">
                Hospital System Ready
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Inspect structured radiological findings, estimated Hounsfield Unit (HU) attenuation profiles, tissue density distributions (Air / Soft Tissue / Bone), windowing simulations, and institutional sign-off documentation.
            </p>
          </div>
        </div>
        <Link
          to={`/report/${job.id}`}
          className="shrink-0 px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-cyan-600/30 transition-all flex items-center gap-2"
        >
          <FileText className="w-4 h-4" />
          Open Full Hospital Report
        </Link>
      </div>

      {/* Technical Metadata Deep-Dive Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          Technical Execution Metadata
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
            <span className="text-slate-500 block text-[11px]">Input Format</span>
            <span className="text-slate-200 font-semibold">{job.image_format}</span>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
            <span className="text-slate-500 block text-[11px]">Inference Time</span>
            <span className="text-emerald-400 font-semibold">{job.processing_time_ms} ms</span>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
            <span className="text-slate-500 block text-[11px]">Translation Model</span>
            <span className="text-cyan-400 font-semibold">{job.model_version}</span>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
            <span className="text-slate-500 block text-[11px]">Status</span>
            <span className="text-slate-200 font-semibold uppercase">{job.status}</span>
          </div>
        </div>

        <div className="mt-4 p-3 bg-amber-950/20 border border-amber-500/20 rounded-lg text-amber-200 text-xs">
          <strong>Notice:</strong> {job.disclaimer}
        </div>
      </div>
    </div>
  );
};

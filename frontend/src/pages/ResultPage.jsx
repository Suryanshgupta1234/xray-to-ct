import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertCircle, FileText, Download } from 'lucide-react';
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

        <Link
          to="/upload"
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
        >
          Translate Another Image
        </Link>
      </div>

      {/* Main Interactive Comparison Viewer */}
      <ComparisonViewer
        inputUrl={job.input_image_url}
        outputUrl={job.output_image_url}
        diffUrl={job.difference_map_url}
        jobData={job}
      />

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

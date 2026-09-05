import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  UploadCloud,
  Clock,
  Layers,
  Cpu,
  ArrowRight,
  Sparkles,
  AlertCircle,
  FileImage,
  ChevronRight,
} from 'lucide-react';
import { inferenceAPI, healthAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const DashboardPage = () => {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [histRes, healthRes] = await Promise.all([
          inferenceAPI.getHistory(1, 5),
          healthAPI.getHealth(),
        ]);
        if (histRes.success && histRes.data) {
          setHistory(histRes.data.items || []);
        }
        if (healthRes.success && healthRes.data) {
          setHealth(healthRes.data);
        }
      } catch (err) {
        setError('Failed to load dashboard statistics.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xl">
        <div>
          <span className="text-xs font-mono text-cyan-400 uppercase tracking-wide">
            Welcome back, {user?.full_name || user?.email?.split('@')[0]}
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mt-1">
            Medical Image Translation Studio
          </h1>
          <p className="text-xs text-slate-400 mt-2 max-w-xl">
            Input planar X-ray projections to synthesize cross-sectional CT approximations with the pix2pix generative network.
          </p>
        </div>
        <Link
          to="/upload"
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm shadow-lg shadow-cyan-600/25 transition-all shrink-0"
        >
          <UploadCloud className="w-4 h-4" />
          New Translation
        </Link>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Recent Inferences</span>
            <div className="w-8 h-8 rounded-lg bg-cyan-950 text-cyan-400 flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white mt-2">{history.length}</p>
          <span className="text-[11px] text-slate-500">Total translations run</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Active Translation Model</span>
            <div className="w-8 h-8 rounded-lg bg-blue-950 text-blue-400 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white mt-2 font-mono">v1 (pix2pix)</p>
          <span className="text-[11px] text-slate-500">U-Net 256 + PatchGAN</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Compute Engine</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-950 text-indigo-400 flex items-center justify-center">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white mt-2 uppercase font-mono">
            {health?.device || 'CPU Fallback'}
          </p>
          <span className="text-[11px] text-slate-500">
            {health?.device?.includes('cuda') ? 'GPU Accelerated' : 'PyTorch Standard Runtime'}
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Backend Health</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-950 text-emerald-400 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-emerald-400 mt-2 uppercase font-mono">
            {health?.status || 'Online'}
          </p>
          <span className="text-[11px] text-slate-500">API, DB, and Model Cache operational</span>
        </div>
      </div>

      {/* Recent Jobs Table / List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Recent Translation Jobs</h2>
            <p className="text-xs text-slate-400">Inspected outputs generated during recent sessions</p>
          </div>
          <Link
            to="/history"
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
          >
            View All History
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading recent inferences...</div>
        ) : history.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-slate-500 mx-auto">
              <FileImage className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-300">No translation jobs recorded yet</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Upload your first 2D X-ray projection to test the deep translation pipeline.
            </p>
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium mt-2 transition-colors"
            >
              <UploadCloud className="w-4 h-4" />
              Upload Image Now
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {history.map((job) => (
              <Link
                key={job.id}
                to={`/result/${job.id}`}
                className="p-4 flex items-center justify-between hover:bg-slate-800/40 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  {job.output_image_url ? (
                    <img
                      src={job.output_image_url}
                      alt="Thumbnail"
                      className="w-12 h-12 rounded-lg object-cover border border-slate-800 bg-black shrink-0"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-slate-800 flex items-center justify-center text-slate-500 shrink-0">
                      <FileImage className="w-5 h-5" />
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-medium text-slate-200 group-hover:text-cyan-400 transition-colors">
                      {job.original_filename || `Job ${job.id.substring(0, 8)}`}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                      <span>Model: <strong className="text-slate-300 font-mono">{job.model_version}</strong></span>
                      {job.processing_time_ms && (
                        <span>Latency: <strong className="text-slate-300 font-mono">{job.processing_time_ms} ms</strong></span>
                      )}
                      <span>{new Date(job.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`px-2.5 py-1 rounded-full text-[11px] font-mono uppercase tracking-wide font-medium ${
                      job.status === 'COMPLETED'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : 'bg-red-950 text-red-400 border border-red-800'
                    }`}
                  >
                    {job.status}
                  </span>
                  <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

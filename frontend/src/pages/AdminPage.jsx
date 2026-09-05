import React, { useState, useEffect } from 'react';
import { ShieldCheck, Users, Activity, Clock, Cpu, Server, CheckCircle2, AlertTriangle } from 'lucide-react';
import { modelAPI, healthAPI } from '../api/client';

export const AdminPage = () => {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAdminMetrics = async () => {
      try {
        const [statsRes, healthRes] = await Promise.all([
          modelAPI.getAdminStats(),
          healthAPI.getHealth(),
        ]);
        if (statsRes.success && statsRes.data) {
          setStats(statsRes.data);
        }
        if (healthRes.success && healthRes.data) {
          setHealth(healthRes.data);
        }
      } catch (err) {
        setError('Failed to load administrative telemetry.');
      } finally {
        setLoading(false);
      }
    };

    fetchAdminMetrics();
  }, []);

  if (loading) {
    return <div className="p-12 text-center text-xs text-slate-400">Loading system telemetry...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <div className="flex items-center gap-2 text-emerald-400 text-xs font-mono font-medium">
          <ShieldCheck className="w-4 h-4" />
          Administrative Control Center
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mt-1">
          System Metrics & Infrastructure Health
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Real-time workload metrics, database connection health, and model execution telemetry.
        </p>
      </div>

      {error && (
        <div className="bg-red-950/50 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Registered Users</span>
            <Users className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-3xl font-bold text-white mt-2">{stats?.total_users ?? '—'}</p>
          <span className="text-[11px] text-slate-500">Authorized accounts</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Total Inferences Executed</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-white mt-2">{stats?.total_inferences ?? '—'}</p>
          <span className="text-[11px] text-emerald-400 font-mono">
            {stats?.completed_inferences ?? 0} Completed / {stats?.failed_inferences ?? 0} Failed
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Average Latency</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-3xl font-bold text-white mt-2 font-mono">{stats?.average_latency_ms ?? 0} ms</p>
          <span className="text-[11px] text-slate-500">Per 256×256 translation slice</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">GPU Acceleration</span>
            <Cpu className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-3xl font-bold text-white mt-2 font-mono">
            {stats?.gpu_available ? 'CUDA ACTIVE' : 'CPU FALLBACK'}
          </p>
          <span className="text-[11px] text-slate-500">
            Hardware: {health?.device || 'CPU'}
          </span>
        </div>
      </div>

      {/* Subsystems Health Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 shadow-xl">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Server className="w-4 h-4 text-cyan-400" />
          Subsystem Status Matrix
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 block mb-1">FastAPI Gateway</span>
            <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-mono font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              {health?.api?.status?.toUpperCase() || 'HEALTHY'}
            </div>
          </div>

          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 block mb-1">Database Connection</span>
            <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-mono font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              {health?.database?.status?.toUpperCase() || 'HEALTHY'}
            </div>
          </div>

          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 block mb-1">Asset Storage Layer</span>
            <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-mono font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              {health?.storage?.status?.toUpperCase() || 'HEALTHY'}
            </div>
          </div>

          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 block mb-1">In-Memory Model Cache</span>
            <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-mono font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              {health?.model_cache?.status?.toUpperCase() || 'HEALTHY'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { History, Eye, Trash2, ChevronLeft, ChevronRight, FileImage, AlertCircle } from 'lucide-react';
import { inferenceAPI } from '../api/client';

export const HistoryPage = () => {
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHistory = async (pageNumber) => {
    setLoading(true);
    try {
      const res = await inferenceAPI.getHistory(pageNumber, pageSize);
      if (res.success && res.data) {
        setJobs(res.data.items || []);
        setTotal(res.data.total || 0);
        setPage(res.data.page || 1);
      }
    } catch (err) {
      setError('Failed to retrieve inference history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(page);
  }, [page]);

  const handleDelete = async (id, e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm('Delete this inference job and its stored artifacts?')) return;

    try {
      await inferenceAPI.deleteJob(id);
      fetchHistory(page);
    } catch (err) {
      alert('Failed to delete inference job.');
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <History className="w-6 h-6 text-cyan-400" />
            Inference History
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete historical record of translation sessions ({total} total records)
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-950/50 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400">Loading history records...</div>
        ) : jobs.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <FileImage className="w-10 h-10 text-slate-600 mx-auto" />
            <p className="text-sm font-medium text-slate-300">No translation records found</p>
            <Link
              to="/upload"
              className="inline-block px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium transition-colors"
            >
              Upload an Image
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400 font-mono">
                <tr>
                  <th className="py-3 px-4">Thumbnails (In / Out)</th>
                  <th className="py-3 px-4">Filename</th>
                  <th className="py-3 px-4">Model</th>
                  <th className="py-3 px-4">Latency</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {job.input_image_url ? (
                          <img
                            src={job.input_image_url}
                            alt="Input"
                            className="w-9 h-9 rounded object-cover border border-slate-800 bg-black"
                          />
                        ) : (
                          <div className="w-9 h-9 rounded bg-slate-800" />
                        )}
                        <span className="text-slate-600">→</span>
                        {job.output_image_url ? (
                          <img
                            src={job.output_image_url}
                            alt="Output"
                            className="w-9 h-9 rounded object-cover border border-slate-800 bg-black"
                          />
                        ) : (
                          <div className="w-9 h-9 rounded bg-slate-800" />
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-200">
                      {job.original_filename || job.id.substring(0, 12)}
                    </td>
                    <td className="py-3 px-4 font-mono text-cyan-400">{job.model_version}</td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {job.processing_time_ms ? `${job.processing_time_ms} ms` : '—'}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wide ${
                          job.status === 'COMPLETED'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-red-950 text-red-400 border border-red-800'
                        }`}
                      >
                        {job.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/result/${job.id}`}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition-colors"
                          title="View Result Comparison"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={(e) => handleDelete(job.id, e)}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-950/40 text-slate-400 hover:text-red-400 transition-colors"
                          title="Delete Job"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="px-6 py-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-400">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1 rounded bg-slate-900 border border-slate-800 disabled:opacity-30 hover:bg-slate-800"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1 rounded bg-slate-900 border border-slate-800 disabled:opacity-30 hover:bg-slate-800"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

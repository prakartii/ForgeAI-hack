import React from 'react';
import { Activity, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export function HealthBadge({ health, loading, error, onRefresh }) {
  if (loading && !health) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-100 border border-slate-200 text-xs font-mono text-slate-600">
        <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-500" />
        <span>Connecting to backend...</span>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-red-50 border border-red-200 text-xs font-mono text-red-700">
        <AlertCircle className="w-3.5 h-3.5 text-red-600" />
        <span>Backend Disconnected</span>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="ml-1 text-red-500 hover:text-red-800 transition-colors"
            title="Retry connection"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        )}
      </div>
    );
  }

  const isHealthy = health.status === 'ok';

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-emerald-50 border border-emerald-200 text-xs font-mono text-emerald-800">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        <span className="font-semibold">Backend:</span>
        <span>{health.status}</span>
        <span className="text-emerald-400">|</span>
        <span className="font-semibold">DB:</span>
        <span>{health.database}</span>
        <span className="text-emerald-400">|</span>
        <span className="text-emerald-600 font-sans">v{health.version}</span>
      </div>
      {onRefresh && (
        <button
          onClick={onRefresh}
          className="text-slate-400 hover:text-slate-600 p-1 rounded transition-colors"
          title="Refresh health check"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      )}
    </div>
  );
}

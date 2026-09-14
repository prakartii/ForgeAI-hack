import React from 'react';
import { RefreshCw } from 'lucide-react';

function Dot({ tone }) {
  const toneClasses = {
    verdant: 'bg-verdant',
    brass: 'bg-brass',
    seal: 'bg-seal',
    slate: 'bg-ink-faint',
  };
  return <span className={`w-1.5 h-1.5 rounded-full ${toneClasses[tone] || toneClasses.slate}`} />;
}

export function HealthBadge({ health, loading, error, onRefresh }) {
  if (loading && !health) {
    return (
      <div className="flex items-center gap-2 text-[12px] text-ink-faint">
        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
        <span>Connecting to backend…</span>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="flex items-center gap-2 text-[12px] text-seal-700">
        <Dot tone="seal" />
        <span>Backend unreachable</span>
        {onRefresh && (
          <button onClick={onRefresh} className="text-seal-600 hover:text-seal-700 transition-colors" title="Retry connection">
            <RefreshCw className="w-3 h-3" />
          </button>
        )}
      </div>
    );
  }

  const graphOk = health.graph_database === 'connected';

  return (
    <div className="flex items-center gap-4 text-[12px] text-ink-soft">
      <span className="flex items-center gap-1.5">
        <Dot tone={health.status === 'ok' ? 'verdant' : 'brass'} />
        Backend v{health.version}
      </span>
      <span className="flex items-center gap-1.5">
        <Dot tone={health.database === 'connected' ? 'verdant' : 'slate'} />
        SQLite
      </span>
      <span className="flex items-center gap-1.5">
        <Dot tone={graphOk ? 'verdant' : 'slate'} />
        Neo4j {graphOk ? '' : '(standby)'}
      </span>
      {onRefresh && (
        <button onClick={onRefresh} className="text-ink-faint hover:text-ink-soft transition-colors" title="Refresh health check">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      )}
    </div>
  );
}

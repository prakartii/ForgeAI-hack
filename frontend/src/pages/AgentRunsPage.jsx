import React from 'react';
import { PlayCircle, Clock } from 'lucide-react';

export function AgentRunsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Agent Runs</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §8 & §9: AgentRun execution traces and envelope records
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3 text-slate-400">
          <PlayCircle className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-800">No Execution Runs Yet</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          Agent runs will be populated during Phase 3 (Agent Runtime) and Phase 4 (Trace System).
          Traces will link run IDs with claim sessions and counterfactual groups.
        </p>
      </div>
    </div>
  );
}

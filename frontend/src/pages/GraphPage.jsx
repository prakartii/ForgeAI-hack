import React from 'react';
import { GitFork } from 'lucide-react';

export function GraphPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Execution Graph</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §10: Causal execution graph for workflow forensics (React Flow)
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3 text-slate-400">
          <GitFork className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-800">Causal Workflow Graph</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          Displays sequence flow: Claim → Intake Output → Adjudication Decision → Explanation → Verification → Customer Communication.
          Will be integrated with React Flow in Phase 4 (Trace System).
        </p>
      </div>
    </div>
  );
}

import React from 'react';
import { AlertTriangle } from 'lucide-react';

export function FailuresPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Diagnosed Failures</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §13, §14 & §15: Fairness, Workflow, and Evidence behavioral failure diagnoses
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3 text-slate-400">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-800">No Active Failures Diagnosed</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          Controlled failure injection in v1 (demographic proxy sensitivity & workflow bypass) will be evaluated in Phase 6.
        </p>
      </div>
    </div>
  );
}

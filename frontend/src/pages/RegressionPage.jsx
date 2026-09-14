import React from 'react';
import { History, ShieldCheck } from 'lucide-react';

export function RegressionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Regression Suite</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §19: Permanent historical failure suite preventing silent regression recurrence
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3 text-slate-400">
          <History className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-800">No Regression Tests Registered Yet</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          Every discovered failure automatically registers as a permanent regression test in Phase 10.
          Candidate agent versions will be evaluated against this suite before release gating.
        </p>
      </div>
    </div>
  );
}

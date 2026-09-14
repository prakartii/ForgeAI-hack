import React, { useState, useEffect } from 'react';
import { Eye, ExternalLink } from 'lucide-react';
import { fetchPrismStatus } from '../services/api';

export function PrismEvidencePage() {
  const [prismStatus, setPrismStatus] = useState(null);

  useEffect(() => {
    fetchPrismStatus().then(setPrismStatus).catch(() => null);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">PRISM Evidence</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §21 & §31: Backing traces, evaluator scores, and diagnostic proofs from PRISM monitor
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-indigo-50 text-indigo-600">
              <Eye className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">PRISM Integration Status</h3>
              <p className="text-xs text-slate-500 font-mono">
                {prismStatus?.base_url || 'https://api.blockconvey.com'}
              </p>
            </div>
          </div>
          <span className={`text-xs font-mono px-2.5 py-1 rounded font-semibold ${
            prismStatus?.status === 'configured'
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : 'bg-amber-50 text-amber-700 border border-amber-200'
          }`}>
            {prismStatus?.status === 'configured' ? 'CONFIGURED' : 'PENDING CREDENTIALS'}
          </span>
        </div>

        <div className="text-xs text-slate-600 space-y-2">
          <p className="font-semibold text-slate-800">Non-negotiable rule (CLAUDE.md §31):</p>
          <blockquote className="p-3 bg-slate-50 rounded border-l-2 border-indigo-400 italic text-slate-600">
            "MUST NEVER BE FAKED: PRISM results, before/after metrics, regression results, release status...
            If a capability is unavailable, implement a clearly-labeled, verified fallback — never invent an output."
          </blockquote>
          <p className="text-slate-500 pt-2">
            In Phase 5, execution traces will stream to PRISM via the official <code className="bg-slate-100 px-1 py-0.5 rounded font-mono">blockconvey-monitor</code> SDK.
          </p>
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { ShieldCheck, CheckCircle2, XCircle } from 'lucide-react';

export function ReleaseGatePage() {
  const gateChecklist = [
    { rule: 'Critical ABI violations = 0', desc: 'No active critical behavioral contract breaches' },
    { rule: 'Fairness threshold passes', desc: 'Zero outcome variance across matched counterfactual pairs' },
    { rule: 'Prohibited factors absent from rationale', desc: 'Context sanitization successfully verified' },
    { rule: 'Required workflow steps complete', desc: 'Explanation verified before customer communication' },
    { rule: 'Evidence requirements pass', desc: 'All consequential decisions backed by verified evidence' },
    { rule: 'Historical regressions pass', desc: '100% pass rate on permanent historical failure suite' },
    { rule: 'Hardened scenarios pass', desc: 'Challenge ladder levels 1-4 pass successfully' },
    { rule: 'Required PRISM evidence exists', desc: 'Traces and evaluators fetched from PRISM (not assumed)' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Release Gate</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §23: Strict deployment gating. PASS only if all criteria are satisfied; otherwise BLOCKED.
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between pb-5 border-b border-slate-200">
          <div>
            <div className="text-xs font-mono text-slate-500 uppercase">Target Candidate</div>
            <div className="text-lg font-bold text-slate-900 font-mono">Agent Candidate: v2 (Staged)</div>
          </div>
          <div className="px-4 py-1.5 rounded bg-slate-100 text-slate-700 font-mono text-xs font-bold border border-slate-300">
            GATE STATUS: PENDING EVALUATION
          </div>
        </div>

        <div className="mt-6">
          <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider font-mono mb-3">
            Mandatory Acceptance Conditions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {gateChecklist.map((item, idx) => (
              <div key={idx} className="p-3 bg-slate-50 rounded border border-slate-200 flex items-start gap-2.5 text-xs">
                <span className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center text-[10px] text-slate-400 mt-0.5 flex-shrink-0 font-mono">
                  {idx + 1}
                </span>
                <div>
                  <div className="font-semibold text-slate-800">{item.rule}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

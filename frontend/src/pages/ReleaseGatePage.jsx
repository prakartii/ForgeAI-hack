import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, XCircle, PlayCircle } from 'lucide-react';
import { runReleaseGate } from '../services/api';
import { ActionButton, Badge, Card, ErrorNote } from '../components/ui';

const CLAUSE_LABELS = {
  critical_abi_violations: 'Critical ABI violations = 0',
  fairness_threshold: 'Fairness threshold passes',
  workflow_compliance: 'Required workflow steps complete',
  evidence_completeness: 'Evidence requirements pass',
  historical_regressions: 'Historical regressions pass',
  hardened_scenarios: 'Hardened scenarios pass',
  prism_evidence: 'Required PRISM evidence exists',
};

export function ReleaseGatePage() {
  const [candidateVersion, setCandidateVersion] = useState('v2');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = async () => {
    setLoading(true);
    try {
      setResult(await runReleaseGate({ candidate_version: candidateVersion }));
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Release Gate</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §23: strict deployment gating — PASS only if every condition below actually holds; otherwise BLOCKED.
        </p>
      </div>

      <Card icon={PlayCircle} title="Run Release Gate" tag="POST /api/gates/run">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs">
            <span className="block text-slate-500 mb-1 font-mono">candidate_version</span>
            <select value={candidateVersion} onChange={(e) => setCandidateVersion(e.target.value)} className="border border-slate-300 rounded px-2 py-1.5 text-xs font-mono">
              <option value="v1">v1</option>
              <option value="v2">v2</option>
            </select>
          </label>
          <ActionButton onClick={run} loading={loading}>Evaluate Gate</ActionButton>
        </div>
        <ErrorNote message={error} />
      </Card>

      <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between pb-5 border-b border-slate-200">
          <div>
            <div className="text-xs font-mono text-slate-500 uppercase">Target Candidate</div>
            <div className="text-lg font-bold text-slate-900 font-mono">Agent Candidate: {result?.candidate_version || candidateVersion}</div>
          </div>
          <div className={`px-4 py-1.5 rounded font-mono text-xs font-bold border ${
            !result
              ? 'bg-slate-100 text-slate-700 border-slate-300'
              : result.status === 'PASS'
              ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
              : 'bg-red-50 text-red-700 border-red-300'
          }`}>
            GATE STATUS: {result ? result.status : 'PENDING EVALUATION'}
          </div>
        </div>

        <div className="mt-6">
          <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider font-mono mb-3">
            Mandatory Acceptance Conditions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(CLAUSE_LABELS).map(([key, label], idx) => {
              const detail = result?.failure_summary?.[key];
              const passed = detail?.passed;
              return (
                <div key={key} className="p-3 bg-slate-50 rounded border border-slate-200 flex items-start gap-2.5 text-xs">
                  {result ? (
                    passed ? <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" /> : <XCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center text-[10px] text-slate-400 mt-0.5 flex-shrink-0 font-mono">
                      {idx + 1}
                    </span>
                  )}
                  <div>
                    <div className="font-semibold text-slate-800">{label}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">{detail?.detail || 'Not yet evaluated'}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {result?.violated_clauses?.length > 0 && (
          <div className="mt-5 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="text-xs font-semibold text-red-800 mb-1.5 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" /> Violated Clauses
            </div>
            <div className="flex flex-wrap gap-1.5">
              {result.violated_clauses.map((c) => <Badge key={c} tone="red">{c}</Badge>)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

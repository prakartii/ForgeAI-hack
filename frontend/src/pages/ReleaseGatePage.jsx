import React, { useState } from 'react';
import { CheckCircle2, XCircle, PlayCircle } from 'lucide-react';
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

  const status = result?.status;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-medium text-ink">Release gate</h2>
        <p className="text-[13px] text-ink-soft mt-1">Passes only if every condition below actually holds — otherwise it's blocked</p>
      </div>

      <Card icon={PlayCircle} title="Evaluate the gate" tag="POST /api/gates/run">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-[12px]">
            <span className="block text-ink-faint mb-1">Candidate version</span>
            <select value={candidateVersion} onChange={(e) => setCandidateVersion(e.target.value)} className="border border-line-strong rounded px-2.5 py-1.5 text-[13px] bg-paper-panel focus:border-ledger">
              <option value="v1">v1</option>
              <option value="v2">v2</option>
            </select>
          </label>
          <ActionButton onClick={run} loading={loading}>Evaluate gate</ActionButton>
        </div>
        <ErrorNote message={error} />
      </Card>

      <div className="bg-paper-panel rounded-md border border-line p-6">
        <div className="flex items-center justify-between pb-5 border-b border-line gap-4">
          <div>
            <div className="text-[12px] text-ink-faint">Candidate</div>
            <div className="text-xl font-serif text-ink">{result?.candidate_version || candidateVersion}</div>
          </div>
          <div className={`px-5 py-2.5 rounded border text-center ${
            !status
              ? 'border-line-strong text-ink-faint'
              : status === 'PASS'
              ? 'border-verdant-100 bg-verdant-50 text-verdant-700'
              : 'border-seal-100 bg-seal-50 text-seal-700'
          }`}>
            <div className="font-serif text-lg leading-none">{status || 'Pending'}</div>
            <div className="text-[11px] mt-1 opacity-80">{status ? 'gate status' : 'not yet evaluated'}</div>
          </div>
        </div>

        <div className="mt-6">
          <h3 className="text-[13px] font-medium text-ink mb-3">Mandatory acceptance conditions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(CLAUSE_LABELS).map(([key, label], idx) => {
              const detail = result?.failure_summary?.[key];
              const passed = detail?.passed;
              return (
                <div key={key} className="p-3.5 rounded border border-line flex items-start gap-2.5 text-[13px]">
                  {result ? (
                    passed ? <CheckCircle2 className="w-4 h-4 text-verdant-600 mt-0.5 flex-shrink-0" /> : <XCircle className="w-4 h-4 text-seal-600 mt-0.5 flex-shrink-0" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border border-line-strong flex items-center justify-center text-[10px] text-ink-faint mt-0.5 flex-shrink-0">
                      {idx + 1}
                    </span>
                  )}
                  <div>
                    <div className="font-medium text-ink">{label}</div>
                    <div className="text-[11px] text-ink-faint mt-0.5">{detail?.detail || 'Not yet evaluated'}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {result?.violated_clauses?.length > 0 && (
          <div className="mt-5 p-3.5 bg-seal-50 border border-seal-100 rounded">
            <div className="text-[13px] font-medium text-seal-700 mb-2">Violated clauses</div>
            <div className="flex flex-wrap gap-x-4 gap-y-1.5">
              {result.violated_clauses.map((c) => <Badge key={c} tone="red">{c.replace(/_/g, ' ')}</Badge>)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

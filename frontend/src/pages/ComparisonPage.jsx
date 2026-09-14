import React, { useState } from 'react';
import { GitCompare, PlayCircle } from 'lucide-react';
import { computeMetrics } from '../services/api';
import { ActionButton, Card, ErrorNote } from '../components/ui';

const METRICS = [
  { key: 'pairwise_consistency', label: 'Pairwise Consistency', description: 'Matched legitimate facts producing identical decisions' },
  { key: 'workflow_compliance', label: 'Workflow Compliance', description: 'Completion rate of mandatory handoffs without bypass' },
  { key: 'evidence_completeness', label: 'Evidence Completeness', description: 'Explanations with valid, evidence-backed citations' },
  { key: 'challenge_robustness', label: 'Challenge Robustness', description: 'Hardening ladder pass rate across L1–L4' },
  { key: 'task_correctness', label: 'Task Correctness', description: 'Agent decision matches the deterministic oracle' },
  { key: 'regression_pass_rate', label: 'Regression Pass Rate', description: 'Historical failure suite passing percentage' },
];

function fmt(v) {
  return v === null || v === undefined ? '[MEASURED VALUE]' : `${Math.round(v * 100)}%`;
}

function delta(before, after) {
  if (before === null || before === undefined || after === null || after === undefined) return '—';
  const d = Math.round((after - before) * 100);
  if (d === 0) return '±0%';
  return d > 0 ? `+${d}%` : `${d}%`;
}

export function ComparisonPage() {
  const [v1, setV1] = useState(null);
  const [v2, setV2] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sampleSize, setSampleSize] = useState(150);

  const runComparison = async () => {
    setLoading(true);
    try {
      const [v1Metrics, v2Metrics] = await Promise.all([
        computeMetrics({ candidate_version: 'v1', enforced: false, sample_size: sampleSize }),
        computeMetrics({ candidate_version: 'v2', enforced: true, sample_size: sampleSize }),
      ]);
      setV1(v1Metrics);
      setV2(v2Metrics);
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
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Version Comparison (v1 vs v2)</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §20, §22 & §24: real measured before/after metrics — v1 unenforced vs v2 under compiled ABI enforcement
        </p>
      </div>

      <Card icon={PlayCircle} title="Compute Real Metrics" tag="POST /api/metrics/compute ×2">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs">
            <span className="block text-slate-500 mb-1 font-mono">sample_size</span>
            <input
              type="number"
              value={sampleSize}
              onChange={(e) => setSampleSize(Number(e.target.value))}
              className="border border-slate-300 rounded px-2 py-1.5 text-xs font-mono w-28"
            />
          </label>
          <ActionButton onClick={runComparison} loading={loading}>
            Run v1 vs v2 (may take a few seconds)
          </ActionButton>
          {v1 && <span className="text-xs font-mono text-slate-400">sample size: {v1.sample_size}</span>}
        </div>
        <ErrorNote message={error} />
      </Card>

      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-700 font-mono">Reliability Metrics Matrix</span>
          <span className="text-[11px] font-mono text-slate-500 italic">
            CLAUDE.md §22: no fabricated data — computed from real executions only
          </span>
        </div>

        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50/50 text-slate-600 font-mono">
              <th className="py-3 px-4 font-semibold">Evaluation Metric</th>
              <th className="py-3 px-4 font-semibold text-center w-36">v1 (Unenforced)</th>
              <th className="py-3 px-4 font-semibold text-center w-36">v2 (ABI-Enforced)</th>
              <th className="py-3 px-4 font-semibold text-center w-32">Delta</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono text-slate-800">
            {METRICS.map((m) => (
              <tr key={m.key} className="hover:bg-slate-50/50">
                <td className="py-3 px-4">
                  <div className="font-semibold text-slate-900 font-sans">{m.label}</div>
                  <div className="text-[11px] text-slate-500 font-sans">{m.description}</div>
                </td>
                <td className="py-3 px-4 text-center">{fmt(v1?.[m.key])}</td>
                <td className="py-3 px-4 text-center font-bold text-emerald-700">{fmt(v2?.[m.key])}</td>
                <td className="py-3 px-4 text-center text-slate-500">{v1 && v2 ? delta(v1[m.key], v2[m.key]) : '[MEASURED VALUE]'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

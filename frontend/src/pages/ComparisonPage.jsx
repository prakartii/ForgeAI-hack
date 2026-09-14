import React, { useState } from 'react';
import { PlayCircle } from 'lucide-react';
import { computeMetrics } from '../services/api';
import { ActionButton, Card, ErrorNote } from '../components/ui';

const METRICS = [
  { key: 'pairwise_consistency', label: 'Pairwise consistency', description: 'Matched legitimate facts producing identical decisions' },
  { key: 'workflow_compliance', label: 'Workflow compliance', description: 'Completion rate of mandatory handoffs without bypass' },
  { key: 'evidence_completeness', label: 'Evidence completeness', description: 'Explanations with valid, evidence-backed citations' },
  { key: 'challenge_robustness', label: 'Challenge robustness', description: 'Hardening ladder pass rate across L1–L4' },
  { key: 'task_correctness', label: 'Task correctness', description: 'Agent decision matches the deterministic oracle' },
  { key: 'regression_pass_rate', label: 'Regression pass rate', description: 'Historical failure suite passing percentage' },
];

function fmt(v) {
  return v === null || v === undefined ? '—' : `${Math.round(v * 100)}%`;
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
        <h2 className="text-2xl font-medium text-ink">Version comparison</h2>
        <p className="text-[13px] text-ink-soft mt-1">Real, measured before/after metrics — v1 unenforced against v2 under compiled ABI enforcement</p>
      </div>

      <Card icon={PlayCircle} title="Compute real metrics" tag="POST /api/metrics/compute ×2">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-[12px]">
            <span className="block text-ink-faint mb-1">Sample size</span>
            <input
              type="number"
              value={sampleSize}
              onChange={(e) => setSampleSize(Number(e.target.value))}
              className="border border-line-strong rounded px-2.5 py-1.5 text-[13px] font-mono w-28 bg-paper-panel focus:border-ledger"
            />
          </label>
          <ActionButton onClick={runComparison} loading={loading}>
            Run v1 vs v2 — may take a few seconds
          </ActionButton>
          {v1 && <span className="text-[12px] text-ink-faint">Sample size: {v1.sample_size}</span>}
        </div>
        <ErrorNote message={error} />
      </Card>

      <Card noPadding>
        <div className="px-5 py-3 border-b border-line flex items-center justify-between">
          <span className="text-[13px] font-semibold text-ink">Reliability metrics matrix</span>
          <span className="text-[11px] text-ink-faint">Computed from real executions — never fabricated</span>
        </div>

        <table className="w-full text-left text-[13px] border-collapse">
          <thead>
            <tr className="border-b border-line text-ink-faint text-[11px]">
              <th className="py-2.5 pl-5 pr-4 font-normal">Evaluation metric</th>
              <th className="py-2.5 px-4 font-normal text-center w-32">v1 (unenforced)</th>
              <th className="py-2.5 px-4 font-normal text-center w-32">v2 (ABI-enforced)</th>
              <th className="py-2.5 pr-5 pl-4 font-normal text-center w-28">Delta</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {METRICS.map((m) => (
              <tr key={m.key}>
                <td className="py-3 pl-5 pr-4">
                  <div className="font-medium text-ink">{m.label}</div>
                  <div className="text-[11px] text-ink-faint mt-0.5">{m.description}</div>
                </td>
                <td className="py-3 px-4 text-center font-mono text-ink-soft">{fmt(v1?.[m.key])}</td>
                <td className="py-3 px-4 text-center font-mono font-semibold text-verdant-700">{fmt(v2?.[m.key])}</td>
                <td className="py-3 pr-5 pl-4 text-center font-mono text-ink-faint">{v1 && v2 ? delta(v1[m.key], v2[m.key]) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

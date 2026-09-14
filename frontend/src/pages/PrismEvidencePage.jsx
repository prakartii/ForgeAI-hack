import React, { useEffect, useState } from 'react';
import { Eye } from 'lucide-react';
import { fetchPrismStatus, fetchRuns } from '../services/api';
import { Badge, Card } from '../components/ui';

export function PrismEvidencePage() {
  const [prismStatus, setPrismStatus] = useState(null);
  const [runs, setRuns] = useState([]);

  useEffect(() => {
    fetchPrismStatus().then(setPrismStatus).catch(() => null);
    fetchRuns().then(setRuns).catch(() => null);
  }, []);

  const configured = prismStatus?.status === 'configured';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-medium text-ink">PRISM evidence</h2>
        <p className="text-[13px] text-ink-soft mt-1">Backing traces, evaluator scores, and diagnostic proofs from PRISM</p>
      </div>

      <Card title="Integration status" icon={Eye}>
        <div className="flex items-center justify-between border-b border-line pb-4 mb-4">
          <div>
            <p className="text-[12px] text-ink-faint font-mono">{prismStatus?.base_url || 'https://api.blockconvey.com'}</p>
            <p className="text-[13px] text-ink-soft mt-1">{prismStatus?.message}</p>
          </div>
          <Badge tone={configured ? 'emerald' : 'amber'}>{configured ? 'Configured' : 'Not configured'}</Badge>
        </div>

        {!configured && (
          <blockquote className="pl-4 border-l-2 border-ledger-100 italic text-[13px] text-ink-soft leading-relaxed">
            "PRISM results, before/after metrics, regression results, and release status must never be faked.
            If a capability is unavailable, implement a clearly-labeled, verified fallback — never invent an output."
          </blockquote>
        )}
      </Card>

      <Card title="Run to PRISM session correlation" tag="agent_runs.prism_session_id" noPadding>
        <p className="text-[13px] text-ink-soft p-5 pb-0">
          Every agent run carries a <code className="font-mono text-[12px]">prism_session_id</code> once its trace is submitted
          to PRISM as a trajectory. With no PRISM credentials configured here, this column is honestly
          empty rather than a placeholder score.
        </p>
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left text-ink-faint text-[11px] border-b border-line">
                <th className="py-2 pl-5 pr-4 font-normal">Run ID</th>
                <th className="py-2 pr-4 font-normal">Claim</th>
                <th className="py-2 pr-4 font-normal">Agent</th>
                <th className="py-2 pr-5 font-normal">PRISM session</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {runs.slice(0, 15).map((run) => (
                <tr key={run.run_id}>
                  <td className="py-2 pl-5 pr-4 font-mono">{run.run_id}</td>
                  <td className="py-2 pr-4 font-mono">{run.claim_id}</td>
                  <td className="py-2 pr-4">{run.agent_name}</td>
                  <td className="py-2 pr-5 font-mono text-ink-faint">
                    {run.prism_session_id || 'unavailable'}
                  </td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr><td colSpan={4} className="py-6 text-center text-ink-faint">No runs yet — execute a claim from Agent Runs.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

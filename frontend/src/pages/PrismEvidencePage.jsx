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
        <h2 className="text-xl font-bold tracking-tight text-slate-900">PRISM Evidence</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §21 & §31: backing traces, evaluator scores, and diagnostic proofs from PRISM
        </p>
      </div>

      <Card title="PRISM Integration Status" icon={Eye}>
        <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
          <div>
            <p className="text-xs text-slate-500 font-mono">{prismStatus?.base_url || 'https://api.blockconvey.com'}</p>
            <p className="text-xs text-slate-600 mt-1">{prismStatus?.message}</p>
          </div>
          <Badge tone={configured ? 'emerald' : 'amber'}>{configured ? 'CONFIGURED' : 'NOT CONFIGURED'}</Badge>
        </div>

        {!configured && (
          <blockquote className="p-3 bg-slate-50 rounded border-l-2 border-indigo-400 italic text-xs text-slate-600">
            "MUST NEVER BE FAKED: PRISM results, before/after metrics, regression results, release status...
            If a capability is unavailable, implement a clearly-labeled, verified fallback — never invent an output."
            <span className="not-italic font-mono text-slate-400 block mt-1">— CLAUDE.md §31</span>
          </blockquote>
        )}
      </Card>

      <Card title="Run → PRISM Session Correlation" tag="agent_runs.prism_session_id">
        <p className="text-xs text-slate-500 mb-3">
          Every AgentRun carries a <code className="font-mono">prism_session_id</code> once its trace is submitted
          to PRISM as a trajectory. With no PRISM credentials configured in this environment, this column is honestly
          empty rather than a placeholder score.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-slate-500 font-mono uppercase text-[10px] border-b border-slate-200">
                <th className="py-2 pr-4">Run ID</th>
                <th className="py-2 pr-4">Claim</th>
                <th className="py-2 pr-4">Agent</th>
                <th className="py-2 pr-4">PRISM Session</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {runs.slice(0, 15).map((run) => (
                <tr key={run.run_id}>
                  <td className="py-2 pr-4 font-mono">{run.run_id}</td>
                  <td className="py-2 pr-4 font-mono">{run.claim_id}</td>
                  <td className="py-2 pr-4 font-mono">{run.agent_name}</td>
                  <td className="py-2 pr-4 font-mono text-slate-400">
                    {run.prism_session_id || 'unavailable'}
                  </td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr><td colSpan={4} className="py-4 text-center text-slate-400">No runs yet — execute a claim from Agent Runs.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

import React, { useCallback, useEffect, useState } from 'react';
import { PlayCircle, Clock, Zap } from 'lucide-react';
import { executeClaimAndReport, fetchRuns } from '../services/api';
import { ActionButton, Badge, Card, EmptyState, ErrorNote } from '../components/ui';

const STATUS_TONE = {
  completed: 'emerald',
  running: 'sky',
  failed: 'red',
  pending: 'slate',
};

export function AgentRunsPage() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [claimId, setClaimId] = useState('IMG_0002');
  const [agentVersion, setAgentVersion] = useState('v1');
  const [enforced, setEnforced] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setRuns(await fetchRuns());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleExecute = async () => {
    setExecuting(true);
    try {
      const result = await executeClaimAndReport({ claim_id: claimId, agent_version: agentVersion, enforced });
      setLastResult(result);
      setError(null);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Agent Runs</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §8 & §9: AgentRun execution traces and envelope records
        </p>
      </div>

      <Card title="Run a Claim" icon={Zap} tag="POST /api/runs/execute">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs">
            <span className="block text-slate-500 mb-1 font-mono">claim_id</span>
            <input
              value={claimId}
              onChange={(e) => setClaimId(e.target.value)}
              className="border border-slate-300 rounded px-2 py-1.5 text-xs font-mono w-40"
            />
          </label>
          <label className="text-xs">
            <span className="block text-slate-500 mb-1 font-mono">agent_version</span>
            <select
              value={agentVersion}
              onChange={(e) => setAgentVersion(e.target.value)}
              className="border border-slate-300 rounded px-2 py-1.5 text-xs font-mono"
            >
              <option value="v1">v1 (controlled weaknesses)</option>
              <option value="v2">v2 (fixed)</option>
            </select>
          </label>
          <label className="text-xs flex items-center gap-1.5 pb-1.5">
            <input type="checkbox" checked={enforced} onChange={(e) => setEnforced(e.target.checked)} />
            <span className="text-slate-600">enforce compiled ABI</span>
          </label>
          <ActionButton onClick={handleExecute} loading={executing}>
            <PlayCircle className="w-3.5 h-3.5" /> Run Pipeline
          </ActionButton>
        </div>
        <ErrorNote message={error} />
        {lastResult && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div>
              <div className="text-slate-500 font-mono">status</div>
              <Badge tone={lastResult.status === 'COMPLETED' ? 'emerald' : lastResult.status?.includes('BLOCKED') ? 'red' : 'amber'}>
                {lastResult.status}
              </Badge>
            </div>
            <div>
              <div className="text-slate-500 font-mono">decision</div>
              <div className="font-mono font-semibold">{lastResult.adjudication?.decision}</div>
            </div>
            <div>
              <div className="text-slate-500 font-mono">payout</div>
              <div className="font-mono font-semibold">INR {lastResult.adjudication?.payout}</div>
            </div>
            <div>
              <div className="text-slate-500 font-mono">explanation verified</div>
              <div className="font-mono font-semibold">{String(!!lastResult.workflow_state?.explanation_verified)}</div>
            </div>
          </div>
        )}
      </Card>

      <Card title="Recent Runs" icon={Clock}>
        {loading ? (
          <p className="text-xs text-slate-500">Loading...</p>
        ) : runs.length === 0 ? (
          <EmptyState
            title="No Execution Runs Yet"
            description="Run a claim above, or load the demo dataset from the Overview page, then rerun."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-500 font-mono uppercase text-[10px] border-b border-slate-200">
                  <th className="py-2 pr-4">Claim</th>
                  <th className="py-2 pr-4">Agent</th>
                  <th className="py-2 pr-4">Version</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Scenario</th>
                  <th className="py-2 pr-4">ABI Version</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {runs.slice(0, 50).map((run) => (
                  <tr key={run.run_id}>
                    <td className="py-2 pr-4 font-mono">{run.claim_id}</td>
                    <td className="py-2 pr-4 font-mono">{run.agent_name}</td>
                    <td className="py-2 pr-4 font-mono">{run.agent_version}</td>
                    <td className="py-2 pr-4"><Badge tone={STATUS_TONE[run.status] || 'slate'}>{run.status}</Badge></td>
                    <td className="py-2 pr-4 font-mono text-slate-500">{run.scenario_id || '-'}</td>
                    <td className="py-2 pr-4 font-mono text-slate-500">{run.abi_version || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

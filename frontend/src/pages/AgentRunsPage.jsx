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
        <h2 className="text-2xl font-medium text-ink">Agent runs</h2>
        <p className="text-[13px] text-ink-soft mt-1">Execute a claim through the live pipeline and browse its trace history</p>
      </div>

      <Card title="Run a claim" icon={Zap} tag="POST /api/runs/execute">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-[12px]">
            <span className="block text-ink-faint mb-1">Claim ID</span>
            <input
              value={claimId}
              onChange={(e) => setClaimId(e.target.value)}
              className="border border-line-strong rounded px-2.5 py-1.5 text-[13px] font-mono w-40 bg-paper-panel focus:border-ledger"
            />
          </label>
          <label className="text-[12px]">
            <span className="block text-ink-faint mb-1">Agent version</span>
            <select
              value={agentVersion}
              onChange={(e) => setAgentVersion(e.target.value)}
              className="border border-line-strong rounded px-2.5 py-1.5 text-[13px] bg-paper-panel focus:border-ledger"
            >
              <option value="v1">v1 — controlled weaknesses</option>
              <option value="v2">v2 — fixed</option>
            </select>
          </label>
          <label className="text-[12px] flex items-center gap-1.5 pb-1.5">
            <input type="checkbox" checked={enforced} onChange={(e) => setEnforced(e.target.checked)} />
            <span className="text-ink-soft">Enforce compiled ABI</span>
          </label>
          <ActionButton onClick={handleExecute} loading={executing}>
            <PlayCircle className="w-3.5 h-3.5" /> Run pipeline
          </ActionButton>
        </div>
        <ErrorNote message={error} />
        {lastResult && (
          <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-[13px]">
            <div>
              <div className="text-ink-faint text-[11px] mb-1">Status</div>
              <Badge tone={lastResult.status === 'COMPLETED' ? 'emerald' : lastResult.status?.includes('BLOCKED') ? 'red' : 'amber'}>
                {lastResult.status}
              </Badge>
            </div>
            <div>
              <div className="text-ink-faint text-[11px] mb-1">Decision</div>
              <div className="font-medium">{lastResult.adjudication?.decision}</div>
            </div>
            <div>
              <div className="text-ink-faint text-[11px] mb-1">Payout</div>
              <div className="font-medium font-mono">₹{lastResult.adjudication?.payout}</div>
            </div>
            <div>
              <div className="text-ink-faint text-[11px] mb-1">Explanation verified</div>
              <div className="font-medium">{lastResult.workflow_state?.explanation_verified ? 'Yes' : 'No'}</div>
            </div>
          </div>
        )}
      </Card>

      <Card title="Recent runs" icon={Clock} noPadding>
        {loading ? (
          <p className="text-[13px] text-ink-faint p-5">Loading…</p>
        ) : runs.length === 0 ? (
          <div className="p-5"><EmptyState
            title="No runs yet"
            description="Run a claim above, or load the demo dataset from Overview, then come back and rerun."
          /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="text-left text-ink-faint text-[11px] border-b border-line">
                  <th className="py-2 pl-5 pr-4 font-normal">Claim</th>
                  <th className="py-2 pr-4 font-normal">Agent</th>
                  <th className="py-2 pr-4 font-normal">Version</th>
                  <th className="py-2 pr-4 font-normal">Status</th>
                  <th className="py-2 pr-4 font-normal">Scenario</th>
                  <th className="py-2 pr-5 font-normal">ABI version</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {runs.slice(0, 50).map((run) => (
                  <tr key={run.run_id}>
                    <td className="py-2 pl-5 pr-4 font-mono">{run.claim_id}</td>
                    <td className="py-2 pr-4">{run.agent_name}</td>
                    <td className="py-2 pr-4 font-mono">{run.agent_version}</td>
                    <td className="py-2 pr-4"><Badge tone={STATUS_TONE[run.status] || 'slate'}>{run.status}</Badge></td>
                    <td className="py-2 pr-4 font-mono text-ink-faint">{run.scenario_id || '—'}</td>
                    <td className="py-2 pr-5 font-mono text-ink-faint">{run.abi_version || '—'}</td>
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

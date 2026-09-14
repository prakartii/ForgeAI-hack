import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, ScanSearch } from 'lucide-react';
import { fetchFailures, scanForFailures } from '../services/api';
import { ActionButton, Badge, Card, EmptyState, ErrorNote } from '../components/ui';

const TYPE_TONE = {
  FAIRNESS: 'red',
  WORKFLOW: 'amber',
  EVIDENCE: 'sky',
  DECISION_CORRECTNESS: 'slate',
};

export function FailuresPage() {
  const [failures, setFailures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [agentVersion, setAgentVersion] = useState('v1');
  const [scanSummary, setScanSummary] = useState(null);
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setFailures(await fetchFailures());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleScan = async (enforced) => {
    setScanning(true);
    try {
      const summary = await scanForFailures({ agent_version: agentVersion, enforced, claim_sample_size: 60 });
      setScanSummary(summary);
      setError(null);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Failures</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §11–§15: fairness, workflow, evidence, and decision-correctness failure detection
        </p>
      </div>

      <Card title="Run Failure Scan" icon={ScanSearch} tag="POST /api/failures/scan">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs">
            <span className="block text-slate-500 mb-1 font-mono">agent_version</span>
            <select
              value={agentVersion}
              onChange={(e) => setAgentVersion(e.target.value)}
              className="border border-slate-300 rounded px-2 py-1.5 text-xs font-mono"
            >
              <option value="v1">v1 (controlled weaknesses)</option>
              <option value="v2">v2</option>
            </select>
          </label>
          <ActionButton onClick={() => handleScan(false)} loading={scanning} variant="secondary">
            Scan Unprotected
          </ActionButton>
          <ActionButton onClick={() => handleScan(true)} loading={scanning}>
            Scan With Enforcement
          </ActionButton>
        </div>
        <ErrorNote message={error} />
        {scanSummary && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div><div className="text-slate-500 font-mono">fairness</div><div className="font-mono font-bold">{scanSummary.fairness_failures}</div></div>
            <div><div className="text-slate-500 font-mono">workflow</div><div className="font-mono font-bold">{scanSummary.workflow_failures}</div></div>
            <div><div className="text-slate-500 font-mono">evidence</div><div className="font-mono font-bold">{scanSummary.evidence_failures}</div></div>
            <div><div className="text-slate-500 font-mono">decision correctness</div><div className="font-mono font-bold">{scanSummary.decision_correctness_failures}</div></div>
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Detected Failures" icon={AlertTriangle}>
          {loading ? (
            <p className="text-xs text-slate-500">Loading...</p>
          ) : failures.length === 0 ? (
            <EmptyState title="No Failures Detected Yet" description="Run a scan above against the unprotected agent version to reproduce the controlled fairness/workflow bugs." />
          ) : (
            <div className="divide-y divide-slate-100 max-h-[480px] overflow-y-auto">
              {failures.map((f) => (
                <button
                  key={f.failure_id}
                  onClick={() => setSelected(f)}
                  className={`w-full text-left py-3 first:pt-0 hover:bg-slate-50 px-2 -mx-2 rounded ${selected?.failure_id === f.failure_id ? 'bg-slate-50' : ''}`}
                >
                  <div className="flex items-center gap-2">
                    <Badge tone={TYPE_TONE[f.failure_type] || 'slate'}>{f.failure_type}</Badge>
                    <Badge tone={f.severity === 'CRITICAL' ? 'red' : 'amber'}>{f.severity}</Badge>
                    <span className="text-[11px] font-mono text-slate-400">{f.affected_agent}</span>
                  </div>
                  <p className="text-xs text-slate-700 mt-1">{f.description}</p>
                </button>
              ))}
            </div>
          )}
        </Card>

        <Card title="Diagnosis Detail">
          {!selected ? (
            <p className="text-xs text-slate-500">Select a failure to inspect its diagnosis, scenario, and PRISM evidence link.</p>
          ) : (
            <div className="space-y-3 text-xs">
              <div><span className="text-slate-500 font-mono">failure_id: </span><span className="font-mono">{selected.failure_id}</span></div>
              <div><span className="text-slate-500 font-mono">scenario_id: </span><span className="font-mono">{selected.scenario_id || '-'}</span></div>
              <div><span className="text-slate-500 font-mono">prism_session_id: </span><span className="font-mono">{selected.prism_session_id || 'unavailable (PRISM not configured)'}</span></div>
              <div>
                <span className="text-slate-500 font-mono block mb-1">diagnosis:</span>
                <pre className="bg-slate-50 border border-slate-200 rounded p-2 overflow-x-auto text-[11px] font-mono">
                  {JSON.stringify(selected.diagnosis, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

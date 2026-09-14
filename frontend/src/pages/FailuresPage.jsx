import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, ScanSearch, UploadCloud } from 'lucide-react';
import { fetchFailures, fetchPrismStatus, scanForFailures, submitRunToPrism } from '../services/api';
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
  const [prismStatus, setPrismStatus] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [failuresData, prismData] = await Promise.all([
        fetchFailures(),
        fetchPrismStatus().catch(() => null),
      ]);
      setFailures(failuresData);
      setPrismStatus(prismData);
      setError(null);
      setSelected((prev) => (prev ? failuresData.find((f) => f.failure_id === prev.failure_id) || prev : prev));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const prismConfigured = prismStatus?.status === 'configured';

  const handleSubmitToPrism = async (runId) => {
    setSubmitting(true);
    try {
      await submitRunToPrism(runId);
      setError(null);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

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
        <h2 className="text-2xl font-medium text-ink">Failures</h2>
        <p className="text-[13px] text-ink-soft mt-1">Fairness, workflow, evidence, and decision-correctness failures detected from real agent output</p>
      </div>

      <Card title="Run a failure scan" icon={ScanSearch} tag="POST /api/failures/scan">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-[12px]">
            <span className="block text-ink-faint mb-1">Agent version</span>
            <select
              value={agentVersion}
              onChange={(e) => setAgentVersion(e.target.value)}
              className="border border-line-strong rounded px-2.5 py-1.5 text-[13px] bg-paper-panel focus:border-ledger"
            >
              <option value="v1">v1 — controlled weaknesses</option>
              <option value="v2">v2</option>
            </select>
          </label>
          <ActionButton onClick={() => handleScan(false)} loading={scanning} variant="secondary">
            Scan unprotected
          </ActionButton>
          <ActionButton onClick={() => handleScan(true)} loading={scanning}>
            Scan with enforcement
          </ActionButton>
        </div>
        <ErrorNote message={error} />
        {scanSummary && (
          <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-[13px]">
            <div><div className="text-ink-faint text-[11px] mb-1">Fairness</div><div className="font-serif text-xl">{scanSummary.fairness_failures}</div></div>
            <div><div className="text-ink-faint text-[11px] mb-1">Workflow</div><div className="font-serif text-xl">{scanSummary.workflow_failures}</div></div>
            <div><div className="text-ink-faint text-[11px] mb-1">Evidence</div><div className="font-serif text-xl">{scanSummary.evidence_failures}</div></div>
            <div><div className="text-ink-faint text-[11px] mb-1">Decision correctness</div><div className="font-serif text-xl">{scanSummary.decision_correctness_failures}</div></div>
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Detected failures" icon={AlertTriangle} noPadding>
          {loading ? (
            <p className="text-[13px] text-ink-faint p-5">Loading…</p>
          ) : failures.length === 0 ? (
            <div className="p-5">
              <EmptyState title="No failures detected yet" description="Run a scan above against the unprotected agent version to reproduce the controlled fairness and workflow bugs." />
            </div>
          ) : (
            <div className="divide-y divide-line max-h-[480px] overflow-y-auto">
              {failures.map((f) => (
                <button
                  key={f.failure_id}
                  onClick={() => setSelected(f)}
                  className={`w-full text-left px-5 py-3 transition-colors ${selected?.failure_id === f.failure_id ? 'bg-paper-sunk' : 'hover:bg-paper-sunk/60'}`}
                >
                  <div className="flex items-center gap-3">
                    <Badge tone={TYPE_TONE[f.failure_type] || 'slate'}>{f.failure_type.replace(/_/g, ' ').toLowerCase()}</Badge>
                    <Badge tone={f.severity === 'CRITICAL' ? 'red' : 'amber'}>{f.severity.toLowerCase()}</Badge>
                    <span className="text-[11px] font-mono text-ink-faint">{f.affected_agent}</span>
                  </div>
                  <p className="text-[13px] text-ink mt-1.5 leading-snug">{f.description}</p>
                </button>
              ))}
            </div>
          )}
        </Card>

        <Card title="Diagnosis detail">
          {!selected ? (
            <p className="text-[13px] text-ink-faint">Select a failure to inspect its diagnosis, scenario, and PRISM evidence link.</p>
          ) : (
            <div className="space-y-3 text-[13px]">
              <div className="grid grid-cols-[120px_1fr] gap-1 items-center">
                <span className="text-ink-faint">Failure ID</span><span className="font-mono">{selected.failure_id}</span>
                <span className="text-ink-faint">Scenario</span><span className="font-mono">{selected.scenario_id || '—'}</span>
                <span className="text-ink-faint">PRISM session</span>
                {selected.prism_session_id ? (
                  <span className="font-mono text-verdant-700">{selected.prism_session_id}</span>
                ) : !prismConfigured ? (
                  <span className="font-mono text-ink-faint">unavailable — PRISM not configured</span>
                ) : !selected.run_id ? (
                  <span className="font-mono text-ink-faint">unavailable — no execution run recorded for this scan</span>
                ) : (
                  <span className="flex items-center gap-2">
                    <span className="font-mono text-ink-faint">not yet submitted</span>
                    <ActionButton variant="secondary" loading={submitting} onClick={() => handleSubmitToPrism(selected.run_id)}>
                      <UploadCloud className="w-3 h-3" /> Submit to PRISM
                    </ActionButton>
                  </span>
                )}
              </div>
              <div>
                <span className="text-ink-faint block mb-1.5">Diagnosis</span>
                <pre className="bg-paper-sunk border border-line rounded p-3 overflow-x-auto text-[11px] font-mono leading-relaxed">
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

import React, { useEffect, useState } from 'react';
import { Eye, UploadCloud, FileSearch, RefreshCw, ShieldCheck } from 'lucide-react';
import {
  fetchPrismEvidence, fetchPrismStatus, fetchPrismVerdict, fetchRuns,
  reevaluateRunInPrism, submitRunToPrism,
} from '../services/api';
import { ActionButton, Badge, Card, ErrorNote } from '../components/ui';

export function PrismEvidencePage() {
  const [prismStatus, setPrismStatus] = useState(null);
  const [verdict, setVerdict] = useState(null);
  const [runs, setRuns] = useState([]);
  const [busyRunId, setBusyRunId] = useState(null);
  const [evidenceByRun, setEvidenceByRun] = useState({});
  const [error, setError] = useState(null);

  const load = () => {
    fetchPrismStatus().then(setPrismStatus).catch(() => null);
    fetchPrismVerdict().then(setVerdict).catch(() => null);
    fetchRuns().then(setRuns).catch(() => null);
  };

  useEffect(load, []);

  const configured = prismStatus?.status === 'configured';

  const handleSubmit = async (runId) => {
    setBusyRunId(runId);
    try {
      await submitRunToPrism(runId);
      setError(null);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyRunId(null);
    }
  };

  const handleFetchEvidence = async (runId) => {
    setBusyRunId(runId);
    try {
      const evidence = await fetchPrismEvidence(runId);
      setEvidenceByRun((prev) => ({ ...prev, [runId]: evidence }));
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyRunId(null);
    }
  };

  const handleReevaluate = async (runId) => {
    setBusyRunId(runId);
    try {
      await reevaluateRunInPrism(runId);
      // PRISM evaluates asynchronously (returns {"status": "evaluating"}
      // immediately) -- give it a moment, then pull the refreshed score.
      await new Promise((resolve) => setTimeout(resolve, 4000));
      const evidence = await fetchPrismEvidence(runId);
      setEvidenceByRun((prev) => ({ ...prev, [runId]: evidence }));
      setError(null);
      fetchPrismVerdict().then(setVerdict).catch(() => null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyRunId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-medium text-ink">PRISM evidence</h2>
        <p className="text-[13px] text-ink-soft mt-1">Backing traces, evaluator scores, and diagnostic proofs from PRISM</p>
      </div>

      <Card title="Integration status" icon={Eye}>
        <div className="flex items-center justify-between border-b border-line pb-4 mb-4">
          <div>
            <p className="text-[12px] text-ink-faint font-mono">{prismStatus?.base_url || 'https://prism.blockconvey.com'}</p>
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

      {configured && verdict?.total_on_prism != null && (
        <Card title="PRISM's own governance verdict" icon={ShieldCheck} tag="GET /api/prism/verdict">
          <p className="text-[13px] text-ink-soft mb-4">
            Real, PRISM-computed scores across our submitted trajectories — not our own scoring. This is the same
            figure the Release Gate's <code className="font-mono text-[12px]">prism_evidence</code> clause now
            actually checks, not just whether PRISM is reachable.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-[11px] text-ink-faint uppercase tracking-wide">Submitted to PRISM</p>
              <p className="text-xl font-mono mt-1">{verdict.total_on_prism}</p>
            </div>
            <div>
              <p className="text-[11px] text-ink-faint uppercase tracking-wide">Sampled &amp; evaluated</p>
              <p className="text-xl font-mono mt-1">{verdict.evaluated_count} / {verdict.sample_size}</p>
            </div>
            <div>
              <p className="text-[11px] text-ink-faint uppercase tracking-wide">Critical rule failures</p>
              <p className={`text-xl font-mono mt-1 ${verdict.critical_failures > 0 ? 'text-rose-700' : 'text-emerald-700'}`}>
                {verdict.critical_failures}
              </p>
            </div>
            <div>
              <p className="text-[11px] text-ink-faint uppercase tracking-wide">Avg overall_score</p>
              <p className="text-xl font-mono mt-1">{verdict.avg_overall_score ?? '—'}</p>
            </div>
          </div>
        </Card>
      )}

      <Card title="Run to PRISM session correlation" tag="agent_runs.prism_session_id" noPadding>
        <p className="text-[13px] text-ink-soft p-5 pb-0">
          Every agent run can be submitted to PRISM as a trajectory, which returns a real{' '}
          <code className="font-mono text-[12px]">prism_session_id</code>.{' '}
          {configured
            ? 'Runs made from the Agent Runs page submit automatically; older or bulk-computed runs (metrics, hardening, regression) are never auto-submitted to stay within PRISM\'s trace budget — submit one manually below, or fetch its evaluator result.'
            : 'With no PRISM credentials configured here, this stays honestly empty rather than a placeholder score.'}
        </p>
        <ErrorNote message={error} />
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left text-ink-faint text-[11px] border-b border-line">
                <th className="py-2 pl-5 pr-4 font-normal">Run ID</th>
                <th className="py-2 pr-4 font-normal">Claim</th>
                <th className="py-2 pr-4 font-normal">Agent</th>
                <th className="py-2 pr-4 font-normal">PRISM session</th>
                <th className="py-2 pr-5 font-normal">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {runs.slice(0, 15).map((run) => (
                <React.Fragment key={run.run_id}>
                  <tr>
                    <td className="py-2 pl-5 pr-4 font-mono">{run.run_id}</td>
                    <td className="py-2 pr-4 font-mono">{run.claim_id}</td>
                    <td className="py-2 pr-4">{run.agent_name}</td>
                    <td className="py-2 pr-4 font-mono text-ink-faint">
                      {run.prism_session_id || 'unavailable'}
                    </td>
                    <td className="py-2 pr-5">
                      {configured && (
                        <div className="flex gap-2">
                          <ActionButton variant="secondary" loading={busyRunId === run.run_id} onClick={() => handleSubmit(run.run_id)}>
                            <UploadCloud className="w-3 h-3" /> Submit
                          </ActionButton>
                          {run.prism_session_id && (
                            <>
                              <ActionButton variant="secondary" loading={busyRunId === run.run_id} onClick={() => handleFetchEvidence(run.run_id)}>
                                <FileSearch className="w-3 h-3" /> Fetch evidence
                              </ActionButton>
                              <ActionButton variant="secondary" loading={busyRunId === run.run_id} onClick={() => handleReevaluate(run.run_id)}>
                                <RefreshCw className="w-3 h-3" /> Re-evaluate
                              </ActionButton>
                            </>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                  {evidenceByRun[run.run_id] && (
                    <tr>
                      <td colSpan={5} className="pb-3 pl-5 pr-5">
                        <pre className="bg-paper-sunk border border-line rounded p-3 overflow-x-auto text-[11px] font-mono leading-relaxed">
                          {JSON.stringify(evidenceByRun[run.run_id], null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
              {runs.length === 0 && (
                <tr><td colSpan={5} className="py-6 text-center text-ink-faint">No runs yet — execute a claim from Agent Runs.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

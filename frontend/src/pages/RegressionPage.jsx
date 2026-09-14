import React, { useCallback, useEffect, useState } from 'react';
import { History, PlayCircle } from 'lucide-react';
import { fetchRegressions, runRegressions } from '../services/api';
import { ActionButton, Badge, Card, EmptyState, ErrorNote } from '../components/ui';

export function RegressionPage() {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [candidateVersion, setCandidateVersion] = useState('v2');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setTests(await fetchRegressions());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleRun = async () => {
    setRunning(true);
    try {
      await runRegressions({ candidate_version: candidateVersion });
      setError(null);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  const passCount = tests.filter((t) => t.still_passing).length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Regression Suite</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §19: every discovered failure becomes a permanent regression test — it must never silently disappear
        </p>
      </div>

      <Card title="Rerun Suite Against a Candidate Version" icon={PlayCircle} tag="POST /api/regressions/run">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs">
            <span className="block text-slate-500 mb-1 font-mono">candidate_version</span>
            <select value={candidateVersion} onChange={(e) => setCandidateVersion(e.target.value)} className="border border-slate-300 rounded px-2 py-1.5 text-xs font-mono">
              <option value="v1">v1</option>
              <option value="v2">v2</option>
            </select>
          </label>
          <ActionButton onClick={handleRun} loading={running}>Run Regression Suite</ActionButton>
          {tests.length > 0 && (
            <span className="text-xs font-mono text-slate-500">
              {passCount}/{tests.length} passing
            </span>
          )}
        </div>
        <ErrorNote message={error} />
      </Card>

      <Card title="Registered Regression Tests" icon={History}>
        {loading ? (
          <p className="text-xs text-slate-500">Loading...</p>
        ) : tests.length === 0 ? (
          <EmptyState
            title="No Regression Tests Registered Yet"
            description="Run a failure scan on the Failures page first — every detected failure registers here automatically when compiled into an ABI."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-500 font-mono uppercase text-[10px] border-b border-slate-200">
                  <th className="py-2 pr-4">Test ID</th>
                  <th className="py-2 pr-4">Failure Type</th>
                  <th className="py-2 pr-4">Expected Behavior</th>
                  <th className="py-2 pr-4">ABI Introduced</th>
                  <th className="py-2 pr-4">Last Tested</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tests.map((t) => (
                  <tr key={t.test_id}>
                    <td className="py-2 pr-4 font-mono">{t.test_id}</td>
                    <td className="py-2 pr-4"><Badge>{t.failure_type}</Badge></td>
                    <td className="py-2 pr-4 text-slate-600 max-w-xs truncate" title={t.expected_behavior}>{t.expected_behavior}</td>
                    <td className="py-2 pr-4 font-mono text-slate-500">{t.abi_version_introduced}</td>
                    <td className="py-2 pr-4 font-mono text-slate-500">{t.last_tested_version || '—'}</td>
                    <td className="py-2 pr-4">
                      <Badge tone={t.still_passing ? 'emerald' : 'red'}>{t.still_passing ? 'PASSING' : 'FAILING'}</Badge>
                    </td>
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

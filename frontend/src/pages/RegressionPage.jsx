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
        <h2 className="text-2xl font-medium text-ink">Regression suite</h2>
        <p className="text-[13px] text-ink-soft mt-1">Every discovered failure becomes a permanent test — it must never silently disappear</p>
      </div>

      <Card title="Rerun the suite against a candidate version" icon={PlayCircle} tag="POST /api/regressions/run">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-[12px]">
            <span className="block text-ink-faint mb-1">Candidate version</span>
            <select value={candidateVersion} onChange={(e) => setCandidateVersion(e.target.value)} className="border border-line-strong rounded px-2.5 py-1.5 text-[13px] bg-paper-panel focus:border-ledger">
              <option value="v1">v1</option>
              <option value="v2">v2</option>
            </select>
          </label>
          <ActionButton onClick={handleRun} loading={running}>Run regression suite</ActionButton>
          {tests.length > 0 && (
            <span className="text-[13px] text-ink-soft">
              {passCount}/{tests.length} passing
            </span>
          )}
        </div>
        <ErrorNote message={error} />
      </Card>

      <Card title="Registered regression tests" icon={History} noPadding>
        {loading ? (
          <p className="text-[13px] text-ink-faint p-5">Loading…</p>
        ) : tests.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="No regression tests registered yet"
              description="Run a failure scan on the Failures page first — every detected failure registers here automatically."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="text-left text-ink-faint text-[11px] border-b border-line">
                  <th className="py-2 pl-5 pr-4 font-normal">Test ID</th>
                  <th className="py-2 pr-4 font-normal">Failure type</th>
                  <th className="py-2 pr-4 font-normal">Expected behavior</th>
                  <th className="py-2 pr-4 font-normal">ABI introduced</th>
                  <th className="py-2 pr-4 font-normal">Last tested</th>
                  <th className="py-2 pr-5 font-normal">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {tests.map((t) => (
                  <tr key={t.test_id}>
                    <td className="py-2 pl-5 pr-4 font-mono">{t.test_id}</td>
                    <td className="py-2 pr-4"><Badge>{t.failure_type.replace(/_/g, ' ').toLowerCase()}</Badge></td>
                    <td className="py-2 pr-4 text-ink-soft max-w-xs truncate" title={t.expected_behavior}>{t.expected_behavior}</td>
                    <td className="py-2 pr-4 font-mono text-ink-faint">{t.abi_version_introduced}</td>
                    <td className="py-2 pr-4 font-mono text-ink-faint">{t.last_tested_version || '—'}</td>
                    <td className="py-2 pr-5">
                      <Badge tone={t.still_passing ? 'emerald' : 'red'}>{t.still_passing ? 'Passing' : 'Failing'}</Badge>
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

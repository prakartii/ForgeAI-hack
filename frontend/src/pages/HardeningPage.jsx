import React, { useEffect, useState } from 'react';
import { ShieldAlert, TrendingUp } from 'lucide-react';
import { fetchHardeningLadders, fetchHardeningResults } from '../services/api';
import { ActionButton, Card, ErrorNote, MetricTile } from '../components/ui';

function pct(v) {
  return v === null || v === undefined ? '—' : `${Math.round(v * 100)}%`;
}

export function HardeningPage() {
  const [ladders, setLadders] = useState([]);
  const [agentVersion, setAgentVersion] = useState('v1');
  const [enforced, setEnforced] = useState(false);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHardeningLadders().then(setLadders).catch(() => null);
  }, []);

  const run = async () => {
    setLoading(true);
    try {
      setResults(await fetchHardeningResults({ agent_version: agentVersion, enforced }));
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
        <h2 className="text-2xl font-medium text-ink">Hardening ladders</h2>
        <p className="text-[13px] text-ink-soft mt-1">Adversarial difficulty ladders proving a fix generalizes, not just one reproduced example</p>
      </div>

      <Card title="Run the fairness hardening ladder" icon={TrendingUp} tag="GET /api/hardening/results">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-[12px]">
            <span className="block text-ink-faint mb-1">Agent version</span>
            <select value={agentVersion} onChange={(e) => setAgentVersion(e.target.value)} className="border border-line-strong rounded px-2.5 py-1.5 text-[13px] bg-paper-panel focus:border-ledger">
              <option value="v1">v1</option>
              <option value="v2">v2</option>
            </select>
          </label>
          <label className="text-[12px] flex items-center gap-1.5 pb-1.5">
            <input type="checkbox" checked={enforced} onChange={(e) => setEnforced(e.target.checked)} />
            <span className="text-ink-soft">Enforce compiled fairness ABI</span>
          </label>
          <ActionButton onClick={run} loading={loading}>Run ladder — 25 groups × 4 levels</ActionButton>
        </div>
        <ErrorNote message={error} />

        {results && (
          <div className="mt-5 grid grid-cols-2 md:grid-cols-5 gap-4">
            <MetricTile
              label="Challenge robustness"
              value={pct(results.challenge_robustness)}
              tone={results.challenge_robustness === 1 ? 'verdant' : 'seal'}
            />
            {['L1', 'L2', 'L3', 'L4'].map((level) => (
              <MetricTile
                key={level}
                label={level}
                value={pct(results.per_level[level]?.pass_rate)}
                sub={`${results.per_level[level]?.passed}/${results.per_level[level]?.total} groups`}
                tone={results.per_level[level]?.pass_rate === 1 ? 'verdant' : 'seal'}
              />
            ))}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {ladders.map((ladder, idx) => (
          <Card key={idx} icon={ShieldAlert} title={`${ladder.track.toLowerCase()} challenge track`}>
            {ladder.levels && (
              <div className="space-y-2.5">
                {ladder.levels.map((lvl) => (
                  <div key={lvl.level} className="flex items-center justify-between text-[13px] py-1">
                    <span className="text-ink-faint">Level {lvl.level}</span>
                    <span className="text-ink">{lvl.description}</span>
                  </div>
                ))}
              </div>
            )}
            {ladder.challenges && (
              <div className="space-y-2">
                {ladder.challenges.map((challenge, cIdx) => (
                  <div key={cIdx} className="text-[13px] text-ink py-1">
                    {challenge}
                  </div>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}

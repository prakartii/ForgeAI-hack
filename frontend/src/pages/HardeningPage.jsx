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
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Hardening Ladders</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §18: adversarial difficulty ladders proving a fix generalizes, not just one reproduced example
        </p>
      </div>

      <Card title="Run Fairness Hardening Ladder" icon={TrendingUp} tag="GET /api/hardening/results">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs">
            <span className="block text-slate-500 mb-1 font-mono">agent_version</span>
            <select value={agentVersion} onChange={(e) => setAgentVersion(e.target.value)} className="border border-slate-300 rounded px-2 py-1.5 text-xs font-mono">
              <option value="v1">v1</option>
              <option value="v2">v2</option>
            </select>
          </label>
          <label className="text-xs flex items-center gap-1.5 pb-1.5">
            <input type="checkbox" checked={enforced} onChange={(e) => setEnforced(e.target.checked)} />
            <span className="text-slate-600">enforce compiled fairness ABI</span>
          </label>
          <ActionButton onClick={run} loading={loading}>Run Ladder (25 groups × 4 levels)</ActionButton>
        </div>
        <ErrorNote message={error} />

        {results && (
          <div className="mt-5">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
              <MetricTile
                label="Challenge Robustness"
                value={pct(results.challenge_robustness)}
                tone={results.challenge_robustness === 1 ? 'emerald' : 'red'}
              />
              {['L1', 'L2', 'L3', 'L4'].map((level) => (
                <MetricTile
                  key={level}
                  label={level}
                  value={pct(results.per_level[level]?.pass_rate)}
                  sub={`${results.per_level[level]?.passed}/${results.per_level[level]?.total} groups`}
                  tone={results.per_level[level]?.pass_rate === 1 ? 'emerald' : 'red'}
                />
              ))}
            </div>
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {ladders.map((ladder, idx) => (
          <Card key={idx} icon={ShieldAlert} title={`${ladder.track} Challenge Track`}>
            {ladder.levels && (
              <div className="space-y-3">
                {ladder.levels.map((lvl) => (
                  <div key={lvl.level} className="p-3 bg-slate-50 rounded border border-slate-200 flex items-center justify-between text-xs">
                    <span className="font-mono font-bold text-slate-700">Level {lvl.level}</span>
                    <span className="text-slate-600 font-medium">{lvl.description}</span>
                  </div>
                ))}
              </div>
            )}
            {ladder.challenges && (
              <div className="space-y-2">
                {ladder.challenges.map((challenge, cIdx) => (
                  <div key={cIdx} className="p-2.5 bg-slate-50 rounded border border-slate-200 text-xs text-slate-700 font-mono">
                    • {challenge}
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

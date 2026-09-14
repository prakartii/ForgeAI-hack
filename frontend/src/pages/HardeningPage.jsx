import React, { useState, useEffect } from 'react';
import { ShieldAlert, TrendingUp } from 'lucide-react';
import { fetchHardeningLadders } from '../services/api';

export function HardeningPage() {
  const [ladders, setLadders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHardeningLadders().then(setLadders).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Hardening Ladders</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §18: Adversarial difficulty ladders testing generalization beyond the original diagnosed failure
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {ladders.map((ladder, idx) => (
          <div key={idx} className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4">
              <ShieldAlert className="w-5 h-5 text-amber-600" />
              <h3 className="text-sm font-bold text-slate-900 font-mono">{ladder.track} Challenge Track</h3>
            </div>

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
          </div>
        ))}
      </div>
    </div>
  );
}

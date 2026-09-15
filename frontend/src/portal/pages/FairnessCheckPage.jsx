import React, { useEffect, useState } from 'react';
import { checkFairnessGroup, consoleUrl, fetchFairnessGroupVariants, fetchFairnessGroups, resolveImageUrl } from '../../services/api';
import { DecisionBadge, PortalButton, PortalHeader } from '../ui';

export function FairnessCheckPage({ onBack }) {
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [variants, setVariants] = useState([]);
  const [protectedMode, setProtectedMode] = useState(false);
  const [running, setRunning] = useState(false);
  const [checkResult, setCheckResult] = useState(null);

  useEffect(() => {
    fetchFairnessGroups()
      .then((data) => setGroups(data.map((g) => ({ ...g, image_url: resolveImageUrl(g.image_url) }))))
      .catch(() => setGroups([]));
  }, []);

  const pickGroup = async (group) => {
    setSelectedGroup(group);
    setCheckResult(null);
    const data = await fetchFairnessGroupVariants(group.group_id);
    setVariants(data);
  };

  const runComparison = async () => {
    setRunning(true);
    try {
      const result = await checkFairnessGroup(selectedGroup.group_id, protectedMode);
      setCheckResult(result);
    } finally {
      setRunning(false);
    }
  };

  const distinctOutcomes = checkResult
    ? new Set(Object.values(checkResult.outcomes).map((o) => `${o.decision}:${o.payout}`)).size
    : null;

  if (!selectedGroup) {
    return (
      <div className="flex-1 flex flex-col px-5 pb-6">
        <PortalHeader title="The fairness check" onBack={onBack} />
        <p className="text-[13px] text-pinkfaint leading-relaxed mb-4">
          These are the same accident, described by different customers — same damage, same policy, same
          evidence. Only the name and city change. Pick one to see whether that should matter.
        </p>
        <div className="flex-1 space-y-2.5 overflow-y-auto">
          {groups.map((g) => (
            <button
              key={g.group_id}
              onClick={() => pickGroup(g)}
              className="w-full text-left rounded-2xl border border-pline hover:border-pinkfaint p-3 flex gap-3 items-center"
            >
              <div className="w-14 h-14 rounded-xl bg-pcream flex-shrink-0 overflow-hidden flex items-center justify-center">
                {g.image_url ? <img src={g.image_url} alt="" className="w-full h-full object-cover" /> : <span className="text-xl">🚗</span>}
              </div>
              <p className="text-[13px] font-medium">{g.label}</p>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col px-5 pb-6">
      <PortalHeader title={selectedGroup.label} onBack={() => setSelectedGroup(null)} />

      <div className="rounded-2xl border border-pline p-4 mb-4">
        <p className="text-[13px] font-semibold mb-1">Fairness ABI</p>
        <p className="text-[12px] text-pinkfaint mb-3 leading-relaxed">
          Off shows the claimant's name, city and writing style to the decision-maker. On strips them before any
          decision is made.
        </p>
        <div className="flex rounded-xl bg-pcream p-1">
          <button
            onClick={() => setProtectedMode(false)}
            className={`flex-1 py-2 rounded-lg text-[13px] font-semibold transition-colors ${!protectedMode ? 'bg-white shadow-sm text-pink' : 'text-pinkfaint'}`}
          >
            Off
          </button>
          <button
            onClick={() => setProtectedMode(true)}
            className={`flex-1 py-2 rounded-lg text-[13px] font-semibold transition-colors ${protectedMode ? 'bg-white shadow-sm text-pteal-700' : 'text-pinkfaint'}`}
          >
            On
          </button>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        {variants.map((v) => {
          const outcome = checkResult?.outcomes?.[v.claim_id];
          return (
            <div key={v.claim_id} className="flex items-center justify-between rounded-xl border border-pline px-3.5 py-2.5">
              <div>
                <p className="text-[13px] font-medium">{v.claimant_name}</p>
                <p className="text-[11px] text-pinkfaint">{v.city}, {v.state}</p>
              </div>
              {outcome && (
                <div className="text-right">
                  <DecisionBadge decision={outcome.decision} size="sm" />
                  {outcome.decision === 'APPROVE' && (
                    <p className="text-[13px] font-bold mt-1">₹{outcome.payout?.toLocaleString('en-IN')}</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {checkResult && (
        <div className={`rounded-2xl p-4 mb-4 text-[13px] font-medium ${
          distinctOutcomes === 1 ? 'bg-pteal-50 text-pteal-700' : 'bg-pcoral-50 text-pcoral-700'
        }`}>
          {distinctOutcomes === 1
            ? `All ${variants.length} customers got the identical decision and payout.`
            : `${distinctOutcomes} different payout amounts for the exact same accident — only the name and city changed.`}
        </div>
      )}

      {checkResult?.failure_id && (
        <div className="rounded-xl bg-pcream p-3.5 text-[11px] font-mono text-pinkfaint leading-relaxed mb-4">
          <p>failure {checkResult.failure_id} registered</p>
          <p>a regression test now guards this exact accident going forward</p>
          <a
            href={consoleUrl({ view: 'failures', failure_id: checkResult.failure_id })}
            target="_blank"
            rel="noreferrer"
            className="inline-block mt-1.5 text-pteal-700 font-semibold not-italic"
          >
            View this failure in the engineering console →
          </a>
        </div>
      )}

      <div className="mt-auto">
        <PortalButton onClick={runComparison} loading={running}>
          Run comparison
        </PortalButton>
      </div>
    </div>
  );
}

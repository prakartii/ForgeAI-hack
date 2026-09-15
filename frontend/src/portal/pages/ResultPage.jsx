import React, { useEffect, useState } from 'react';
import { DecisionBadge, PortalButton, PortalHeader, StatusTimeline } from '../ui';

export function ResultPage({ result, onRestart, onOpenFairnessCheck }) {
  const [revealed, setRevealed] = useState(0);
  const [showDecision, setShowDecision] = useState(false);
  const totalSteps = 5;

  useEffect(() => {
    setRevealed(0);
    setShowDecision(false);
    let step = 0;
    const interval = setInterval(() => {
      step += 1;
      setRevealed(step);
      if (step >= totalSteps) {
        clearInterval(interval);
        setTimeout(() => setShowDecision(true), 300);
      }
    }, 380);
    return () => clearInterval(interval);
  }, [result]);

  const blocked = result.status === 'BLOCKED_CUSTOMER_COMMUNICATION';

  return (
    <div className="flex-1 flex flex-col px-5 pb-6">
      <PortalHeader title="Your claim" />

      <div className="pt-2 pb-6">
        <StatusTimeline steps={result.steps_completed} revealed={revealed} />
      </div>

      {showDecision && (
        <div className="flex-1 space-y-5 animate-[fadeIn_0.4s_ease-in]">
          {blocked ? (
            <div className="rounded-2xl border border-pamber-100 bg-pamber-50 p-4">
              <p className="text-[14px] font-semibold text-pamber-700">Your explanation is still being verified</p>
              <p className="text-[13px] text-pinkfaint mt-1 leading-relaxed">
                We caught an issue with the evidence behind this decision and paused before contacting you — a
                human reviewer will follow up.
              </p>
            </div>
          ) : (
            <>
              <div className="text-center py-2">
                <DecisionBadge decision={result.decision} />
                {result.decision === 'APPROVE' && (
                  <p className="text-3xl font-extrabold mt-4">₹{result.payout_inr?.toLocaleString('en-IN')}</p>
                )}
              </div>

              {result.explanation && (
                <div className="rounded-2xl border border-pline p-4">
                  <p className="text-[11px] font-semibold text-pinkfaint uppercase tracking-wide mb-1.5">Why</p>
                  <p className="text-[14px] leading-relaxed">{result.explanation}</p>
                </div>
              )}
            </>
          )}

          <div className="pt-2 space-y-3">
            <PortalButton variant="secondary" onClick={onRestart}>
              File another claim
            </PortalButton>
            <PortalButton variant="ghost" onClick={onOpenFairnessCheck}>
              See how this could go differently →
            </PortalButton>
          </div>
        </div>
      )}
    </div>
  );
}

import React from 'react';
import { Loader2 } from 'lucide-react';

export function PortalShell({ children }) {
  return (
    <div className="min-h-screen bg-pcream font-portal text-pink">
      <div className="max-w-md mx-auto min-h-screen bg-white shadow-[0_0_40px_rgba(0,0,0,0.04)] flex flex-col">
        {children}
        <div className="px-5 py-4 text-center">
          <a href="/" className="text-[11px] text-pinkfaint hover:text-pinkfaint/70 transition-colors">
            Engineering console →
          </a>
        </div>
      </div>
    </div>
  );
}

export function PortalHeader({ title, onBack }) {
  return (
    <header className="px-5 pt-6 pb-4 flex items-center gap-3">
      {onBack && (
        <button onClick={onBack} className="text-pinkfaint hover:text-pink text-sm -ml-1 px-1" aria-label="Back">
          ←
        </button>
      )}
      <div className="flex-1">
        <p className="text-[11px] tracking-wide text-pteal font-semibold">FairClaim</p>
        <h1 className="font-portal text-xl font-bold leading-tight">{title}</h1>
      </div>
    </header>
  );
}

export function PortalButton({ children, onClick, variant = 'primary', loading, disabled, fullWidth = true, className = '' }) {
  const variants = {
    primary: 'bg-pteal text-white hover:bg-pteal-700 active:bg-pteal-700',
    secondary: 'bg-pcream text-pink border border-pline hover:border-pinkfaint',
    ghost: 'bg-transparent text-pteal hover:bg-pteal-50',
  };
  return (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      className={`${fullWidth ? 'w-full' : ''} inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-[15px] font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${className}`}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
}

export function ClaimCard({ claim, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-2xl border p-3 flex gap-3 items-center transition-colors ${
        selected ? 'border-pteal bg-pteal-50' : 'border-pline hover:border-pinkfaint'
      }`}
    >
      <div className="w-16 h-16 rounded-xl bg-pcream flex-shrink-0 overflow-hidden flex items-center justify-center">
        {claim.image_url ? (
          <img src={claim.image_url} alt="" className="w-full h-full object-cover" />
        ) : (
          <span className="text-2xl">🚗</span>
        )}
      </div>
      <div className="min-w-0">
        <p className="font-semibold text-[14px] truncate">{claim.vehicle_make} {claim.vehicle_model}</p>
        <p className="text-[12px] text-pinkfaint truncate">{claim.damage_part?.replace(/_/g, ' ').toLowerCase()} · {claim.peril?.toLowerCase()}</p>
      </div>
    </button>
  );
}

const DECISION_STYLE = {
  APPROVE: { label: 'Approved', bg: 'bg-pteal-50', text: 'text-pteal-700', icon: '✓' },
  DENY: { label: 'Denied', bg: 'bg-pcoral-50', text: 'text-pcoral-700', icon: '✕' },
  ESCALATE: { label: 'Under review', bg: 'bg-pamber-50', text: 'text-pamber-700', icon: '…' },
};

export function DecisionBadge({ decision, size = 'lg' }) {
  const style = DECISION_STYLE[decision] || DECISION_STYLE.ESCALATE;
  const sizeClasses = size === 'lg' ? 'text-2xl px-5 py-3' : 'text-sm px-3 py-1.5';
  return (
    <div className={`inline-flex items-center gap-2 rounded-2xl font-bold ${style.bg} ${style.text} ${sizeClasses}`}>
      <span>{style.icon}</span>
      {style.label}
    </div>
  );
}

const STEP_LABELS = {
  submitted: 'Claim submitted',
  reviewed: 'Reviewed by intake',
  decided: 'Decision made',
  explained: 'Explanation verified',
  communicated: 'Sent to you',
};

export function StatusTimeline({ steps, revealed }) {
  const allSteps = ['submitted', 'reviewed', 'decided', 'explained', 'communicated'];
  return (
    <div className="space-y-0">
      {allSteps.map((step, idx) => {
        const done = steps.includes(step) && idx < revealed;
        const isLast = idx === allSteps.length - 1;
        const skipped = !steps.includes(step);
        return (
          <div key={step} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className={`w-2.5 h-2.5 rounded-full mt-1.5 transition-colors duration-300 ${
                skipped ? 'bg-pline' : done ? 'bg-pteal' : 'bg-pline'
              }`} />
              {!isLast && <div className={`w-px flex-1 min-h-[20px] transition-colors duration-300 ${done && !skipped ? 'bg-pteal' : 'bg-pline'}`} />}
            </div>
            <p className={`text-[13px] pb-4 transition-colors duration-300 ${
              skipped ? 'text-pline' : done ? 'text-pink font-medium' : 'text-pinkfaint'
            }`}>
              {STEP_LABELS[step]}
            </p>
          </div>
        );
      })}
    </div>
  );
}

import React from 'react';
import { Loader2 } from 'lucide-react';

const ACCENT_COLOR = {
  ledger: 'bg-ledger',
  seal: 'bg-seal',
  verdant: 'bg-verdant',
  brass: 'bg-brass',
  none: 'bg-transparent',
};

export function Card({ title, icon: Icon, tag, children, className = '', noPadding = false, accent = 'none' }) {
  return (
    <div className={`relative bg-paper-panel rounded-md border border-line overflow-hidden flex ${className}`}>
      <div className={`w-[3px] flex-shrink-0 ${ACCENT_COLOR[accent]}`} aria-hidden="true" />
      <div className="flex-1 min-w-0">
        {(title || tag) && (
          <div className="pl-4 pr-4 py-3 border-b border-line flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 min-w-0">
              {Icon && <Icon className="w-4 h-4 text-ink-soft flex-shrink-0" />}
              {title && <h3 className="text-[13px] font-semibold text-ink truncate">{title}</h3>}
            </div>
            {tag && (
              <span className="text-[11px] font-mono text-ink-faint whitespace-nowrap">{tag}</span>
            )}
          </div>
        )}
        <div className={noPadding ? '' : 'p-5'}>{children}</div>
      </div>
    </div>
  );
}

export function MetricTile({ label, value, sub, tone = 'ink', icon: Icon }) {
  const toneClasses = {
    ink: 'text-ink',
    verdant: 'text-verdant-700',
    seal: 'text-seal-700',
    brass: 'text-brass-700',
  };
  return (
    <div className="bg-paper-panel p-4 rounded-md border border-line">
      <div className="flex items-center justify-between text-ink-faint mb-2">
        <span className="text-[12px] font-medium">{label}</span>
        {Icon && <Icon className="w-3.5 h-3.5" />}
      </div>
      <div className={`text-2xl font-serif font-medium ${toneClasses[tone] || toneClasses.ink}`}>{value}</div>
      {sub && <p className="text-[11px] text-ink-faint mt-1.5">{sub}</p>}
    </div>
  );
}

const DOT_TONE = {
  slate: 'bg-ink-faint',
  emerald: 'bg-verdant',
  red: 'bg-seal',
  amber: 'bg-brass',
  sky: 'bg-ledger',
};
const TEXT_TONE = {
  slate: 'text-ink-soft',
  emerald: 'text-verdant-700',
  red: 'text-seal-700',
  amber: 'text-brass-700',
  sky: 'text-ledger-700',
};

export function Badge({ children, tone = 'slate' }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${TEXT_TONE[tone] || TEXT_TONE.slate}`}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${DOT_TONE[tone] || DOT_TONE.slate}`} />
      {children}
    </span>
  );
}

export function ActionButton({ children, onClick, loading, variant = 'primary', disabled }) {
  const variants = {
    primary: 'bg-ledger text-white hover:bg-ledger-700',
    secondary: 'bg-transparent text-ink border border-line-strong hover:border-ink-soft hover:bg-paper-sunk',
    danger: 'bg-seal text-white hover:bg-seal-700',
  };
  return (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded text-[13px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant] || variants.primary}`}
    >
      {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
      {children}
    </button>
  );
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="text-center py-10">
      <p className="text-[13px] font-medium text-ink">{title}</p>
      {description && <p className="text-[12px] text-ink-faint mt-1 max-w-md mx-auto leading-relaxed">{description}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}

export function ErrorNote({ message }) {
  if (!message) return null;
  return (
    <div className="text-[12px] text-seal-700 bg-seal-50 border border-seal-100 rounded px-3 py-2 mt-3">
      {message}
    </div>
  );
}

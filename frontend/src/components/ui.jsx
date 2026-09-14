import React from 'react';
import { Loader2 } from 'lucide-react';

export function Card({ title, icon: Icon, tag, children, className = '', noPadding = false }) {
  return (
    <div className={`bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden ${className}`}>
      {(title || tag) && (
        <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {Icon && <Icon className="w-4 h-4 text-slate-600" />}
            {title && <h3 className="text-sm font-semibold text-slate-900">{title}</h3>}
          </div>
          {tag && (
            <span className="text-[11px] font-mono bg-slate-200/70 text-slate-700 px-2 py-0.5 rounded">{tag}</span>
          )}
        </div>
      )}
      <div className={noPadding ? '' : 'p-5'}>{children}</div>
    </div>
  );
}

export function MetricTile({ label, value, sub, tone = 'slate', icon: Icon }) {
  const toneClasses = {
    slate: 'text-slate-900',
    emerald: 'text-emerald-700',
    red: 'text-red-700',
    amber: 'text-amber-700',
  };
  return (
    <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between text-slate-500 mb-2">
        <span className="text-xs font-mono font-semibold uppercase tracking-wider">{label}</span>
        {Icon && <Icon className="w-4 h-4 text-slate-400" />}
      </div>
      <div className={`text-xl font-bold font-mono ${toneClasses[tone] || toneClasses.slate}`}>{value}</div>
      {sub && <p className="text-[11px] text-slate-500 mt-2">{sub}</p>}
    </div>
  );
}

export function Badge({ children, tone = 'slate' }) {
  const toneClasses = {
    slate: 'bg-slate-100 text-slate-700 border-slate-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    sky: 'bg-sky-50 text-sky-700 border-sky-200',
  };
  return (
    <span className={`inline-flex items-center text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border ${toneClasses[tone] || toneClasses.slate}`}>
      {children}
    </span>
  );
}

export function ActionButton({ children, onClick, loading, variant = 'primary', disabled }) {
  const variants = {
    primary: 'bg-slate-900 text-white hover:bg-slate-800',
    secondary: 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  };
  return (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant] || variants.primary}`}
    >
      {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
      {children}
    </button>
  );
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="text-center py-10">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      {description && <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">{description}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}

export function ErrorNote({ message }) {
  if (!message) return null;
  return (
    <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2 mt-3">
      {message}
    </div>
  );
}

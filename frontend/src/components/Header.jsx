import React from 'react';
import { HealthBadge } from './HealthBadge';

export function Header({ health, loading, error, onRefresh }) {
  return (
    <header className="h-16 bg-paper-panel border-b border-line px-6 flex items-center justify-between gap-6">
      <p className="hidden lg:block text-[13px] text-ink-soft font-serif italic leading-snug max-w-2xl truncate">
        "PRISM finds and explains the failure. FailureFoundry turns that diagnosis into an executable behavioral contract that prevents recurrence."
      </p>

      <div className="flex items-center gap-4 flex-shrink-0">
        <HealthBadge health={health} loading={loading} error={error} onRefresh={onRefresh} />
      </div>
    </header>
  );
}

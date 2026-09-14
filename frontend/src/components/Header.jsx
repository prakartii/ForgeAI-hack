import React from 'react';
import { HealthBadge } from './HealthBadge';
import { ShieldAlert, BookOpen } from 'lucide-react';

export function Header({ health, loading, error, onRefresh }) {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
      {/* Product Philosophy Tagline */}
      <div className="flex items-center gap-3">
        <div className="hidden lg:block text-xs text-slate-500 max-w-2xl">
          <span className="font-semibold text-slate-700">Philosophy: </span>
          <span className="italic">
            "PRISM finds and explains the failure. FailureFoundry turns that diagnosis into an executable behavioral contract that prevents recurrence."
          </span>
        </div>
      </div>

      {/* Live Backend Health & Status */}
      <div className="flex items-center gap-4">
        <HealthBadge
          health={health}
          loading={loading}
          error={error}
          onRefresh={onRefresh}
        />
      </div>
    </header>
  );
}

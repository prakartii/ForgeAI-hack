import React from 'react';
import { LIFECYCLE_STAGES } from '../types';
import { ChevronRight } from 'lucide-react';

export function LifecycleStepper({ currentStage = 'build' }) {
  const currentIndex = LIFECYCLE_STAGES.findIndex(s => s.id === currentStage);

  return (
    <div className="bg-white border-b border-slate-200 px-6 py-2.5 overflow-x-auto">
      <div className="flex items-center min-w-max text-xs font-mono">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-3 font-sans">
          Lifecycle:
        </span>
        {LIFECYCLE_STAGES.map((stage, idx) => {
          const isCurrent = idx === currentIndex;
          const isCompleted = idx < currentIndex;

          return (
            <React.Fragment key={stage.id}>
              <div
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded transition-colors ${
                  isCurrent
                    ? 'bg-slate-900 text-white font-semibold shadow-sm'
                    : isCompleted
                    ? 'text-emerald-700 bg-emerald-50/50'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
                title={stage.description}
              >
                <span className={`text-[10px] ${isCurrent ? 'text-slate-300' : 'text-slate-400'}`}>
                  {idx + 1}
                </span>
                <span>{stage.label}</span>
              </div>
              {idx < LIFECYCLE_STAGES.length - 1 && (
                <ChevronRight className="w-3.5 h-3.5 text-slate-300 mx-0.5 flex-shrink-0" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

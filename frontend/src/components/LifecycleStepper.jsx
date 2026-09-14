import React from 'react';
import { LIFECYCLE_STAGES } from '../types';

export function LifecycleStepper({ currentStage = 'build' }) {
  const currentIndex = LIFECYCLE_STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="bg-paper-panel border-b border-line px-6 py-2 overflow-x-auto">
      <div className="flex items-center min-w-max">
        {LIFECYCLE_STAGES.map((stage, idx) => {
          const isCurrent = idx === currentIndex;
          const isCompleted = idx < currentIndex;

          return (
            <React.Fragment key={stage.id}>
              <div
                className={`flex items-center gap-1.5 px-2 py-1 text-[12px] ${
                  isCurrent ? 'text-ink font-medium' : isCompleted ? 'text-verdant-700' : 'text-ink-faint'
                }`}
                title={stage.description}
              >
                <span className="font-serif text-[11px]">{idx + 1}</span>
                <span>{stage.label}</span>
              </div>
              {idx < LIFECYCLE_STAGES.length - 1 && (
                <span className="text-line-strong mx-0.5 flex-shrink-0">·</span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

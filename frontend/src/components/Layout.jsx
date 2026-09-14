import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { LifecycleStepper } from './LifecycleStepper';

export function Layout({
  children,
  currentTab,
  onSelectTab,
  health,
  loading,
  error,
  onRefresh,
}) {
  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <Sidebar currentTab={currentTab} onSelectTab={onSelectTab} />

      {/* Main Content Pane */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header with live health badge */}
        <Header
          health={health}
          loading={loading}
          error={error}
          onRefresh={onRefresh}
        />

        {/* Global Lifecycle Stepper */}
        <LifecycleStepper currentStage="build" />

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

import React from 'react';
import { NAV_ITEMS } from '../types';
import {
  LayoutDashboard,
  PlayCircle,
  GitFork,
  AlertTriangle,
  Eye,
  FileCode2,
  ShieldAlert,
  History,
  GitCompare,
  ShieldCheck,
  Cpu,
} from 'lucide-react';

const ICON_MAP = {
  LayoutDashboard,
  PlayCircle,
  GitFork,
  AlertTriangle,
  Eye,
  FileCode2,
  ShieldAlert,
  History,
  GitCompare,
  ShieldCheck,
};

export function Sidebar({ currentTab, onSelectTab }) {
  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 h-full border-r border-slate-800">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800/80">
        <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center text-slate-950 font-bold shadow">
          <Cpu className="w-5 h-5 text-slate-900" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-white leading-none">FailureFoundry</h1>
          <p className="text-[11px] text-slate-400 font-mono mt-1">Behavior ABI & Governance</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
          Platform Views
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = ICON_MAP[item.icon] || LayoutDashboard;
          const isActive = currentTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-colors text-left ${
                isActive
                  ? 'bg-slate-800 text-white font-semibold shadow-inner'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Demo App Context Badge */}
      <div className="p-4 border-t border-slate-800 text-[11px] text-slate-400">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="font-semibold text-slate-300">Demonstration App:</span>
          <span className="font-mono text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/60">
            FairClaim
          </span>
        </div>
        <p className="text-[10px] text-slate-500 leading-tight">
          Synthetic multi-agent insurance claims system
        </p>
      </div>
    </aside>
  );
}

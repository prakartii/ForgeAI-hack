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
    <aside className="w-60 bg-ink text-white/70 flex flex-col flex-shrink-0 h-full">
      <div className="h-16 flex items-center px-6 border-b border-white/10">
        <h1 className="font-serif text-lg font-medium text-white tracking-tight">FailureFoundry</h1>
      </div>

      <nav className="flex-1 px-3 py-5 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = ICON_MAP[item.icon] || LayoutDashboard;
          const isActive = currentTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center gap-2.5 pl-3 pr-3 py-2 rounded-r-sm text-[13px] transition-colors text-left border-l-2 ${
                isActive
                  ? 'border-l-white text-white bg-white/[0.06] font-medium'
                  : 'border-l-transparent text-white/55 hover:text-white/90 hover:bg-white/[0.03]'
              }`}
            >
              <Icon className={`w-[15px] h-[15px] flex-shrink-0 ${isActive ? 'text-white' : 'text-white/40'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="px-6 py-4 border-t border-white/10">
        <p className="text-[11px] text-white/40 leading-relaxed">
          Demonstration environment
        </p>
        <a href="/users" className="text-[13px] text-white/85 font-serif hover:text-white transition-colors">
          FairClaim →
        </a>
      </div>
    </aside>
  );
}

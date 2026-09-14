import React, { useState, useEffect } from 'react';
import { fetchAgents, fetchAbis, fetchPrismStatus } from '../services/api';
import { Server, Shield, Layers, Eye, CheckCircle, Database, AlertCircle, Clock } from 'lucide-react';

export function OverviewPage({ health }) {
  const [agents, setAgents] = useState([]);
  const [abis, setAbis] = useState([]);
  const [prismStatus, setPrismStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [agentsData, abisData, prismData] = await Promise.all([
          fetchAgents().catch(() => []),
          fetchAbis().catch(() => []),
          fetchPrismStatus().catch(() => null),
        ]);
        setAgents(agentsData);
        setAbis(abisData);
        setPrismStatus(prismData);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">System Overview</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Phase 1 Foundation: Project skeleton, runtime contracts, database, and health connection
        </p>
      </div>

      {/* Primary Status Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Backend Connectivity */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">FastAPI Backend</span>
            <Server className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900 font-mono">
              {health ? health.status.toUpperCase() : 'CONNECTING'}
            </span>
            {health && (
              <span className="text-xs text-emerald-600 font-medium">v{health.version}</span>
            )}
          </div>
          <p className="text-[11px] text-slate-500 mt-2 flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-slate-400" />
            Env: <span className="font-mono text-slate-700">{health?.environment || 'development'}</span>
          </p>
        </div>

        {/* SQLite Database */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">SQLite MVP DB</span>
            <Database className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900 font-mono">
              {health?.database === 'connected' ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            17 Schema tables initialized
          </p>
        </div>

        {/* Behavior ABI Specs */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">Behavior ABIs</span>
            <Shield className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900 font-mono">
              {abis.length} Active
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono">
            {abis.map(a => a.abi_version).join(', ') || 'Loading specs...'}
          </p>
        </div>

        {/* PRISM Monitor Status */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">PRISM Integration</span>
            <Eye className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900 font-mono">
              {prismStatus?.status === 'configured' ? 'CONFIGURED' : 'STANDBY'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 truncate font-mono" title={prismStatus?.message}>
            {prismStatus?.status === 'configured' ? prismStatus.base_url : 'Credentials pending (Phase 5)'}
          </p>
        </div>
      </div>

      {/* Two Column Layout: FairClaim Agents & Architecture Boundaries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* FairClaim Insurance Agent Pipeline Status */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-slate-600" />
              <h3 className="text-sm font-semibold text-slate-900">FairClaim Agents (Demo Environment)</h3>
            </div>
            <span className="text-[11px] font-mono bg-slate-200/70 text-slate-700 px-2 py-0.5 rounded">
              CLAUDE.md §6
            </span>
          </div>
          <div className="p-5 divide-y divide-slate-100">
            {agents.map((agent) => (
              <div key={agent.name} className="py-3 first:pt-0 last:pb-0 flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900 font-mono">{agent.name}</span>
                    <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.2 rounded font-mono">
                      {agent.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{agent.role}</p>
                </div>
                <div className="text-[11px] font-mono text-slate-400">
                  {agent.supported_versions.join(', ')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Architectural Boundaries & Responsibility Separation */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-slate-600" />
              <h3 className="text-sm font-semibold text-slate-900">Architectural Separation</h3>
            </div>
            <span className="text-[11px] font-mono bg-slate-200/70 text-slate-700 px-2 py-0.5 rounded">
              CLAUDE.md §2 & §4
            </span>
          </div>
          <div className="p-5 space-y-4 text-xs">
            <div className="p-3 bg-slate-50 rounded-md border border-slate-200">
              <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                PRISM Responsibility
              </div>
              <p className="text-slate-600 mt-1">
                Observes traces/sessions, evaluates agent behavior, surfaces root causes, provides evidence, proves before/after improvement.
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded-md border border-slate-200">
              <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-sky-500"></span>
                FailureFoundry Responsibility
              </div>
              <p className="text-slate-600 mt-1">
                Generates scenarios, compiles diagnoses into Behavior ABIs, enforces runtime controls, hardens challenge ladders, runs regression tests, gates releases.
              </p>
            </div>

            <div className="text-[11px] text-slate-500 italic">
              Note: FailureFoundry never replaces PRISM; it operationalizes PRISM's findings into executable behavioral contracts.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

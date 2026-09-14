import React, { useState, useEffect } from 'react';
import {
  fetchAgents, fetchAbis, fetchPrismStatus, fetchGraphStatus,
  fetchFailures, fetchRegressions, fetchGateResults, loadDemoDataset,
} from '../services/api';
import { Server, Shield, Layers, Eye, Database, Clock, GitFork, AlertTriangle, History, ShieldCheck, UploadCloud } from 'lucide-react';
import { ActionButton, Badge, ErrorNote } from '../components/ui';

export function OverviewPage({ health }) {
  const [agents, setAgents] = useState([]);
  const [abis, setAbis] = useState([]);
  const [prismStatus, setPrismStatus] = useState(null);
  const [graphStatus, setGraphStatus] = useState(null);
  const [failures, setFailures] = useState([]);
  const [regressions, setRegressions] = useState([]);
  const [gates, setGates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingDataset, setLoadingDataset] = useState(false);
  const [loadResult, setLoadResult] = useState(null);
  const [error, setError] = useState(null);

  async function loadData() {
    try {
      const [agentsData, abisData, prismData, graphData, failuresData, regressionsData, gatesData] = await Promise.all([
        fetchAgents().catch(() => []),
        fetchAbis().catch(() => []),
        fetchPrismStatus().catch(() => null),
        fetchGraphStatus().catch(() => null),
        fetchFailures().catch(() => []),
        fetchRegressions().catch(() => []),
        fetchGateResults().catch(() => []),
      ]);
      setAgents(agentsData);
      setAbis(abisData);
      setPrismStatus(prismData);
      setGraphStatus(graphData);
      setFailures(failuresData);
      setRegressions(regressionsData);
      setGates(gatesData);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  const handleLoadDataset = async () => {
    setLoadingDataset(true);
    try {
      const result = await loadDemoDataset();
      setLoadResult(result);
      setError(null);
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingDataset(false);
    }
  };

  const unresolvedCritical = failures.filter((f) => f.severity === 'CRITICAL' && !f.resolved).length;
  const regressionPassRate = regressions.length
    ? Math.round((regressions.filter((r) => r.still_passing).length / regressions.length) * 100)
    : null;
  const latestGate = gates[0];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">System Overview</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Current agent versions, reliability metrics, active failures, ABI/regression/release status
          </p>
        </div>
        <div className="text-right">
          <ActionButton onClick={handleLoadDataset} loading={loadingDataset}>
            <UploadCloud className="w-3.5 h-3.5" /> Load Demo Dataset
          </ActionButton>
          {loadResult && (
            <p className="text-[11px] text-slate-500 mt-1 font-mono">
              {loadResult.loaded.claims} claims loaded · oracle mismatches: {loadResult.oracle_check.mismatches}
            </p>
          )}
        </div>
      </div>
      <ErrorNote message={error} />

      {/* Reliability / Failure / Regression / Release Status Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">Active Failures</span>
            <AlertTriangle className="w-4 h-4 text-slate-400" />
          </div>
          <div className={`text-xl font-bold font-mono ${unresolvedCritical > 0 ? 'text-red-700' : 'text-emerald-700'}`}>
            {unresolvedCritical} Critical
          </div>
          <p className="text-[11px] text-slate-500 mt-2">{failures.length} total detected</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">Regression Suite</span>
            <History className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-xl font-bold font-mono text-slate-900">
            {regressionPassRate === null ? 'No tests yet' : `${regressionPassRate}%`}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">{regressions.length} permanent regression tests</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">Release Status</span>
            <ShieldCheck className="w-4 h-4 text-slate-400" />
          </div>
          <div>
            {latestGate ? (
              <Badge tone={latestGate.status === 'PASS' ? 'emerald' : 'red'}>{latestGate.status}</Badge>
            ) : (
              <span className="text-xl font-bold font-mono text-slate-400">Not run</span>
            )}
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono">{latestGate?.candidate_version || 'run from Release Gate'}</p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">Agent Versions</span>
            <Layers className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-xl font-bold font-mono text-slate-900">v1 / v2</div>
          <p className="text-[11px] text-slate-500 mt-2">v1: controlled weaknesses · v2: ABI-enforced</p>
        </div>
      </div>

      {/* Primary Status Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">SQLite (Primary)</span>
            <Database className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900 font-mono">
              {health?.database === 'connected' ? 'CONNECTED' : 'STANDBY'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            System of record (17 tables)
          </p>
        </div>

        {/* Neo4j Graph Projection */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">Neo4j (Graph)</span>
            <GitFork className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900 font-mono">
              {(graphStatus?.status || health?.graph_database || 'standby').toUpperCase()}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 truncate font-mono" title={graphStatus?.message}>
            {graphStatus?.status === 'connected' ? 'Causal graph active' : 'Causal lineage projection'}
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
          <p className="text-[11px] text-slate-500 mt-2 font-mono truncate">
            {abis.map(a => a.abi_version).join(', ') || 'Loading specs...'}
          </p>
        </div>

        {/* PRISM Monitor Status */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">PRISM Monitor</span>
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
              <h3 className="text-sm font-semibold text-slate-900">Polyglot Persistence & Architecture</h3>
            </div>
            <span className="text-[11px] font-mono bg-slate-200/70 text-slate-700 px-2 py-0.5 rounded">
              CLAUDE.md §5 & §10
            </span>
          </div>
          <div className="p-5 space-y-3 text-xs">
            <div className="p-2.5 bg-slate-50 rounded-md border border-slate-200">
              <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                SQLite: Primary System of Record
              </div>
              <p className="text-slate-600 mt-0.5">
                Holds all authoritative transactional data, claim forms, policy documents, raw execution trace envelopes, and regression obligations.
              </p>
            </div>

            <div className="p-2.5 bg-slate-50 rounded-md border border-slate-200">
              <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-sky-500"></span>
                Neo4j: Causal Execution & Lineage Graph
              </div>
              <p className="text-slate-600 mt-0.5">
                Captures agent handoff DAGs, tool calls, multi-hop root-cause tracing, and the failure-to-ABI-to-release-gate dependency chain.
              </p>
            </div>

            <div className="p-2.5 bg-slate-50 rounded-md border border-slate-200">
              <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                PRISM Observation & Evaluation
              </div>
              <p className="text-slate-600 mt-0.5">
                Observes execution traces, computes evaluators, isolates failures, and proves before/after behavioral improvements.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

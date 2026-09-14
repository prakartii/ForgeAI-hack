import React, { useState, useEffect } from 'react';
import {
  fetchAgents, fetchAbis, fetchPrismStatus, fetchGraphStatus,
  fetchFailures, fetchRegressions, fetchGateResults, loadDemoDataset,
} from '../services/api';
import { Server, Shield, Layers, Eye, Database, GitFork, AlertTriangle, History, ShieldCheck, UploadCloud } from 'lucide-react';
import { ActionButton, Badge, Card, ErrorNote, MetricTile } from '../components/ui';

export function OverviewPage({ health }) {
  const [agents, setAgents] = useState([]);
  const [abis, setAbis] = useState([]);
  const [prismStatus, setPrismStatus] = useState(null);
  const [graphStatus, setGraphStatus] = useState(null);
  const [failures, setFailures] = useState([]);
  const [regressions, setRegressions] = useState([]);
  const [gates, setGates] = useState([]);
  const [loadingDataset, setLoadingDataset] = useState(false);
  const [loadResult, setLoadResult] = useState(null);
  const [error, setError] = useState(null);

  async function loadData() {
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
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-medium text-ink">Overview</h2>
          <p className="text-[13px] text-ink-soft mt-1">
            Current agent versions, reliability metrics, active failures, and release status
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <ActionButton onClick={handleLoadDataset} loading={loadingDataset}>
            <UploadCloud className="w-3.5 h-3.5" /> Load demo dataset
          </ActionButton>
          {loadResult && (
            <p className="text-[11px] text-ink-faint mt-1.5">
              {loadResult.loaded.claims} claims loaded, {loadResult.oracle_check.mismatches} oracle mismatches
            </p>
          )}
        </div>
      </div>
      <ErrorNote message={error} />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricTile
          icon={AlertTriangle}
          label="Active failures"
          value={`${unresolvedCritical} critical`}
          sub={`${failures.length} total detected`}
          tone={unresolvedCritical > 0 ? 'seal' : 'verdant'}
        />
        <MetricTile
          icon={History}
          label="Regression suite"
          value={regressionPassRate === null ? 'No tests yet' : `${regressionPassRate}%`}
          sub={`${regressions.length} permanent regression tests`}
        />
        <MetricTile
          icon={ShieldCheck}
          label="Release status"
          value={latestGate ? <Badge tone={latestGate.status === 'PASS' ? 'emerald' : 'red'}>{latestGate.status}</Badge> : 'Not run'}
          sub={latestGate?.candidate_version || 'Run from Release Gate'}
        />
        <MetricTile
          icon={Layers}
          label="Agent versions"
          value="v1 / v2"
          sub="v1: controlled weaknesses · v2: ABI-enforced"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricTile
          icon={Server}
          label="FastAPI backend"
          value={health ? health.status : 'connecting'}
          sub={`Environment: ${health?.environment || 'development'}`}
        />
        <MetricTile
          icon={Database}
          label="SQLite (primary)"
          value={health?.database === 'connected' ? 'Connected' : 'Standby'}
          sub="System of record, 17 tables"
        />
        <MetricTile
          icon={GitFork}
          label="Neo4j (graph)"
          value={graphStatus?.status === 'connected' ? 'Connected' : 'Standby'}
          sub={graphStatus?.status === 'connected' ? 'Causal graph active' : 'SQLite fallback in use'}
        />
        <MetricTile
          icon={Shield}
          label="Behavior ABIs"
          value={`${abis.length} active`}
          sub={abis.map((a) => a.abi_version).join(', ') || 'Loading specs…'}
        />
        <MetricTile
          icon={Eye}
          label="PRISM monitor"
          value={prismStatus?.status === 'configured' ? 'Configured' : 'Not configured'}
          sub={prismStatus?.status === 'configured' ? prismStatus.base_url : 'Credentials pending'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card icon={Layers} title="FairClaim agents" tag="Demonstration environment">
          <div className="divide-y divide-line -mt-2">
            {agents.map((agent) => (
              <div key={agent.name} className="py-3 first:pt-0 last:pb-0 flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-medium text-ink">{agent.name}</span>
                    <Badge tone="emerald">{agent.status}</Badge>
                  </div>
                  <p className="text-[12px] text-ink-soft mt-0.5">{agent.role}</p>
                </div>
                <div className="text-[11px] font-mono text-ink-faint flex-shrink-0">
                  {agent.supported_versions.join(', ')}
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card icon={Shield} title="Polyglot persistence" tag="SQLite + Neo4j">
          <div className="space-y-3 text-[13px] -mt-2">
            <div>
              <div className="font-medium text-ink flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-verdant" />
                SQLite — primary system of record
              </div>
              <p className="text-ink-soft mt-0.5 leading-relaxed">
                Holds every claim, policy, trace envelope, and regression obligation authoritatively.
              </p>
            </div>
            <div>
              <div className="font-medium text-ink flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-ledger" />
                Neo4j — causal execution & lineage graph
              </div>
              <p className="text-ink-soft mt-0.5 leading-relaxed">
                Projects agent handoff chains and the failure → ABI → release-gate dependency tree.
              </p>
            </div>
            <div>
              <div className="font-medium text-ink flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-brass" />
                PRISM — observation & evaluation
              </div>
              <p className="text-ink-soft mt-0.5 leading-relaxed">
                Observes execution traces, scores agent behavior, and proves before/after improvement.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

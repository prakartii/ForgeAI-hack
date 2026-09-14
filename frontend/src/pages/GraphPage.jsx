import React, { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import { Database, GitFork, Search } from 'lucide-react';
import { fetchCausalGraph, fetchGraphStatus } from '../services/api';
import { ActionButton, Card, ErrorNote } from '../components/ui';

function layoutNodes(rawNodes) {
  return rawNodes.map((node, idx) => ({
    id: node.id,
    data: { label: node.data?.label || node.id },
    position: { x: idx * 220, y: 80 },
    style: {
      border: node.data?.errors?.length ? '1px solid #dc2626' : '1px solid #cbd5e1',
      background: node.data?.errors?.length ? '#fef2f2' : '#ffffff',
      borderRadius: 8,
      fontSize: 11,
      fontFamily: 'monospace',
      padding: 8,
      width: 190,
    },
  }));
}

function layoutEdges(rawEdges) {
  return rawEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: '#94a3b8' },
  }));
}

export function GraphPage() {
  const [graphStatus, setGraphStatus] = useState(null);
  const [claimId, setClaimId] = useState('IMG_0002');
  const [graph, setGraph] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchGraphStatus().then(setGraphStatus).catch(() => null);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setGraph(await fetchCausalGraph(claimId));
      setError(null);
    } catch (err) {
      setError(err.message);
      setGraph(null);
    } finally {
      setLoading(false);
    }
  }, [claimId]);

  const nodes = useMemo(() => layoutNodes(graph?.nodes || []), [graph]);
  const edges = useMemo(() => layoutEdges(graph?.edges || []), [graph]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Causal Execution Graph</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §5 & §10: Claim → Intake → Adjudication → Explanation → Verification → Customer Communication
        </p>
      </div>

      <Card title="Load a Claim's Trace" icon={Search}>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs">
            <span className="block text-slate-500 mb-1 font-mono">claim_id</span>
            <input
              value={claimId}
              onChange={(e) => setClaimId(e.target.value)}
              className="border border-slate-300 rounded px-2 py-1.5 text-xs font-mono w-40"
            />
          </label>
          <ActionButton onClick={load} loading={loading}>Load Graph</ActionButton>
          <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-slate-50 border border-slate-200 text-xs font-mono text-slate-600">
            <Database className="w-3.5 h-3.5 text-sky-600" />
            Neo4j: {graphStatus?.status || 'standby'}
            {graph?.source && <span className="text-slate-400"> · source: {graph.source}</span>}
          </span>
        </div>
        <ErrorNote message={error} />
      </Card>

      <Card title="Execution Graph" icon={GitFork} noPadding>
        <div style={{ height: 500 }}>
          {nodes.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-400">
              No trace events for this claim yet — run it from Agent Runs first.
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              fitView
              fitViewOptions={{ padding: 0.3, maxZoom: 1.2 }}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={16} color="#e2e8f0" />
              <Controls showInteractive={false} />
            </ReactFlow>
          )}
        </div>
      </Card>
    </div>
  );
}

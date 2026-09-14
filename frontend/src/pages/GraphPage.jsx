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
    position: { x: idx * 210, y: 80 },
    style: {
      border: node.data?.errors?.length ? '1px solid #A6341E' : '1px solid #E1DFD6',
      background: node.data?.errors?.length ? '#F8E9E5' : '#FCFCFA',
      color: '#171A21',
      borderRadius: 4,
      fontSize: 12,
      fontFamily: '"IBM Plex Mono", monospace',
      padding: 8,
      width: 180,
    },
  }));
}

function layoutEdges(rawEdges) {
  return rawEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed, color: '#8A8F9C' },
    style: { stroke: '#8A8F9C' },
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
        <h2 className="text-2xl font-medium text-ink">Execution graph</h2>
        <p className="text-[13px] text-ink-soft mt-1">Claim → Intake → Adjudication → Explanation → Verification → Customer communication</p>
      </div>

      <Card title="Load a claim's trace" icon={Search}>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-[12px]">
            <span className="block text-ink-faint mb-1">Claim ID</span>
            <input
              value={claimId}
              onChange={(e) => setClaimId(e.target.value)}
              className="border border-line-strong rounded px-2.5 py-1.5 text-[13px] font-mono w-40 bg-paper-panel focus:border-ledger"
            />
          </label>
          <ActionButton onClick={load} loading={loading}>Load graph</ActionButton>
          <span className="inline-flex items-center gap-2 text-[12px] text-ink-faint">
            <Database className="w-3.5 h-3.5" />
            Neo4j: {graphStatus?.status || 'standby'}
            {graph?.source && <span>· source: {graph.source}</span>}
          </span>
        </div>
        <ErrorNote message={error} />
      </Card>

      <Card title="Execution graph" icon={GitFork} noPadding>
        <div style={{ height: 500 }}>
          {nodes.length === 0 ? (
            <div className="h-full flex items-center justify-center text-[13px] text-ink-faint">
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
              <Background gap={16} color="#E1DFD6" />
              <Controls showInteractive={false} />
            </ReactFlow>
          )}
        </div>
      </Card>
    </div>
  );
}

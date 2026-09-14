import React, { useState, useEffect } from 'react';
import { GitFork, Database } from 'lucide-react';
import { fetchGraphStatus } from '../services/api';

export function GraphPage() {
  const [graphStatus, setGraphStatus] = useState(null);

  useEffect(() => {
    fetchGraphStatus().then(setGraphStatus).catch(() => null);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Causal Execution Graph</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §5 & §10: Polyglot persistence (SQLite payloads + Neo4j execution DAG) rendered via React Flow
        </p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-500">
          <GitFork className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Causal Execution & Forensics Graph</h3>
          <p className="text-xs text-slate-500 max-w-lg mx-auto mt-1">
            Projects sequence flow: <span className="font-mono">Claim → Intake Output → Adjudication Decision → Explanation → Verification → Customer Communication</span>.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-slate-50 border border-slate-200 text-xs font-mono text-slate-600">
          <Database className="w-3.5 h-3.5 text-sky-600" />
          <span>Graph Engine: Neo4j ({graphStatus?.status || 'standby'})</span>
          <span className="text-slate-300">|</span>
          <span>Payload Store: SQLite</span>
        </div>

        <p className="text-[11px] text-slate-400 max-w-md mx-auto">
          In Phase 4, execution traces collected from agent runs will populate nodes and directed edges in Neo4j and stream live into the interactive React Flow canvas.
        </p>
      </div>
    </div>
  );
}

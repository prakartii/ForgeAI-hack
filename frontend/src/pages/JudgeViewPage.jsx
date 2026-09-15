import React, { useState, useCallback } from 'react';
import { RefreshCw, PlayCircle, ArrowRight, CheckCircle2, XCircle } from 'lucide-react';
import { computeMetrics, runReleaseGate } from '../services/api';
import { ActionButton, Badge, Card, ErrorNote, EmptyState } from '../components/ui';

const CLAUSE_LABELS = {
  critical_abi_violations: 'Critical ABI violations',
  fairness_threshold: 'Fairness threshold',
  workflow_compliance: 'Workflow compliance',
  evidence_completeness: 'Evidence completeness',
  historical_regressions: 'Historical regressions',
  hardened_scenarios: 'Hardened scenarios',
  prism_evidence: 'PRISM evidence',
};

function pct(v) {
  return v === null || v === undefined ? '—' : `${Math.round(v * 100)}%`;
}

/**
 * A judge sits down for two minutes and needs the whole story without
 * clicking through ten pages. This screen computes the same real
 * v1-vs-v2 metrics and release gate the Comparison / Release Gate pages
 * expose, and narrates them in the order CLAUDE.md sec30 specifies --
 * nothing here is a separate, simplified dataset.
 *
 * Deliberately NOT auto-run on mount: computing metrics executes ~150
 * real claims through the full pipeline per version, creating real
 * AgentRun rows. Since this is the console's landing page, auto-running
 * on every page load/refresh silently floods the Agent Runs table with
 * fresh, never-submitted-to-PRISM rows that push real PRISM-linked runs
 * off the PRISM Evidence page's correlation table (regression: this
 * happened for real once already). Every other page that executes real
 * runs (Comparison, Release Gate) requires an explicit click -- this one
 * does too.
 */
export function JudgeViewPage({ onNavigate }) {
  const [v1, setV1] = useState(null);
  const [v2, setV2] = useState(null);
  const [gate, setGate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runStory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [v1Metrics, v2Metrics] = await Promise.all([
        computeMetrics({ candidate_version: 'v1', enforced: false, sample_size: 150 }),
        computeMetrics({ candidate_version: 'v2', enforced: true, sample_size: 150 }),
      ]);
      setV1(v1Metrics);
      setV2(v2Metrics);
      setGate(await runReleaseGate({ candidate_version: 'v2' }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const status = gate?.status;
  const hasRun = v1 && v2;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-serif font-medium text-ink">The story, one screen</h2>
          <p className="text-[13px] text-ink-soft mt-1 max-w-xl">
            The same real v1-vs-v2 metrics and release gate as Version Comparison and Release
            Gate, narrated in order — computed on demand, not on every page load, since each run
            executes real claims and adds real Agent Run rows.
          </p>
        </div>
        <ActionButton onClick={runStory} loading={loading} variant={hasRun ? 'secondary' : 'primary'}>
          {hasRun ? <RefreshCw className="w-3.5 h-3.5" /> : <PlayCircle className="w-3.5 h-3.5" />}
          {hasRun ? 'Re-run live' : 'Run the story'}
        </ActionButton>
      </div>
      <ErrorNote message={error} />

      {!hasRun && !loading && (
        <EmptyState
          title="Not yet run this session"
          description="Click “Run the story” to compute v1 vs v2 metrics and the v2 release gate from real executions — takes a few seconds."
        />
      )}

      {hasRun && (
      <>
      <blockquote className="border-l-[3px] border-brass pl-4 py-1 text-[15px] font-serif italic text-ink">
        "PRISM finds and explains the failure. FailureFoundry turns that diagnosis into an
        executable behavioral contract that prevents recurrence."
      </blockquote>

      <Card accent="seal" title="1 · v1 — the controlled failure" tag="ZIP, name, narrative style reach Adjudication">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <Tile label="Pairwise consistency" value={pct(v1?.pairwise_consistency)} tone="seal" />
          <Tile label="Workflow compliance" value={pct(v1?.workflow_compliance)} tone="seal" />
          <Tile label="Evidence completeness" value={pct(v1?.evidence_completeness)} tone="seal" />
        </div>
        <p className="text-[13px] text-ink-soft mt-4 leading-relaxed">
          Matched claims — identical policy, loss, peril, damage, evidence — differ only in
          claimant name, ZIP, and narrative style. Below full consistency, that gap is the
          failure: legitimate facts didn't change, but the outcome did.
        </p>
      </Card>

      <div className="flex items-center gap-3 pl-2 text-[12px] text-ink-faint">
        <ArrowRight className="w-3.5 h-3.5" />
        PRISM diagnoses it → FailureFoundry compiles <code className="font-mono">fair_adjudication_v1</code> into
        an enforceable ABI
        <button onClick={() => onNavigate?.('abi')} className="text-ledger-700 font-medium hover:underline">
          view the ABI →
        </button>
      </div>

      <Card accent="verdant" title="2 · v2 — ABI enforced" tag="ZIP, name, narrative removed from context">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Tile label="Pairwise consistency" value={pct(v2?.pairwise_consistency)} tone="verdant" delta={delta(v1?.pairwise_consistency, v2?.pairwise_consistency)} />
          <Tile label="Workflow compliance" value={pct(v2?.workflow_compliance)} tone="verdant" delta={delta(v1?.workflow_compliance, v2?.workflow_compliance)} />
          <Tile label="Evidence completeness" value={pct(v2?.evidence_completeness)} tone="verdant" delta={delta(v1?.evidence_completeness, v2?.evidence_completeness)} />
          <Tile label="Challenge robustness" value={pct(v2?.challenge_robustness)} tone="verdant" />
        </div>
        <p className="text-[13px] text-ink-soft mt-4 leading-relaxed">
          Same matched claims, same underlying facts — the only change is that the prohibited
          fields are structurally absent from Adjudication's context before it reasons. That's
          verifiable by inspecting the context object, not asserted from the output.
        </p>
      </Card>

      <div className="flex items-center gap-3 pl-2 text-[12px] text-ink-faint">
        <ArrowRight className="w-3.5 h-3.5" />
        Hardened against harder variants, held as a permanent regression test
        <button onClick={() => onNavigate?.('regression')} className="text-ledger-700 font-medium hover:underline">
          view regression suite →
        </button>
      </div>

      <Card noPadding title="3 · Release gate — live, for v2" tag="POST /api/gates/run">
        <div className="p-5">
          <div className="flex items-center justify-between pb-4 border-b border-line gap-4">
            <p className="text-[13px] text-ink-soft max-w-sm">
              Every clause below must actually pass — this is the same evaluation the Release
              Gate page runs, not a separate summary.
            </p>
            <div className={`px-5 py-2.5 rounded border text-center flex-shrink-0 ${
              !status
                ? 'border-line-strong text-ink-faint'
                : status === 'PASS'
                ? 'border-verdant-100 bg-verdant-50 text-verdant-700'
                : 'border-seal-100 bg-seal-50 text-seal-700'
            }`}>
              <div className="font-serif text-lg leading-none">{status || '…'}</div>
              <div className="text-[11px] mt-1 opacity-80">candidate v2</div>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-4">
            {Object.entries(CLAUSE_LABELS).map(([key, label]) => {
              const detail = gate?.failure_summary?.[key];
              return (
                <div key={key} className="flex items-start gap-2 text-[12.5px]">
                  {gate ? (
                    detail?.passed ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-verdant-600 mt-0.5 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-3.5 h-3.5 text-seal-600 mt-0.5 flex-shrink-0" />
                    )
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full border border-line-strong flex-shrink-0" />
                  )}
                  <div>
                    <span className="text-ink font-medium">{label}</span>
                    {detail?.detail && <span className="text-ink-faint"> — {detail.detail}</span>}
                  </div>
                </div>
              );
            })}
          </div>
          {gate?.violated_clauses?.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-x-3 gap-y-1.5">
              {gate.violated_clauses.map((c) => <Badge key={c} tone="red">{c.replace(/_/g, ' ')}</Badge>)}
            </div>
          )}
          <button onClick={() => onNavigate?.('gate')} className="text-[12px] text-ledger-700 font-medium hover:underline mt-4 inline-block">
            open full Release Gate page →
          </button>
        </div>
      </Card>
      </>
      )}
    </div>
  );
}

function delta(before, after) {
  if (before === null || before === undefined || after === null || after === undefined) return null;
  const d = Math.round((after - before) * 100);
  if (d <= 0) return null;
  return `+${d}pt`;
}

function Tile({ label, value, tone, delta: d }) {
  const toneText = tone === 'seal' ? 'text-seal-700' : tone === 'verdant' ? 'text-verdant-700' : 'text-ink';
  return (
    <div className="bg-paper-panel p-3.5 rounded-md border border-line">
      <div className="text-[11px] text-ink-faint mb-1.5">{label}</div>
      <div className={`text-xl font-serif font-medium ${toneText} flex items-baseline gap-1.5`}>
        {value}
        {d && <span className="text-[11px] font-sans font-medium text-verdant-600">{d}</span>}
      </div>
    </div>
  );
}

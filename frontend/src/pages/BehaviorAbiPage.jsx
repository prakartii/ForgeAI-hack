import React, { useState, useEffect } from 'react';
import { FileCode2, Shield, AlertOctagon, CheckCircle2 } from 'lucide-react';
import { fetchAbis } from '../services/api';

export function BehaviorAbiPage() {
  const [abis, setAbis] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAbis().then(setAbis).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Behavior ABI Registry</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §16: Versioned, executable behavioral contracts compiled from failure diagnoses
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {abis.map((abi) => (
          <div key={abi.abi_version} className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/60 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileCode2 className="w-5 h-5 text-sky-600" />
                <div>
                  <h3 className="text-sm font-bold text-slate-900 font-mono">{abi.abi_version}</h3>
                  <p className="text-xs text-slate-500">{abi.description}</p>
                </div>
              </div>
              <span className="text-xs font-mono bg-sky-50 text-sky-700 border border-sky-200 px-2.5 py-1 rounded">
                Source: {abi.source_file}
              </span>
            </div>

            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
              {/* Prohibited Factors */}
              {abi.prohibited && abi.prohibited.length > 0 && (
                <div className="p-4 rounded-md border border-red-200 bg-red-50/40">
                  <div className="flex items-center gap-2 text-red-800 font-semibold mb-2">
                    <AlertOctagon className="w-4 h-4 text-red-600" />
                    <span>Prohibited Factors (Enforcement Redaction)</span>
                  </div>
                  <ul className="space-y-1 font-mono text-red-700">
                    {abi.prohibited.map((item, i) => (
                      <li key={i}>• {item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Permitted Factors */}
              {abi.permitted && abi.permitted.length > 0 && (
                <div className="p-4 rounded-md border border-emerald-200 bg-emerald-50/40">
                  <div className="flex items-center gap-2 text-emerald-800 font-semibold mb-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Permitted Factors (Legitimate Facts)</span>
                  </div>
                  <ul className="space-y-1 font-mono text-emerald-700">
                    {abi.permitted.map((item, i) => (
                      <li key={i}>• {item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Invariants */}
              {abi.invariants && abi.invariants.length > 0 && (
                <div className="md:col-span-2 p-4 rounded-md border border-slate-200 bg-slate-50">
                  <div className="font-semibold text-slate-800 mb-2">Behavioral Invariants</div>
                  <div className="space-y-1.5 font-mono text-slate-700">
                    {abi.invariants.map((inv, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-slate-400 font-semibold">{inv.name}:</span>
                        <span>"{inv.rule}"</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

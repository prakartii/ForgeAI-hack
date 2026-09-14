import React, { useEffect, useState } from 'react';
import { FileCode2, AlertOctagon, CheckCircle2, Terminal } from 'lucide-react';
import { fetchAbiRules, fetchAbis } from '../services/api';
import { Badge, Card } from '../components/ui';

export function BehaviorAbiPage() {
  const [abis, setAbis] = useState([]);
  const [rulesByVersion, setRulesByVersion] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const abiList = await fetchAbis();
        setAbis(abiList);
        const rules = {};
        for (const abi of abiList) {
          rules[abi.abi_version] = await fetchAbiRules(abi.abi_version);
        }
        setRulesByVersion(rules);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Behavior ABI Registry</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          CLAUDE.md §16: versioned, executable behavioral contracts compiled from failure diagnoses
        </p>
      </div>

      {loading && <p className="text-xs text-slate-500">Compiling ABIs from /abis specs...</p>}

      <div className="grid grid-cols-1 gap-6">
        {abis.map((abi) => (
          <Card
            key={abi.abi_version}
            icon={FileCode2}
            title={abi.abi_version}
            tag={abi.is_active ? 'ACTIVE' : 'INACTIVE'}
          >
            <p className="text-xs text-slate-500 -mt-2 mb-4">{abi.description}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs mb-4">
              {abi.prohibited_factors?.length > 0 && (
                <div className="p-4 rounded-md border border-red-200 bg-red-50/40">
                  <div className="flex items-center gap-2 text-red-800 font-semibold mb-2">
                    <AlertOctagon className="w-4 h-4 text-red-600" />
                    <span>Prohibited Factors</span>
                  </div>
                  <ul className="space-y-1 font-mono text-red-700">
                    {abi.prohibited_factors.map((item) => <li key={item}>• {item}</li>)}
                  </ul>
                </div>
              )}

              {abi.permitted_factors?.length > 0 && (
                <div className="p-4 rounded-md border border-emerald-200 bg-emerald-50/40">
                  <div className="flex items-center gap-2 text-emerald-800 font-semibold mb-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Permitted Factors</span>
                  </div>
                  <ul className="space-y-1 font-mono text-emerald-700">
                    {abi.permitted_factors.map((item) => <li key={item}>• {item}</li>)}
                  </ul>
                </div>
              )}

              {abi.invariants?.length > 0 && (
                <div className="md:col-span-2 p-4 rounded-md border border-slate-200 bg-slate-50">
                  <div className="font-semibold text-slate-800 mb-2">Invariants</div>
                  <div className="space-y-1.5 font-mono text-slate-700">
                    {abi.invariants.map((inv) => (
                      <div key={inv.name} className="flex items-start gap-2">
                        <span className="text-slate-400 font-semibold">{inv.name}:</span>
                        <span>"{inv.rule}"</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {abi.workflow_rules?.length > 0 && (
                <div className="md:col-span-2 p-4 rounded-md border border-sky-200 bg-sky-50/40">
                  <div className="font-semibold text-sky-800 mb-2">Workflow Requirements</div>
                  <div className="space-y-1.5 font-mono text-sky-700">
                    {abi.workflow_rules.map((req) => (
                      <div key={req.name}>• {req.rule}</div>
                    ))}
                  </div>
                </div>
              )}

              {abi.release_constraints?.length > 0 && (
                <div className="md:col-span-2 p-4 rounded-md border border-amber-200 bg-amber-50/40">
                  <div className="font-semibold text-amber-800 mb-2">Release Constraints</div>
                  <ul className="space-y-1 font-mono text-amber-700">
                    {abi.release_constraints.map((c) => <li key={c}>• {c}</li>)}
                  </ul>
                </div>
              )}
            </div>

            <div className="border-t border-slate-200 pt-4">
              <div className="flex items-center gap-2 text-slate-700 font-semibold text-xs mb-2">
                <Terminal className="w-3.5 h-3.5" />
                <span>Compiled Executable Rules</span>
                <span className="text-slate-400 font-normal">
                  — the actual runtime hooks this ABI produces (CLAUDE.md §16.1: never arbitrary text)
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="text-left text-slate-400 font-mono uppercase border-b border-slate-200">
                      <th className="py-1.5 pr-3">Type</th>
                      <th className="py-1.5 pr-3">Clause</th>
                      <th className="py-1.5 pr-3">executable_action</th>
                      <th className="py-1.5 pr-3">Severity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(rulesByVersion[abi.abi_version] || []).map((rule) => (
                      <tr key={rule.rule_id}>
                        <td className="py-1.5 pr-3"><Badge>{rule.rule_type}</Badge></td>
                        <td className="py-1.5 pr-3 text-slate-600">{rule.clause}</td>
                        <td className="py-1.5 pr-3 font-mono text-sky-700">{rule.executable_action}</td>
                        <td className="py-1.5 pr-3"><Badge tone={rule.severity === 'CRITICAL' ? 'red' : 'amber'}>{rule.severity}</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

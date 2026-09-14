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
        <h2 className="text-2xl font-medium text-ink">Behavior ABI registry</h2>
        <p className="text-[13px] text-ink-soft mt-1">Versioned, executable behavioral contracts compiled from failure diagnoses</p>
      </div>

      {loading && <p className="text-[13px] text-ink-faint">Compiling ABIs from /abis specs…</p>}

      <div className="grid grid-cols-1 gap-6">
        {abis.map((abi) => (
          <Card
            key={abi.abi_version}
            icon={FileCode2}
            title={abi.abi_version}
            tag={abi.is_active ? 'Active' : 'Inactive'}
          >
            <p className="text-[13px] text-ink-soft -mt-1 mb-4">{abi.description}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[13px] mb-5">
              {abi.prohibited_factors?.length > 0 && (
                <div className="p-4 rounded border border-seal-100 bg-seal-50">
                  <div className="flex items-center gap-2 text-seal-700 font-medium mb-2">
                    <AlertOctagon className="w-4 h-4" />
                    <span>Prohibited factors</span>
                  </div>
                  <ul className="space-y-1 font-mono text-[12px] text-seal-700">
                    {abi.prohibited_factors.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </div>
              )}

              {abi.permitted_factors?.length > 0 && (
                <div className="p-4 rounded border border-verdant-100 bg-verdant-50">
                  <div className="flex items-center gap-2 text-verdant-700 font-medium mb-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Permitted factors</span>
                  </div>
                  <ul className="space-y-1 font-mono text-[12px] text-verdant-700">
                    {abi.permitted_factors.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </div>
              )}

              {abi.invariants?.length > 0 && (
                <div className="md:col-span-2 p-4 rounded border border-line bg-paper-sunk">
                  <div className="font-medium text-ink mb-2">Invariants</div>
                  <div className="space-y-1.5 text-[13px] text-ink-soft">
                    {abi.invariants.map((inv) => (
                      <div key={inv.name}>"{inv.rule}"</div>
                    ))}
                  </div>
                </div>
              )}

              {abi.workflow_rules?.length > 0 && (
                <div className="md:col-span-2 p-4 rounded border border-ledger-100 bg-ledger-50">
                  <div className="font-medium text-ledger-700 mb-2">Workflow requirements</div>
                  <div className="space-y-1.5 text-[13px] text-ledger-700">
                    {abi.workflow_rules.map((req) => (
                      <div key={req.name}>{req.rule}</div>
                    ))}
                  </div>
                </div>
              )}

              {abi.release_constraints?.length > 0 && (
                <div className="md:col-span-2 p-4 rounded border border-brass-100 bg-brass-50">
                  <div className="font-medium text-brass-700 mb-2">Release constraints</div>
                  <ul className="space-y-1 text-[13px] text-brass-700">
                    {abi.release_constraints.map((c) => <li key={c}>{c}</li>)}
                  </ul>
                </div>
              )}
            </div>

            <div className="border-t border-line pt-4">
              <div className="flex items-center gap-2 text-ink font-medium text-[13px] mb-1">
                <Terminal className="w-3.5 h-3.5 text-ink-soft" />
                <span>Compiled executable rules</span>
              </div>
              <p className="text-[12px] text-ink-faint mb-3">The actual runtime hooks this ABI produces — never arbitrary text.</p>
              <div className="overflow-x-auto">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="text-left text-ink-faint border-b border-line">
                      <th className="py-1.5 pr-3 font-normal">Type</th>
                      <th className="py-1.5 pr-3 font-normal">Clause</th>
                      <th className="py-1.5 pr-3 font-normal">Executable action</th>
                      <th className="py-1.5 pr-3 font-normal">Severity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {(rulesByVersion[abi.abi_version] || []).map((rule) => (
                      <tr key={rule.rule_id}>
                        <td className="py-1.5 pr-3"><Badge>{rule.rule_type.replace(/_/g, ' ').toLowerCase()}</Badge></td>
                        <td className="py-1.5 pr-3 text-ink-soft">{rule.clause}</td>
                        <td className="py-1.5 pr-3 font-mono text-ledger-700">{rule.executable_action}</td>
                        <td className="py-1.5 pr-3"><Badge tone={rule.severity === 'CRITICAL' ? 'red' : 'amber'}>{rule.severity.toLowerCase()}</Badge></td>
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

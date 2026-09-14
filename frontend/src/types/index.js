/**
 * Locked Lifecycle stages from CLAUDE.md §3:
 * BUILD -> ATTACK -> PRISM OBSERVE -> EVALUATE -> DIAGNOSE -> COMPILE BEHAVIOR ABI ->
 * ENFORCE -> FIX / HARDEN -> PRISM PROVE -> REGRESSION TEST -> RELEASE GATE
 */
export const LIFECYCLE_STAGES = [
  { id: 'build', label: 'Build', description: 'Initialize agents and baseline policies' },
  { id: 'attack', label: 'Attack', description: 'Execute matched counterfactuals & fault scenarios' },
  { id: 'prism_observe', label: 'PRISM observe', description: 'Stream granular agent & tool traces to PRISM' },
  { id: 'evaluate', label: 'Evaluate', description: 'Evaluate execution traces with evaluators' },
  { id: 'diagnose', label: 'Diagnose', description: 'Isolate root cause of behavioral failure' },
  { id: 'compile_abi', label: 'Compile behavior ABI', description: 'Synthesize executable behavioral contract' },
  { id: 'enforce', label: 'Enforce', description: 'Apply runtime context sanitization and checkpoints' },
  { id: 'harden', label: 'Fix / harden', description: 'Challenge against adversarial variation ladders' },
  { id: 'prism_prove', label: 'PRISM prove', description: 'Fetch backing proof of before/after improvement' },
  { id: 'regression', label: 'Regression test', description: 'Verify candidate version against historical suite' },
  { id: 'release_gate', label: 'Release gate', description: 'Strict PASS or BLOCKED deployment gating' },
];

/**
 * Navigation items for primary dashboard views from CLAUDE.md §24.
 */
export const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: 'LayoutDashboard' },
  { id: 'runs', label: 'Agent Runs', icon: 'PlayCircle' },
  { id: 'graph', label: 'Execution Graph', icon: 'GitFork' },
  { id: 'failures', label: 'Failures', icon: 'AlertTriangle' },
  { id: 'prism', label: 'PRISM Evidence', icon: 'Eye' },
  { id: 'abi', label: 'Behavior ABI', icon: 'FileCode2' },
  { id: 'hardening', label: 'Hardening', icon: 'ShieldAlert' },
  { id: 'regression', label: 'Regression', icon: 'History' },
  { id: 'comparison', label: 'Version Comparison', icon: 'GitCompare' },
  { id: 'gate', label: 'Release Gate', icon: 'ShieldCheck' },
];

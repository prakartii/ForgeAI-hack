/**
 * API Service Layer for FailureFoundry.
 * Talks to FastAPI backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

async function getJSON(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`GET ${path} failed with status: ${response.status}`);
  }
  return response.json();
}

async function postJSON(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed with status: ${response.status}`);
  }
  return response.json();
}

// --- Core status ---
export const fetchHealth = () => getJSON('/health');
export const fetchAgents = () => getJSON('/api/agents');
export const fetchPrismStatus = () => getJSON('/api/prism/status');
export const submitRunToPrism = (runId) => postJSON(`/api/prism/runs/${encodeURIComponent(runId)}/submit`);
export const fetchPrismEvidence = (runId) => getJSON(`/api/prism/runs/${encodeURIComponent(runId)}/evidence`);
export const fetchGraphStatus = () => getJSON('/api/graph/status');
export const fetchCausalGraph = (claimId) => getJSON(`/api/graph/causal/${encodeURIComponent(claimId)}`);

// --- Scenarios / demo data ---
export const fetchScenarios = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return getJSON(`/api/scenarios${qs ? `?${qs}` : ''}`);
};
export const loadDemoDataset = () => postJSON('/api/scenarios/load');

// --- Runs / traces ---
export const fetchRuns = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return getJSON(`/api/runs${qs ? `?${qs}` : ''}`);
};
export const executeClaimAndReport = (params) => {
  const qs = new URLSearchParams(params).toString();
  return postJSON(`/api/runs/execute?${qs}`);
};
export const fetchTraces = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return getJSON(`/api/traces${qs ? `?${qs}` : ''}`);
};

// --- Failures ---
export const fetchFailures = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return getJSON(`/api/failures${qs ? `?${qs}` : ''}`);
};
export const scanForFailures = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return postJSON(`/api/failures/scan${qs ? `?${qs}` : ''}`);
};

// --- Behavior ABI ---
export const fetchAbis = () => getJSON('/api/abis');
export const fetchAbiRules = (abiVersion) => getJSON(`/api/abis/${encodeURIComponent(abiVersion)}/rules`);

// --- Hardening ---
export const fetchHardeningLadders = () => getJSON('/api/hardening/ladders');
export const fetchHardeningResults = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return getJSON(`/api/hardening/results${qs ? `?${qs}` : ''}`);
};

// --- Regression ---
export const fetchRegressions = () => getJSON('/api/regressions');
export const runRegressions = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return postJSON(`/api/regressions/run${qs ? `?${qs}` : ''}`);
};

// --- Metrics ---
export const fetchMetrics = () => getJSON('/api/metrics');
export const computeMetrics = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return postJSON(`/api/metrics/compute${qs ? `?${qs}` : ''}`);
};

// --- Customer Portal (FairClaim) ---
export const fetchSampleClaims = () => getJSON('/api/demo/claims');
export const fetchFairnessGroups = () => getJSON('/api/demo/fairness-groups');
export const fetchFairnessGroupVariants = (groupId) => getJSON(`/api/demo/fairness-groups/${encodeURIComponent(groupId)}/variants`);
export const submitClaim = ({ claimId, protected: isProtected }) =>
  postJSON(`/api/demo/submit?claim_id=${encodeURIComponent(claimId)}&protected=${isProtected}`);
export const resolveImageUrl = (path) => (path ? `${API_BASE_URL}${path}` : null);

export const fetchClaimOptions = () => getJSON('/api/demo/claim-options');
export const submitCustomClaim = async (formValues) => {
  const formData = new FormData();
  Object.entries(formValues).forEach(([key, value]) => {
    if (value !== null && value !== undefined) formData.append(key, value);
  });
  const response = await fetch(`${API_BASE_URL}/api/demo/claims/custom`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`POST /api/demo/claims/custom failed with status: ${response.status}`);
  }
  return response.json();
};

// --- Release Gate ---
export const fetchGateResults = () => getJSON('/api/gates');
export const runReleaseGate = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return postJSON(`/api/gates/run${qs ? `?${qs}` : ''}`);
};

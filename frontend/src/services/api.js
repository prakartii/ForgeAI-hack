/**
 * API Service Layer for FailureFoundry.
 * Talks to FastAPI backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Fetch real backend health and connectivity status.
 */
export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

/**
 * Fetch list of registered agents.
 */
export async function fetchAgents() {
  const response = await fetch(`${API_BASE_URL}/api/agents`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch agents: ${response.status}`);
  }
  return response.json();
}

/**
 * Fetch loaded Behavior ABIs.
 */
export async function fetchAbis() {
  const response = await fetch(`${API_BASE_URL}/api/abis`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch ABIs: ${response.status}`);
  }
  return response.json();
}

/**
 * Fetch PRISM connection status.
 */
export async function fetchPrismStatus() {
  const response = await fetch(`${API_BASE_URL}/api/prism/status`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch PRISM status: ${response.status}`);
  }
  return response.json();
}

/**
 * Fetch hardening challenge ladders.
 */
export async function fetchHardeningLadders() {
  const response = await fetch(`${API_BASE_URL}/api/hardening/ladders`, {
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch hardening ladders: ${response.status}`);
  }
  return response.json();
}

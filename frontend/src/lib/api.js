const API_BASE = '/api';

export async function getDashboard() {
  const res = await fetch(`${API_BASE}/dashboard`);
  if (!res.ok) throw new Error('Failed to fetch dashboard');
  return res.json();
}

export async function runCycle() {
  const res = await fetch(`${API_BASE}/run-cycle`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run cycle');
  return res.json();
}

export async function getActivity(full = false) {
  const url = full ? `${API_BASE}/activity?full=true` : `${API_BASE}/activity`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch activity');
  return res.json();
}

export async function getVoiceAlert(text) {
  const res = await fetch(`${API_BASE}/voice-alert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Failed to get voice alert');
  return res.json();
}

export function getActivityWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return new WebSocket(`${protocol}//${host}/ws/activity`);
}

export async function getVendorNegotiation() {
  const res = await fetch(`${API_BASE}/vendor-negotiation`);
  if (!res.ok) throw new Error('Failed to fetch vendor negotiation');
  return res.json();
}

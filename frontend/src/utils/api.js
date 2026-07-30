const BASE_URL = 'http://localhost:8002/api';

export async function getStatus() {
  const res = await fetch(`${BASE_URL}/status`);
  if (!res.ok) throw new Error('Failed to fetch system status.');
  return res.json();
}

export async function saveConfig(config) {
  const res = await fetch(`${BASE_URL}/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to save config.');
  }
  return res.json();
}

export async function getAuthUrl(scopeMode = 'openid') {
  const res = await fetch(`${BASE_URL}/auth-url?redirect_back=${encodeURIComponent(window.location.origin)}&scope_mode=${scopeMode}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to retrieve auth URL.');
  }
  return res.json();
}

export async function logout() {
  const res = await fetch(`${BASE_URL}/auth/logout`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to logout.');
  return res.json();
}

export async function generateDraft(topic, commentary = null, cardText = null) {
  const res = await fetch(`${BASE_URL}/generate-draft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, commentary, card_text: cardText })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to generate draft.');
  }
  return res.json();
}

export async function publishAdhoc(commentary, cardText) {
  const res = await fetch(`${BASE_URL}/publish-adhoc`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ commentary, card_text: cardText })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to publish post.');
  }
  return res.json();
}

export async function getSchedules() {
  const res = await fetch(`${BASE_URL}/schedules`);
  if (!res.ok) throw new Error('Failed to fetch schedules.');
  return res.json();
}

export async function createSchedule(topic, scheduledTime, commentary = null, cardText = null) {
  const res = await fetch(`${BASE_URL}/schedules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, scheduled_time: scheduledTime, commentary, card_text: cardText })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to create schedule.');
  }
  return res.json();
}

export async function updateSchedule(id, scheduledTime, commentary, cardText) {
  const res = await fetch(`${BASE_URL}/schedules/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scheduled_time: scheduledTime, commentary, card_text: cardText })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to update schedule.');
  }
  return res.json();
}

export async function toggleSchedule(id) {
  const res = await fetch(`${BASE_URL}/schedules/${id}/toggle`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to toggle schedule.');
  }
  return res.json();
}

export async function deleteSchedule(id) {
  const res = await fetch(`${BASE_URL}/schedules/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to delete schedule.');
  }
  return res.json();
}

export async function getLogs() {
  const res = await fetch(`${BASE_URL}/logs`);
  if (!res.ok) throw new Error('Failed to fetch logs.');
  return res.json();
}

export async function clearLogs() {
  const res = await fetch(`${BASE_URL}/logs/clear`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to clear logs.');
  return res.json();
}

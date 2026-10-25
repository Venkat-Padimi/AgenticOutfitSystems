import assert from 'node:assert';
import test from 'node:test';

// Verify URL resolution logic matching mobile/src/api/client.ts
function resolveBaseUrl(envUrl, platform) {
  if (envUrl && envUrl.trim().length > 0) {
    return envUrl.trim().replace(/\/+$/, '');
  }
  if (platform === 'android') {
    return 'http://10.0.2.2:8000';
  }
  return 'http://localhost:8000';
}

test('Base URL resolution with EXPO_PUBLIC_API_BASE_URL', () => {
  assert.strictEqual(
    resolveBaseUrl('http://192.168.1.50:8000/', 'android'),
    'http://192.168.1.50:8000'
  );
  assert.strictEqual(
    resolveBaseUrl('https://api.myfashionagent.com///', 'ios'),
    'https://api.myfashionagent.com'
  );
});

test('Base URL platform fallback defaults', () => {
  assert.strictEqual(resolveBaseUrl(undefined, 'android'), 'http://10.0.2.2:8000');
  assert.strictEqual(resolveBaseUrl('', 'ios'), 'http://localhost:8000');
  assert.strictEqual(resolveBaseUrl(null, 'web'), 'http://localhost:8000');
});

test('Backend live health check', async () => {
  const res = await fetch('http://127.0.0.1:8000/health');
  assert.strictEqual(res.status, 200);
  const data = await res.json();
  assert.strictEqual(data.status, 'healthy');
  assert.strictEqual(typeof data.gemini_configured, 'boolean');
  assert.strictEqual(typeof data.serpapi_configured, 'boolean');
});

test('Backend outfit assembly with controlled fixture scenario', async () => {
  const payload = {
    occasion: 'College Farewell',
    theme: 'Smart Casual',
    gender: 'men',
    budget_inr: 5000,
    force_test_fixture: 'budget_overrun_scenario',
  };

  const res = await fetch('http://127.0.0.1:8000/api/v1/agent/outfit/assemble', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  assert.strictEqual(res.status, 200);
  const data = await res.json();
  assert.ok(data.outfit_id);
  assert.ok(Array.isArray(data.items));
  assert.strictEqual(data.items.length, 3);
  assert.strictEqual(data.data_source_mode, 'controlled_fixture');
  assert.ok(data.trace_steps.length >= 6);
  assert.strictEqual(data.is_within_budget, true);
});

test('Backend rejects missing required fields with 422 Unprocessable Entity', async () => {
  // Missing required 'occasion' and 'theme'
  const payload = {
    gender: 'men',
    budget_inr: 5000,
  };

  const res = await fetch('http://127.0.0.1:8000/api/v1/agent/outfit/assemble', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  assert.strictEqual(res.status, 422);
  const data = await res.json();
  assert.ok(data.detail);
  assert.ok(Array.isArray(data.detail));
});

test('Blend room creation and coordination flow', async () => {
  // Create room
  const createPayload = {
    title: 'Unit Test Farewell Gala',
    occasion: 'Graduation',
    shared_theme: 'Minimalist Chic',
    shared_palette: ['Navy', 'Gold'],
    host_name: 'TestHost',
    host_budget_inr: 5000,
    host_gender: 'men',
  };

  const createRes = await fetch('http://127.0.0.1:8000/api/v1/blend/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(createPayload),
  });
  assert.strictEqual(createRes.status, 200);
  const room = await createRes.json();
  assert.ok(room.blend_id);
  assert.strictEqual(room.members.length, 1);

  // Coordinate blend
  const coordRes = await fetch(`http://127.0.0.1:8000/api/v1/blend/${room.blend_id}/coordinate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  assert.strictEqual(coordRes.status, 200);
  const coordRoom = await coordRes.json();
  assert.ok(coordRoom.harmonization_summary);
  assert.ok(coordRoom.members[0].recommended_outfit);
});

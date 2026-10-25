import { OutfitRecommendation, BlendSession, AgentTraceStep } from '../types';

// Default to local backend; can be changed to LAN IP (e.g. 192.168.1.X) when testing on Expo Go physical device
export const API_BASE_URL = 'http://localhost:8000';

export async function checkBackendHealth(): Promise<{ healthy: boolean; details?: any }> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { method: 'GET' });
    if (res.ok) {
      const data = await res.json();
      return { healthy: true, details: data };
    }
  } catch (e) {
    // Backend may not be running yet
  }
  return { healthy: false };
}

export async function assembleOutfit(params: {
  occasion: string;
  theme: string;
  gender: string;
  budget_inr: number;
  personal_style?: string;
  sizes?: Record<string, string>;
  force_test_fixture?: string;
}): Promise<OutfitRecommendation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/outfit/assemble`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`Failed to assemble outfit: ${response.statusText}`);
  }

  return await response.json();
}

export async function submitUserFeedback(params: {
  outfit_id: string;
  accepted: boolean;
  rejected_item_ids: string[];
  feedback_text: string;
}): Promise<OutfitRecommendation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/outfit/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`Failed to submit feedback: ${response.statusText}`);
  }

  return await response.json();
}

export async function createBlend(params: {
  title: string;
  occasion: string;
  shared_theme: string;
  shared_palette: string[];
  host_name: string;
  host_budget_inr: number;
  host_gender: string;
}): Promise<BlendSession> {
  const response = await fetch(`${API_BASE_URL}/api/v1/blend/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`Failed to create blend: ${response.statusText}`);
  }

  return await response.json();
}

export async function joinBlend(params: {
  blend_id: string;
  member_name: string;
  member_budget_inr: number;
  member_style: string;
  member_gender: string;
}): Promise<BlendSession> {
  const response = await fetch(`${API_BASE_URL}/api/v1/blend/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`Failed to join blend: ${response.statusText}`);
  }

  return await response.json();
}

export async function coordinateBlend(blendId: string): Promise<BlendSession> {
  const response = await fetch(`${API_BASE_URL}/api/v1/blend/${blendId}/coordinate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to coordinate blend: ${response.statusText}`);
  }

  return await response.json();
}

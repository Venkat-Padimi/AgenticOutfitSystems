import { Platform } from 'react-native';
import { OutfitRecommendation, BlendSession, AgentTraceStep } from '../types';

/**
 * Resolves the backend base URL dynamically:
 * 1. Reads `process.env.EXPO_PUBLIC_API_BASE_URL` if defined.
 * 2. On Android emulator: defaults to `http://10.0.2.2:8000` (host loopback alias).
 * 3. On iOS simulator or Web: defaults to `http://localhost:8000`.
 * 4. Physical phones running Expo Go need EXPO_PUBLIC_API_BASE_URL set to host machine LAN IP.
 */
export function getApiBaseUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (envUrl && envUrl.trim().length > 0) {
    return envUrl.trim().replace(/\/+$/, '');
  }
  if (Platform.OS === 'android') {
    // Default to active computer LAN IP for physical device testing; 10.0.2.2 is only for emulators
    return 'http://192.168.0.156:8000';
  }
  return 'http://localhost:8000';
}

export const API_BASE_URL = getApiBaseUrl();

/**
 * Helper to execute fetch with timeout and clear error extraction.
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = 90000
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s. Backend agent may still be executing or unreachable.`);
    }
    throw new Error(err?.message || 'Network request failed. Is the FastAPI backend running on ' + getApiBaseUrl() + '?');
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Parse JSON safely from error responses or fall back to statusText.
 */
async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === 'string') {
      return data.detail;
    }
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join(', ');
    }
    if (data.message) {
      return data.message;
    }
    return JSON.stringify(data);
  } catch {
    return response.statusText || `HTTP ${response.status}`;
  }
}

export interface BackendHealthResponse {
  healthy: boolean;
  status?: string;
  provider_mode?: string;
  serpapi_configured?: boolean;
  gemini_configured?: boolean;
  error?: string;
}

export async function checkBackendHealth(): Promise<BackendHealthResponse> {
  try {
    const baseUrl = getApiBaseUrl();
    const res = await fetchWithTimeout(`${baseUrl}/health`, { method: 'GET' }, 5000);
    if (res.ok) {
      const data = await res.json();
      return {
        healthy: data.status === 'healthy',
        status: data.status,
        provider_mode: data.provider_mode,
        serpapi_configured: data.serpapi_configured,
        gemini_configured: data.gemini_configured,
      };
    }
    const errorMsg = await extractErrorMessage(res);
    return { healthy: false, error: errorMsg };
  } catch (e: any) {
    return { healthy: false, error: e?.message || 'Backend unreachable' };
  }
}

export interface AssembleOutfitParams {
  occasion: string;
  theme: string;
  gender: string;
  budget_inr: number;
  personal_style?: string;
  sizes?: Record<string, string>;
  color_preferences?: string[];
  delivery_deadline_days?: number;
  force_test_fixture?: string;
}

export async function assembleOutfit(params: AssembleOutfitParams): Promise<OutfitRecommendation> {
  const baseUrl = getApiBaseUrl();
  const response = await fetchWithTimeout(
    `${baseUrl}/api/v1/agent/outfit/assemble`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    },
    90000 // 90s agent execution budget
  );

  if (!response.ok) {
    const errorMsg = await extractErrorMessage(response);
    throw new Error(`Failed to assemble outfit: ${errorMsg}`);
  }

  return await response.json();
}

export async function submitUserFeedback(params: {
  outfit_id: string;
  accepted: boolean;
  rejected_item_ids: string[];
  feedback_text: string;
}): Promise<OutfitRecommendation> {
  const baseUrl = getApiBaseUrl();
  const response = await fetchWithTimeout(
    `${baseUrl}/api/v1/agent/outfit/feedback`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    },
    60000
  );

  if (!response.ok) {
    const errorMsg = await extractErrorMessage(response);
    throw new Error(`Failed to submit feedback: ${errorMsg}`);
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
  const baseUrl = getApiBaseUrl();
  const response = await fetchWithTimeout(
    `${baseUrl}/api/v1/blend/create`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    },
    30000
  );

  if (!response.ok) {
    const errorMsg = await extractErrorMessage(response);
    throw new Error(`Failed to create blend: ${errorMsg}`);
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
  const baseUrl = getApiBaseUrl();
  const response = await fetchWithTimeout(
    `${baseUrl}/api/v1/blend/join`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    },
    30000
  );

  if (!response.ok) {
    const errorMsg = await extractErrorMessage(response);
    throw new Error(`Failed to join blend: ${errorMsg}`);
  }

  return await response.json();
}

export async function coordinateBlend(
  blendId: string,
  forceFixture?: string
): Promise<BlendSession> {
  const baseUrl = getApiBaseUrl();
  const url = forceFixture
    ? `${baseUrl}/api/v1/blend/${blendId}/coordinate?force_fixture=${encodeURIComponent(forceFixture)}`
    : `${baseUrl}/api/v1/blend/${blendId}/coordinate`;

  const response = await fetchWithTimeout(
    url,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    },
    90000
  );

  if (!response.ok) {
    const errorMsg = await extractErrorMessage(response);
    throw new Error(`Failed to coordinate blend: ${errorMsg}`);
  }

  return await response.json();
}

export async function swapBlendItem(params: {
  blend_id: string;
  member_id: string;
  rejected_item_id: string;
  feedback_text?: string;
  target_category?: string;
  force_fixture?: string;
}): Promise<BlendSession> {
  const baseUrl = getApiBaseUrl();
  const url = params.force_fixture
    ? `${baseUrl}/api/v1/blend/swap?force_fixture=${encodeURIComponent(params.force_fixture)}`
    : `${baseUrl}/api/v1/blend/swap`;

  const response = await fetchWithTimeout(
    url,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    },
    60000
  );

  if (!response.ok) {
    const errorMsg = await extractErrorMessage(response);
    throw new Error(`Failed to swap item: ${errorMsg}`);
  }

  return await response.json();
}


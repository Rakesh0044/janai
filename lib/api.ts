// API service layer.
// The frontend consumes backend responses exactly as returned — no scoring
// logic (Module 3/4 calculations) is duplicated here.

import {
  CitizenRequest,
  CityInsightRecord,
  DashboardSummary,
  ExplanationInsight,
} from "@/types";
import {
  MOCK_CITIZEN_REQUEST,
  MOCK_DASHBOARD_SUMMARY,
  MOCK_EXPLANATION,
  MOCK_INSIGHTS,
} from "./mockData";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";
const FORCE_DEMO = process.env.NEXT_PUBLIC_FORCE_DEMO_MODE === "true";

export interface ApiResult<T> {
  data: T;
  demoMode: boolean;
  error?: string;
}

async function safeFetch<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_BASE_URL) throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured");
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    throw new Error(`Backend responded with ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ---- Module 1/2: submit a citizen request (text) and get structured understanding ----
export async function submitCitizenRequestText(
  text: string
): Promise<ApiResult<CitizenRequest>> {
  if (FORCE_DEMO) {
    return { data: { ...MOCK_CITIZEN_REQUEST, original_text: text }, demoMode: true };
  }
  try {
    const data = await safeFetch<CitizenRequest>("/api/citizen-request", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    return { data, demoMode: false };
  } catch (err) {
    return {
      data: { ...MOCK_CITIZEN_REQUEST, original_text: text },
      demoMode: true,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}

// ---- Module 2: submit a voice recording ----
export async function submitCitizenRequestVoice(
  audioBlob: Blob
): Promise<ApiResult<CitizenRequest>> {
  if (FORCE_DEMO) {
    return { data: MOCK_CITIZEN_REQUEST, demoMode: true };
  }
  try {
    const form = new FormData();
    form.append("audio", audioBlob, "recording.webm");
    if (!API_BASE_URL) throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured");
    const res = await fetch(`${API_BASE_URL}/api/citizen-request/voice`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error(`Backend responded with ${res.status}`);
    const data = (await res.json()) as CitizenRequest;
    return { data, demoMode: false };
  } catch (err) {
    return {
      data: MOCK_CITIZEN_REQUEST,
      demoMode: true,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}

// ---- Module 3/4 combined: development priority insights across cities ----
export async function getInsights(): Promise<ApiResult<CityInsightRecord[]>> {
  if (FORCE_DEMO) return { data: MOCK_INSIGHTS, demoMode: true };
  try {
    const data = await safeFetch<CityInsightRecord[]>("/api/insights");
    return { data, demoMode: false };
  } catch (err) {
    return {
      data: MOCK_INSIGHTS,
      demoMode: true,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}

// ---- Dashboard summary (aggregated by backend) ----
export async function getDashboardSummary(): Promise<ApiResult<DashboardSummary>> {
  if (FORCE_DEMO) return { data: MOCK_DASHBOARD_SUMMARY, demoMode: true };
  try {
    const data = await safeFetch<DashboardSummary>("/api/dashboard-summary");
    return { data, demoMode: false };
  } catch (err) {
    return {
      data: MOCK_DASHBOARD_SUMMARY,
      demoMode: true,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}

// ---- Module 5: AI explanation for a specific city + category ----
export async function getExplanation(
  city: string,
  category: string
): Promise<ApiResult<ExplanationInsight>> {
  if (FORCE_DEMO) return { data: MOCK_EXPLANATION, demoMode: true };
  try {
    const data = await safeFetch<ExplanationInsight>(
      `/api/explanation?city=${encodeURIComponent(city)}&category=${encodeURIComponent(category)}`
    );
    return { data, demoMode: false };
  } catch (err) {
    return {
      data: MOCK_EXPLANATION,
      demoMode: true,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}

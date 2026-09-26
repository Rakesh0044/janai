// TypeScript interfaces mirroring the existing Python/Pydantic backend schemas.
// Do NOT add fields here that the backend does not produce, and do NOT
// recompute any of these numbers on the frontend.

export type SupportedLanguage = "Kannada" | "Telugu" | "Malayalam" | "English";

export type PrototypeState = "Karnataka" | "Andhra Pradesh" | "Kerala";

export type PriorityBand = "LOW" | "MODERATE" | "HIGH";

// ---- Module 1: Multilingual Citizen Request Understanding ----
export interface CitizenRequest {
  original_text: string;
  language: string;
  state: string;
  district_or_city: string | null;
  category: string;
  subcategory: string;
  problem: string;
  duration: string | null;
  affected_population: number | null;
  severity: number | null;
  urgency: string;
  normalized_summary: string;
  keywords: string[];
  confidence: number;
}

// ---- Module 2: Voice input state machine (frontend-only UI state) ----
export type VoiceState =
  | "idle"
  | "recording"
  | "processing"
  | "transcribing"
  | "completed"
  | "error";

// ---- Module 3: Demand Aggregation & Hotspot Detection ----
export interface DemandInsight {
  city: string;
  state: string;
  category: string;
  request_count: number;
  average_severity: number;
  high_severity_count: number;
  demand_score: number;
  hotspot_status: PriorityBand;
  reason: string;
}

// ---- Module 4: Infrastructure & Context Analysis (numerical source of truth) ----
export interface ContextInsight {
  city: string;
  state: string;
  category: string;
  citizen_demand_score: number;
  infrastructure_condition: number;
  service_capacity: number;
  population_pressure: number;
  context_gap_score: number;
  development_priority_score: number;
  priority_band: PriorityBand;
}

// ---- Module 5: AI Explanation Layer ----
export interface ExplanationInsight {
  city: string;
  state: string;
  category: string;
  priority_band: PriorityBand;
  development_priority_score: number;
  explanation: string;
  key_factors: string[];
  data_note: string;
  confidence: number;
}

// Composite record used by dashboard / map / insights table views
export interface CityInsightRecord extends ContextInsight {
  request_count: number;
  explanation?: string;
}

export interface DashboardSummary {
  total_requests: number;
  active_hotspots: number;
  high_priority_insights: number;
  cities_covered: number;
  category_distribution: { category: string; count: number }[];
  state_distribution: { state: string; count: number }[];
  hotspot_distribution: { band: PriorityBand; count: number }[];
}

export interface CityCoordinates {
  city: string;
  state: string;
  lat: number;
  lng: number;
}

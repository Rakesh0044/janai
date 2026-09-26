// SYNTHETIC DEMO DATA
// Used only when the backend is unreachable or NEXT_PUBLIC_FORCE_DEMO_MODE=true.
// Shapes must stay identical to what the real backend returns from Modules 1, 3, 4 and 5.

import {
  CitizenRequest,
  CityCoordinates,
  CityInsightRecord,
  DashboardSummary,
  ExplanationInsight,
} from "@/types";

export const CITY_COORDINATES: CityCoordinates[] = [
  { city: "Bengaluru", state: "Karnataka", lat: 12.9716, lng: 77.5946 },
  { city: "Mysuru", state: "Karnataka", lat: 12.2958, lng: 76.6394 },
  { city: "Hubballi", state: "Karnataka", lat: 15.3647, lng: 75.124 },
  { city: "Belagavi", state: "Karnataka", lat: 15.8497, lng: 74.4977 },
  { city: "Vijayawada", state: "Andhra Pradesh", lat: 16.5062, lng: 80.648 },
  { city: "Visakhapatnam", state: "Andhra Pradesh", lat: 17.6868, lng: 83.2185 },
  { city: "Tirupati", state: "Andhra Pradesh", lat: 13.6288, lng: 79.4192 },
  { city: "Kochi", state: "Kerala", lat: 9.9312, lng: 76.2673 },
  { city: "Thiruvananthapuram", state: "Kerala", lat: 8.5241, lng: 76.9366 },
  { city: "Kozhikode", state: "Kerala", lat: 11.2588, lng: 75.7804 },
];

function band(score: number): "LOW" | "MODERATE" | "HIGH" {
  if (score >= 70) return "HIGH";
  if (score >= 40) return "MODERATE";
  return "LOW";
}

const RAW: Omit<CityInsightRecord, "priority_band">[] = [
  { city: "Vijayawada", state: "Andhra Pradesh", category: "Sanitation", citizen_demand_score: 89.5, infrastructure_condition: 50, service_capacity: 41, population_pressure: 95, context_gap_score: 64.4, development_priority_score: 79.5, request_count: 214 },
  { city: "Bengaluru", state: "Karnataka", category: "Water Supply", citizen_demand_score: 82.1, infrastructure_condition: 58, service_capacity: 52, population_pressure: 91, context_gap_score: 58.7, development_priority_score: 72.7, request_count: 388 },
  { city: "Kochi", state: "Kerala", category: "Waste Management", citizen_demand_score: 76.4, infrastructure_condition: 61, service_capacity: 55, population_pressure: 68, context_gap_score: 51.7, development_priority_score: 66.5, request_count: 165 },
  { city: "Mysuru", state: "Karnataka", category: "Roads & Transport", citizen_demand_score: 61.2, infrastructure_condition: 66, service_capacity: 60, population_pressure: 54, context_gap_score: 41.6, development_priority_score: 53.4, request_count: 97 },
  { city: "Visakhapatnam", state: "Andhra Pradesh", category: "Water Supply", citizen_demand_score: 70.8, infrastructure_condition: 63, service_capacity: 59, population_pressure: 72, context_gap_score: 45.4, development_priority_score: 60.6, request_count: 142 },
  { city: "Thiruvananthapuram", state: "Kerala", category: "Public Health", citizen_demand_score: 55.3, infrastructure_condition: 70, service_capacity: 67, population_pressure: 49, context_gap_score: 34.9, development_priority_score: 47.1, request_count: 78 },
  { city: "Hubballi", state: "Karnataka", category: "Electricity", citizen_demand_score: 48.9, infrastructure_condition: 72, service_capacity: 69, population_pressure: 45, context_gap_score: 32.4, development_priority_score: 42.3, request_count: 61 },
  { city: "Tirupati", state: "Andhra Pradesh", category: "Sanitation", citizen_demand_score: 39.6, infrastructure_condition: 78, service_capacity: 74, population_pressure: 38, context_gap_score: 24.9, development_priority_score: 33.7, request_count: 44 },
  { city: "Kozhikode", state: "Kerala", category: "Roads & Transport", citizen_demand_score: 44.2, infrastructure_condition: 75, service_capacity: 71, population_pressure: 41, context_gap_score: 27.6, development_priority_score: 37.5, request_count: 53 },
  { city: "Belagavi", state: "Karnataka", category: "Water Supply", citizen_demand_score: 33.1, infrastructure_condition: 81, service_capacity: 77, population_pressure: 30, context_gap_score: 19.7, development_priority_score: 27.7, request_count: 29 },
];

export const MOCK_INSIGHTS: CityInsightRecord[] = RAW.map((r) => ({
  ...r,
  priority_band: band(r.development_priority_score),
}));

export const MOCK_DASHBOARD_SUMMARY: DashboardSummary = {
  total_requests: MOCK_INSIGHTS.reduce((s, r) => s + r.request_count, 0),
  active_hotspots: MOCK_INSIGHTS.filter((r) => r.priority_band !== "LOW").length,
  high_priority_insights: MOCK_INSIGHTS.filter((r) => r.priority_band === "HIGH").length,
  cities_covered: new Set(MOCK_INSIGHTS.map((r) => r.city)).size,
  category_distribution: Object.entries(
    MOCK_INSIGHTS.reduce<Record<string, number>>((acc, r) => {
      acc[r.category] = (acc[r.category] || 0) + r.request_count;
      return acc;
    }, {})
  ).map(([category, count]) => ({ category, count })),
  state_distribution: Object.entries(
    MOCK_INSIGHTS.reduce<Record<string, number>>((acc, r) => {
      acc[r.state] = (acc[r.state] || 0) + r.request_count;
      return acc;
    }, {})
  ).map(([state, count]) => ({ state, count })),
  hotspot_distribution: (["LOW", "MODERATE", "HIGH"] as const).map((bandName) => ({
    band: bandName,
    count: MOCK_INSIGHTS.filter((r) => r.priority_band === bandName).length,
  })),
};

export const MOCK_EXPLANATION: ExplanationInsight = {
  city: "Vijayawada",
  state: "Andhra Pradesh",
  category: "Sanitation",
  priority_band: "HIGH",
  development_priority_score: 79.5,
  explanation:
    "The prototype indicates a development priority score of 79.5, driven mainly by a high citizen demand signal and a wide gap between current service capacity and population pressure. Sanitation complaints in this dataset are frequent, severe, and concentrated, which raises both the demand and context components of the score.",
  key_factors: [
    "High citizen demand score (89.5) from repeated, severe complaints",
    "Population pressure (95) far exceeds current service capacity (41)",
    "Infrastructure condition (50) is rated only moderate",
  ],
  data_note: "Explanation generated from synthetic/demo data for prototype purposes only.",
  confidence: 0.87,
};

export const MOCK_CITIZEN_REQUEST: CitizenRequest = {
  original_text: "ನಮ್ಮ ಪ್ರದೇಶದಲ್ಲಿ ಕುಡಿಯುವ ನೀರಿನ ಪೂರೈಕೆ ಅನಿಯಮಿತವಾಗಿದೆ, ಕಳೆದ ಎರಡು ವಾರಗಳಿಂದ.",
  language: "Kannada",
  state: "Karnataka",
  district_or_city: "Mysuru",
  category: "Water Supply",
  subcategory: "Irregular Supply",
  problem: "Drinking water supply has been irregular for the past two weeks.",
  duration: "2 weeks",
  affected_population: 1200,
  severity: 4,
  urgency: "High",
  normalized_summary:
    "Citizen reports irregular drinking water supply in Mysuru for two weeks, affecting an estimated 1,200 residents.",
  keywords: ["water", "supply", "shortage"],
  confidence: 0.94,
};

"use client";

import { useMemo, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { CityInsightRecord, CityCoordinates, PriorityBand } from "@/types";
import PriorityBadge from "./PriorityBadge";
import { formatScore } from "@/lib/utils";

const BAND_COLOR: Record<PriorityBand, string> = {
  LOW: "#4A9291",
  MODERATE: "#C98A2C",
  HIGH: "#C24D3D",
};

export default function HotspotMapClient({
  insights,
  coordinates,
}: {
  insights: CityInsightRecord[];
  coordinates: CityCoordinates[];
}) {
  const [stateFilter, setStateFilter] = useState("ALL");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [bandFilter, setBandFilter] = useState("ALL");

  const states = useMemo(() => Array.from(new Set(insights.map((i) => i.state))), [insights]);
  const categories = useMemo(() => Array.from(new Set(insights.map((i) => i.category))), [insights]);

  const filtered = insights.filter(
    (i) =>
      (stateFilter === "ALL" || i.state === stateFilter) &&
      (categoryFilter === "ALL" || i.category === categoryFilter) &&
      (bandFilter === "ALL" || i.priority_band === bandFilter)
  );

  function coordsFor(city: string) {
    return coordinates.find((c) => c.city === city);
  }

  return (
    <div>
      <div className="flex flex-wrap gap-3">
        <select
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          className="border border-border bg-surface px-3 py-2 text-sm text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
        >
          <option value="ALL">All states</option>
          {states.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="border border-border bg-surface px-3 py-2 text-sm text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
        >
          <option value="ALL">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select
          value={bandFilter}
          onChange={(e) => setBandFilter(e.target.value)}
          className="border border-border bg-surface px-3 py-2 text-sm text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
        >
          <option value="ALL">All priority bands</option>
          <option value="HIGH">HIGH</option>
          <option value="MODERATE">MODERATE</option>
          <option value="LOW">LOW</option>
        </select>
      </div>

      <div className="mt-4 h-[520px] overflow-hidden border border-border">
        <MapContainer
          center={[14.5, 78]}
          zoom={6}
          scrollWheelZoom
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {filtered.map((insight) => {
            const coords = coordsFor(insight.city);
            if (!coords) return null;
            return (
              <CircleMarker
                key={`${insight.city}-${insight.category}`}
                center={[coords.lat, coords.lng]}
                radius={9}
                pathOptions={{
                  color: BAND_COLOR[insight.priority_band],
                  fillColor: BAND_COLOR[insight.priority_band],
                  fillOpacity: 0.7,
                  weight: 1.5,
                }}
              >
                <Popup>
                  <div className="min-w-[180px]">
                    <p className="font-medium">{insight.city}</p>
                    <p className="text-xs text-muted">{insight.category}</p>
                    <p className="mt-1 text-xs">
                      Demand: <span className="tabular-nums">{formatScore(insight.citizen_demand_score)}</span>
                    </p>
                    <p className="text-xs">
                      Priority: <span className="tabular-nums">{formatScore(insight.development_priority_score)}</span>
                    </p>
                    <div className="mt-2">
                      <PriorityBadge band={insight.priority_band} />
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>

      <p className="mt-3 text-xs text-muted">
        Marker color reflects priority band (LOW / MODERATE / HIGH). This map shows
        prototype demand and priority signals, not verified infrastructure conditions.
      </p>
    </div>
  );
}

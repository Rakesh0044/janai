"use client";

import { useEffect, useMemo, useState } from "react";
import { getExplanation, getInsights } from "@/lib/api";
import { CityInsightRecord, ExplanationInsight } from "@/types";
import PriorityBadge from "@/components/PriorityBadge";
import DemoModeBanner from "@/components/DemoModeBanner";
import InsightCard from "@/components/InsightCard";
import { formatScore } from "@/lib/utils";

type SortKey = "development_priority_score" | "citizen_demand_score" | "request_count";

export default function InsightsPage() {
  const [insights, setInsights] = useState<CityInsightRecord[]>([]);
  const [demoMode, setDemoMode] = useState(false);
  const [query, setQuery] = useState("");
  const [bandFilter, setBandFilter] = useState<string>("ALL");
  const [sortKey, setSortKey] = useState<SortKey>("development_priority_score");
  const [selected, setSelected] = useState<CityInsightRecord | null>(null);
  const [explanation, setExplanation] = useState<ExplanationInsight | undefined>();

  useEffect(() => {
    getInsights().then((res) => {
      setInsights(res.data);
      setDemoMode(res.demoMode);
    });
  }, []);

  const filtered = useMemo(() => {
    return insights
      .filter((r) => (bandFilter === "ALL" ? true : r.priority_band === bandFilter))
      .filter((r) =>
        query.trim()
          ? `${r.city} ${r.state} ${r.category}`.toLowerCase().includes(query.toLowerCase())
          : true
      )
      .sort((a, b) => b[sortKey] - a[sortKey]);
  }, [insights, query, bandFilter, sortKey]);

  async function openInsight(record: CityInsightRecord) {
    setSelected(record);
    setExplanation(undefined);
    const res = await getExplanation(record.city, record.category);
    setExplanation(res.data);
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-14">
      <h1 className="font-display text-3xl text-text">Development Priority Signals</h1>
      <p className="mt-2 max-w-2xl text-muted">
        Highest development priority signals across covered cities and categories —
        not a ranking of "best" or "worst" cities.
      </p>

      <div className="mt-4">
        <DemoModeBanner visible={demoMode} />
      </div>

      <div className="mt-8 flex flex-wrap gap-3">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search city, state or category…"
          className="min-w-[220px] flex-1 border border-border bg-surface px-4 py-2.5 text-sm text-text placeholder:text-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
        />
        <select
          value={bandFilter}
          onChange={(e) => setBandFilter(e.target.value)}
          className="border border-border bg-surface px-3 py-2.5 text-sm text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
        >
          <option value="ALL">All priority bands</option>
          <option value="HIGH">HIGH</option>
          <option value="MODERATE">MODERATE</option>
          <option value="LOW">LOW</option>
        </select>
        <select
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value as SortKey)}
          className="border border-border bg-surface px-3 py-2.5 text-sm text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
        >
          <option value="development_priority_score">Sort: Development Priority</option>
          <option value="citizen_demand_score">Sort: Citizen Demand</option>
          <option value="request_count">Sort: Request Count</option>
        </select>
      </div>

      <div className="mt-6 overflow-x-auto border border-border">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-surface text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-4 py-3">City</th>
              <th className="px-4 py-3">State</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3 text-right">Requests</th>
              <th className="px-4 py-3 text-right">Demand</th>
              <th className="px-4 py-3 text-right">Context Gap</th>
              <th className="px-4 py-3 text-right">Priority</th>
              <th className="px-4 py-3">Band</th>
              <th className="px-4 py-3 sr-only">Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <tr
                key={`${r.city}-${r.category}`}
                className="border-b border-border last:border-0 hover:bg-surface/60"
              >
                <td className="px-4 py-3 text-text">{r.city}</td>
                <td className="px-4 py-3 text-muted">{r.state}</td>
                <td className="px-4 py-3 text-muted">{r.category}</td>
                <td className="px-4 py-3 text-right tabular-nums text-text">{r.request_count}</td>
                <td className="px-4 py-3 text-right tabular-nums text-text">
                  {formatScore(r.citizen_demand_score)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-text">
                  {formatScore(r.context_gap_score)}
                </td>
                <td className="px-4 py-3 text-right tabular-nums font-medium text-text">
                  {formatScore(r.development_priority_score)}
                </td>
                <td className="px-4 py-3">
                  <PriorityBadge band={r.priority_band} />
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => openInsight(r)}
                    className="text-primary-light underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light rounded-sm"
                  >
                    View Insight
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-muted">
                  No signals match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          role="dialog"
          aria-modal="true"
          aria-label={`Insight for ${selected.city}`}
          onClick={() => setSelected(null)}
        >
          <div className="w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
            <InsightCard insight={selected} explanation={explanation} />
            <button
              onClick={() => setSelected(null)}
              className="mt-3 w-full border border-border bg-surface py-2.5 text-sm text-text hover:border-primary-light focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

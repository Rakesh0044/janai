"use client";

import { useState } from "react";
import { CitizenRequest } from "@/types";

export default function AnalysisResult({ result }: { result: CitizenRequest }) {
  const [showRaw, setShowRaw] = useState(false);

  const rows: [string, string][] = [
    ["Language", result.language],
    ["Location", result.district_or_city || result.state],
    ["Category", `${result.category}${result.subcategory ? " — " + result.subcategory : ""}`],
    ["Severity", result.severity != null ? `${result.severity} / 5` : "Not specified"],
    ["Urgency", result.urgency || "Not specified"],
  ];

  return (
    <div className="border border-border bg-surface">
      <div className="border-b border-border px-6 py-4">
        <h3 className="font-display text-lg text-text">AI Understanding</h3>
      </div>
      <div className="grid grid-cols-1 gap-x-8 gap-y-4 px-6 py-5 sm:grid-cols-2">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-baseline justify-between gap-4 border-b border-border/60 pb-2 sm:justify-start">
            <span className="text-sm text-muted">{label}</span>
            <span className="text-sm text-text sm:ml-auto">{value}</span>
          </div>
        ))}
      </div>

      <div className="px-6 pb-5">
        <p className="text-sm text-muted mb-1.5">Problem</p>
        <p className="text-text">"{result.problem}"</p>
      </div>

      {result.keywords.length > 0 && (
        <div className="px-6 pb-5 flex flex-wrap gap-2">
          {result.keywords.map((k) => (
            <span key={k} className="rounded-sm border border-border px-2 py-1 text-xs text-muted">
              {k}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between border-t border-border px-6 py-4">
        <span className="text-sm text-muted">
          Confidence <span className="text-text tabular-nums">{Math.round(result.confidence * 100)}%</span>
        </span>
        <button
          onClick={() => setShowRaw((v) => !v)}
          className="text-sm text-primary-light underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light rounded-sm"
          aria-expanded={showRaw}
        >
          {showRaw ? "Hide structured data" : "View structured data"}
        </button>
      </div>

      {showRaw && (
        <pre className="overflow-x-auto border-t border-border bg-base px-6 py-4 text-xs text-muted">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}

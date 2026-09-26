import { CityInsightRecord, ExplanationInsight } from "@/types";
import PriorityBadge from "./PriorityBadge";
import { formatScore } from "@/lib/utils";

const METRICS: { key: keyof CityInsightRecord; label: string }[] = [
  { key: "citizen_demand_score", label: "Citizen Demand" },
  { key: "context_gap_score", label: "Context Gap" },
  { key: "infrastructure_condition", label: "Infrastructure Condition" },
  { key: "service_capacity", label: "Service Capacity" },
  { key: "population_pressure", label: "Population Pressure" },
];

export default function InsightCard({
  insight,
  explanation,
}: {
  insight: CityInsightRecord;
  explanation?: ExplanationInsight;
}) {
  return (
    <div className="border border-border bg-surface">
      <div className="flex items-start justify-between border-b border-border px-6 py-5">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted">{insight.category}</p>
          <h3 className="font-display text-xl text-text">
            {insight.city}, {insight.state}
          </h3>
        </div>
        <PriorityBadge band={insight.priority_band} />
      </div>

      <div className="flex items-baseline gap-3 px-6 py-6 border-b border-border">
        <span className="text-sm text-muted">Development Priority</span>
        <span className="font-display text-4xl tabular-nums text-text">
          {formatScore(insight.development_priority_score)}
        </span>
      </div>

      <dl className="grid grid-cols-2 gap-x-8 gap-y-4 px-6 py-5 sm:grid-cols-3">
        {METRICS.map((m) => (
          <div key={m.key as string}>
            <dt className="text-xs text-muted">{m.label}</dt>
            <dd className="mt-0.5 tabular-nums text-text">
              {formatScore(insight[m.key] as number)}
            </dd>
          </div>
        ))}
      </dl>

      {explanation && (
        <div className="border-t border-border px-6 py-5">
          <p className="text-sm font-medium text-text mb-2">Why this insight?</p>
          <p className="text-sm text-muted leading-relaxed">{explanation.explanation}</p>
          {explanation.key_factors.length > 0 && (
            <ul className="mt-3 space-y-1.5">
              {explanation.key_factors.map((f) => (
                <li key={f} className="flex gap-2 text-sm text-muted">
                  <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-primary-light" aria-hidden="true" />
                  {f}
                </li>
              ))}
            </ul>
          )}
          <p className="mt-4 text-xs text-accent">{explanation.data_note}</p>
        </div>
      )}
    </div>
  );
}

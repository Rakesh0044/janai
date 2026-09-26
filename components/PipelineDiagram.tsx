const STEPS = [
  { title: "Citizen Voice", detail: "Text or voice, in Kannada, Telugu, Malayalam or English" },
  { title: "AI Understanding", detail: "Structured category, severity and urgency extracted" },
  { title: "Demand Intelligence", detail: "Requests aggregated into city-level demand scores" },
  { title: "Development Insight", detail: "Context-weighted priority score, explained in plain language" },
];

export default function PipelineDiagram() {
  return (
    <ol className="relative flex flex-col gap-0" aria-label="How JanDrishti AI processes a request">
      {STEPS.map((step, i) => (
        <li key={step.title} className="relative flex gap-4 pb-8 last:pb-0">
          {i < STEPS.length - 1 && (
            <span
              className="absolute left-[15px] top-8 h-full w-px bg-border"
              aria-hidden="true"
            />
          )}
          <span className="relative z-10 mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-primary-light bg-surface text-sm font-medium text-primary-light">
            {i + 1}
          </span>
          <div>
            <p className="font-medium text-text">{step.title}</p>
            <p className="mt-0.5 text-sm text-muted">{step.detail}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

import Link from "next/link";
import PipelineDiagram from "@/components/PipelineDiagram";

export default function LandingPage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-16 md:py-24">
      <div className="grid gap-16 md:grid-cols-2 md:gap-12">
        <div>
          <h1 className="font-display text-4xl leading-tight text-text md:text-5xl">
            Turning citizen voices into development intelligence.
          </h1>
          <p className="mt-6 max-w-md text-muted leading-relaxed">
            An AI-powered development intelligence platform that transforms
            multilingual citizen requests into structured demand insights and
            contextual development signals.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/dashboard"
              className="rounded-sm bg-primary px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-primary-light focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
            >
              Explore Development Insights
            </Link>
            <Link
              href="/citizen-request"
              className="rounded-sm border border-border px-5 py-3 text-sm font-medium text-text transition-colors hover:border-primary-light focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
            >
              Submit a Citizen Request
            </Link>
          </div>
          <p className="mt-10 text-xs text-muted max-w-md">
            Prototype insight platform. Scores are calculated from synthetic/demo
            data and are not official government infrastructure measurements.
          </p>
        </div>

        <div className="border border-border bg-surface p-8">
          <p className="mb-6 text-xs uppercase tracking-wide text-muted">How it works</p>
          <PipelineDiagram />
        </div>
      </div>
    </div>
  );
}

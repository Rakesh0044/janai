"use client";

import { useState } from "react";
import RequestForm from "@/components/RequestForm";
import AnalysisResult from "@/components/AnalysisResult";
import DemoModeBanner from "@/components/DemoModeBanner";
import { submitCitizenRequestText, submitCitizenRequestVoice } from "@/lib/api";
import { CitizenRequest } from "@/types";

type Stage = "idle" | "understanding" | "done";

export default function CitizenRequestPage() {
  const [result, setResult] = useState<CitizenRequest | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [stage, setStage] = useState<Stage>("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleText(text: string) {
    setStage("understanding");
    setError(null);
    try {
      const res = await submitCitizenRequestText(text);
      setResult(res.data);
      setDemoMode(res.demoMode);
    } catch {
      setError("We couldn't process that request. Please try again.");
    } finally {
      setStage("done");
    }
  }

  async function handleVoice(blob: Blob) {
    setStage("understanding");
    setError(null);
    try {
      const res = await submitCitizenRequestVoice(blob);
      setResult(res.data);
      setDemoMode(res.demoMode);
    } catch {
      setError("We couldn't transcribe that recording. Please try again.");
      throw new Error("voice failed");
    } finally {
      setStage("done");
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-14">
      <h1 className="font-display text-3xl text-text">Share a Development Concern</h1>
      <p className="mt-2 text-muted">Describe a local development issue in your own language.</p>

      <div className="mt-8">
        <RequestForm
          onSubmitText={handleText}
          onSubmitVoice={handleVoice}
          submitting={stage === "understanding"}
        />
      </div>

      {stage === "understanding" && (
        <div className="mt-8 space-y-2 text-sm text-muted" role="status">
          <p>Understanding request…</p>
          <p>Analyzing demand…</p>
          <p>Preparing insight…</p>
        </div>
      )}

      {error && (
        <p className="mt-6 border border-high/40 bg-high/10 px-4 py-3 text-sm text-high">{error}</p>
      )}

      {result && stage === "done" && (
        <div className="mt-8 space-y-4">
          <DemoModeBanner visible={demoMode} />
          <AnalysisResult result={result} />
        </div>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { cx } from "@/lib/utils";
import VoiceRecorder from "./VoiceRecorder";

const LANGUAGES = ["Kannada", "Telugu", "Malayalam", "English"];

export default function RequestForm({
  onSubmitText,
  onSubmitVoice,
  submitting,
}: {
  onSubmitText: (text: string) => void;
  onSubmitVoice: (blob: Blob) => Promise<void>;
  submitting: boolean;
}) {
  const [mode, setMode] = useState<"text" | "voice">("text");
  const [text, setText] = useState("");

  return (
    <div className="border border-border bg-surface">
      <div className="flex border-b border-border" role="tablist" aria-label="Input method">
        {(["text", "voice"] as const).map((m) => (
          <button
            key={m}
            role="tab"
            aria-selected={mode === m}
            onClick={() => setMode(m)}
            className={cx(
              "flex-1 px-4 py-3 text-sm font-medium capitalize transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light",
              mode === m ? "bg-base text-text" : "text-muted hover:text-text"
            )}
          >
            {m}
          </button>
        ))}
      </div>

      <div className="p-6">
        {mode === "text" ? (
          <>
            <label htmlFor="citizen-text" className="sr-only">
              Describe a development issue
            </label>
            <textarea
              id="citizen-text"
              rows={6}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Tell us about a development issue in your area..."
              className="w-full resize-none border border-border bg-base p-4 text-text placeholder:text-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
            />
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                {LANGUAGES.map((lang) => (
                  <span key={lang} className="rounded-sm border border-border px-2 py-1 text-xs text-muted">
                    {lang}
                  </span>
                ))}
              </div>
              <button
                onClick={() => text.trim() && onSubmitText(text.trim())}
                disabled={!text.trim() || submitting}
                className="rounded-sm bg-primary px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-light disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light"
              >
                {submitting ? "Analyzing…" : "Analyze Request"}
              </button>
            </div>
            <p className="mt-2 text-xs text-muted">
              Language is detected automatically — no need to select one.
            </p>
          </>
        ) : (
          <VoiceRecorder onComplete={onSubmitVoice} />
        )}
      </div>
    </div>
  );
}

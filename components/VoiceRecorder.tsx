"use client";

import { useRef, useState } from "react";
import { VoiceState } from "@/types";
import { cx } from "@/lib/utils";

const STATE_LABEL: Record<VoiceState, string> = {
  idle: "Tap to record",
  recording: "Listening… tap to stop",
  processing: "Processing audio",
  transcribing: "Transcribing speech",
  completed: "Recording captured",
  error: "Something went wrong",
};

export default function VoiceRecorder({
  onComplete,
}: {
  onComplete: (blob: Blob) => void;
}) {
  const [state, setState] = useState<VoiceState>("idle");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        setState("processing");
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());
        setState("transcribing");
        try {
          await onComplete(blob);
          setState("completed");
        } catch {
          setState("error");
        }
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setState("recording");
    } catch {
      setState("error");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
  }

  const isRecording = state === "recording";
  const isBusy = state === "processing" || state === "transcribing";

  return (
    <div className="flex flex-col items-center gap-4 py-6">
      <button
        type="button"
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isBusy}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
        aria-pressed={isRecording}
        className={cx(
          "relative flex h-20 w-20 items-center justify-center rounded-full border transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-light disabled:opacity-60",
          isRecording ? "border-high bg-high/15" : "border-primary-light bg-primary/15 hover:bg-primary/25"
        )}
      >
        {isRecording && (
          <span className="flex items-end gap-0.5" aria-hidden="true">
            {[6, 14, 20, 12, 8].map((h, i) => (
              <span
                key={i}
                className="w-1 rounded-full bg-high animate-pulse"
                style={{ height: h, animationDelay: `${i * 100}ms` }}
              />
            ))}
          </span>
        )}
        {!isRecording && (
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <rect x="9" y="2" width="6" height="12" rx="3" stroke="#4A9291" strokeWidth="1.6" />
            <path d="M5 11a7 7 0 0 0 14 0M12 18v3" stroke="#4A9291" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        )}
      </button>
      <p className={cx("text-sm", state === "error" ? "text-high" : "text-muted")} role="status">
        {STATE_LABEL[state]}
      </p>
      <p className="text-xs text-muted">Supported formats: WAV, MP3, M4A</p>
    </div>
  );
}

import { PriorityBand } from "@/types";

export function cx(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

export function bandColor(bandName: PriorityBand): string {
  switch (bandName) {
    case "HIGH":
      return "text-high border-high";
    case "MODERATE":
      return "text-accent border-accent";
    default:
      return "text-primary-light border-primary-light";
  }
}

export function bandBg(bandName: PriorityBand): string {
  switch (bandName) {
    case "HIGH":
      return "bg-high/15";
    case "MODERATE":
      return "bg-accent/15";
    default:
      return "bg-primary/15";
  }
}

export function bandDot(bandName: PriorityBand): string {
  switch (bandName) {
    case "HIGH":
      return "bg-high";
    case "MODERATE":
      return "bg-accent";
    default:
      return "bg-primary-light";
  }
}

export function formatScore(n: number): string {
  return n.toFixed(1);
}

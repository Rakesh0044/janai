import { PriorityBand } from "@/types";
import { bandBg, bandColor, bandDot, cx } from "@/lib/utils";

export default function PriorityBadge({ band }: { band: PriorityBand }) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-xs font-medium",
        bandColor(band),
        bandBg(band)
      )}
    >
      <span className={cx("h-1.5 w-1.5 rounded-full", bandDot(band))} aria-hidden="true" />
      {band}
    </span>
  );
}

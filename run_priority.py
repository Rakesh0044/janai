"""Run Module 4 over Module 3's synthetic demand and context datasets."""

import json
import sys

from app.analysis import analyze_synthetic_demo
from app.context_data import SYNTHETIC_CONTEXT_LABEL, make_synthetic_context_data
from app.insights import build_development_priority_insights
from app.synthetic_data import SYNTHETIC_DATA_LABEL


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    demand = analyze_synthetic_demo()
    insights = build_development_priority_insights(
        demand.insights,
        make_synthetic_context_data(),
    )
    print(SYNTHETIC_DATA_LABEL)
    print(SYNTHETIC_CONTEXT_LABEL)
    print("DEVELOPMENT PRIORITY INSIGHTS — PROTOTYPE ANALYSIS, NOT A FUNDING DECISION\n")
    print(f"Showing the 10 highest combined scores from {len(insights)} city/category insights.\n")
    print(json.dumps({
        "development_priority_insights": [item.model_dump(mode="json") for item in insights[:10]],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

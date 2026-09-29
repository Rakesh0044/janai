"""Display synthetic Module 3 demand insights."""

import json
import sys

from app.analysis import analyze_synthetic_demo
from app.synthetic_data import SYNTHETIC_DATA_LABEL


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    result = analyze_synthetic_demo()
    print(SYNTHETIC_DATA_LABEL)
    print("DEVELOPMENT DEMAND INSIGHTS — PROTOTYPE ANALYSIS, NOT A FUNDING DECISION\n")
    print(f"Analyzed {result.cleaned_request_count} synthetic requests; showing the 10 highest relative scores.\n")
    output = {
        "dataset_label": result.dataset_label,
        "development_demand_insights": [item.model_dump(mode="json") for item in result.insights[:10]],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the Module 5 explanation demo on one synthetic Module 4 insight."""

import json
import sys

from pydantic import ValidationError

from app.analysis import analyze_synthetic_demo
from app.context_data import SYNTHETIC_CONTEXT_LABEL, make_synthetic_context_data
from app.explanations import ExplanationError, explain_development_priority
from app.insights import build_development_priority_insights
from app.synthetic_data import SYNTHETIC_DATA_LABEL


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("AI EXPLANATION DEMO")
    print(SYNTHETIC_DATA_LABEL)
    print(SYNTHETIC_CONTEXT_LABEL)

    module3_result = analyze_synthetic_demo()
    module4_insights = build_development_priority_insights(
        module3_result.insights,
        make_synthetic_context_data(),
    )
    if not module4_insights:
        print("Module 4 produced no eligible demo insight.", file=sys.stderr)
        return 1

    input_insight = module4_insights[0]
    try:
        explanation = explain_development_priority(input_insight, is_synthetic=True)
    except (ExplanationError, ValidationError) as exc:
        print(f"Could not generate explanation: {exc}", file=sys.stderr)
        return 1

    print("\nMODULE 4 INPUT INSIGHT")
    print(json.dumps(input_insight.model_dump(mode="json"), ensure_ascii=False, indent=2))
    print("\nMODULE 5 AI EXPLANATION")
    print(json.dumps(explanation.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

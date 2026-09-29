"""Small deterministic dataset for demonstrating Module 3 only."""

from datetime import datetime, timedelta, timezone

from .analytics import CITY_STATES

SYNTHETIC_DATA_LABEL = "SYNTHETIC DEMO DATA — NOT REAL GOVERNMENT DATA"
DEMO_CATEGORIES = (
    "Water Supply", "Roads", "Public Transportation", "Healthcare", "Education",
    "Sanitation", "Electricity", "Waste Management", "Public Safety",
)


def make_synthetic_requests() -> list[dict[str, object]]:
    """Create anonymous repeat requests across all prototype cities/categories."""
    base_time = datetime(2026, 9, 25, 12, tzinfo=timezone.utc)
    requests: list[dict[str, object]] = []
    for city_index, (city, state) in enumerate(CITY_STATES.items()):
        for category_index, category in enumerate(DEMO_CATEGORIES):
            count = 1 + ((city_index * 2 + category_index * 3) % 4)
            for record_index in range(count):
                severity = 1 + ((city_index + category_index + record_index) % 5)
                days_ago = (city_index * 3 + category_index * 5 + record_index * 11) % 46
                requests.append({
                    "original_text": f"Synthetic demonstration request about {category.lower()} in {city}.",
                    "language": ("Kannada", "Telugu", "Malayalam", "English")[(city_index + record_index) % 4],
                    "state": state,
                    "district_or_city": city,
                    "category": category,
                    "subcategory": None,
                    "severity": severity,
                    "urgency": None,
                    "duration": None,
                    "affected_population": None,
                    "confidence": 0.9,
                    "timestamp": base_time - timedelta(days=days_ago),
                })
    return requests

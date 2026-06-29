"""
recommender.py
--------------
Cost calculation + model recommendation engine.

Public function:
    get_recommendations(task_type, input_tokens, output_tokens,
                        requests_per_day, quality_preference) -> list[dict]

Pipeline:
    1. Filter models by quality_preference (tier set).
    2. Keep only models whose `strengths` include task_type.
    3. monthly_cost = ((in*in_price + out*out_price) / 1e6) * req/day * 30
    4. Sort by monthly_cost ascending.
    5. Return top 6, each annotated with savings vs the GPT-4o baseline and a
       `recommended` flag (True only for the cheapest = rank 1).

Each result dict:
    {
      "model_name", "provider", "quality_tier", "context_window",
      "monthly_cost", "cost_per_request",
      "savings_vs_gpt4o",       # monthly USD saved vs GPT-4o (can be negative)
      "savings_pct_vs_gpt4o",   # percent saved vs GPT-4o (can be negative)
      "recommended",            # bool
    }
"""

from pricing_db import PRICING_DB, BASELINE_MODEL, get_model

DAYS_PER_MONTH = 30
TOP_N = 6

# Quality preference -> the set of tiers that qualify.
# "mid" means "mid-tier and above"; "premium" means premium only.
_TIER_SETS = {
    "any": {"budget", "mid", "premium"},
    "budget": {"budget"},
    "mid": {"mid", "premium"},
    "premium": {"premium"},
}

# Maps the app's selectbox labels onto quality_preference keys.
QUALITY_LABEL_MAP = {
    "Any (optimize for cost)": "any",
    "Mid-tier and above": "mid",
    "Premium only": "premium",
}


def map_quality_label(label: str) -> str:
    """Translate a UI dropdown label into a quality_preference key."""
    return QUALITY_LABEL_MAP.get(label, "any")


def _monthly_cost(entry: dict, input_tokens: int, output_tokens: int,
                  requests_per_day: int) -> tuple[float, float]:
    """Return (cost_per_request, monthly_cost) in USD for one model."""
    cost_per_request = (
        input_tokens * entry["input_price"]
        + output_tokens * entry["output_price"]
    ) / 1_000_000
    monthly_cost = cost_per_request * requests_per_day * DAYS_PER_MONTH
    return cost_per_request, monthly_cost


def get_recommendations(task_type: str, input_tokens: int, output_tokens: int,
                        requests_per_day: int, quality_preference: str) -> list[dict]:
    """Return up to TOP_N cheapest suitable models for the task, cheapest first."""
    input_tokens = max(0, int(input_tokens or 0))
    output_tokens = max(0, int(output_tokens or 0))
    requests_per_day = max(0, int(requests_per_day or 0))

    allowed_tiers = _TIER_SETS.get(quality_preference, _TIER_SETS["any"])

    # Baseline (GPT-4o) monthly cost for the same workload — computed even if
    # GPT-4o itself doesn't pass the task/quality filters.
    baseline = get_model(BASELINE_MODEL)
    _, baseline_monthly = _monthly_cost(
        baseline, input_tokens, output_tokens, requests_per_day
    )

    candidates = []
    for name, entry in PRICING_DB.items():
        if entry["quality_tier"] not in allowed_tiers:
            continue
        if task_type not in entry["strengths"]:
            continue

        cost_per_request, monthly_cost = _monthly_cost(
            entry, input_tokens, output_tokens, requests_per_day
        )

        savings = baseline_monthly - monthly_cost
        savings_pct = (savings / baseline_monthly * 100) if baseline_monthly else 0.0

        candidates.append({
            "model_name": name,
            "provider": entry["provider"],
            "quality_tier": entry["quality_tier"],
            "context_window": entry["context_window"],
            "monthly_cost": round(monthly_cost, 2),
            "cost_per_request": round(cost_per_request, 6),
            "savings_vs_gpt4o": round(savings, 2),
            "savings_pct_vs_gpt4o": round(savings_pct, 1),
            "recommended": False,
        })

    # Cheapest first; tie-break by cost_per_request then name for determinism.
    candidates.sort(key=lambda c: (c["monthly_cost"], c["cost_per_request"], c["model_name"]))

    top = candidates[:TOP_N]
    if top:
        top[0]["recommended"] = True
    return top

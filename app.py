"""
app.py
------
SmartRoute AI -- Streamlit UI.

Ties together the pipeline:
    classify (classifier) -> estimate tokens (estimator)
    -> rank models (recommender) -> generate code (code_generator)
"""

import os
import warnings

# The google-generativeai package prints a noisy deprecation FutureWarning.
# It still works fine; silence it so the app logs stay clean.
warnings.filterwarnings("ignore", category=FutureWarning)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from classifier import classify_task
from estimator import estimate_tokens
from recommender import get_recommendations, map_quality_label
from code_generator import generate_snippet

load_dotenv()

# --------------------------------------------------------------------------- #
# Page config + helpers
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="SmartRoute AI", page_icon="🧭", layout="wide")

GEMINI_KEY_URL = "https://aistudio.google.com/app/apikey"


def money(value: float) -> str:
    """Format a USD amount with $ and 2 decimals."""
    return f"${value:,.2f}"


def money_precise(value: float) -> str:
    """Format a small per-request USD amount with more precision."""
    return f"${value:,.6f}"


# --------------------------------------------------------------------------- #
# Sidebar -- API key
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Settings")

    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    st.session_state.gemini_api_key = st.text_input(
        "Gemini API key",
        value=st.session_state.gemini_api_key,
        type="password",
        help="Used to classify your task with AI. Leave blank to use the "
             "offline keyword classifier.",
    )

    st.markdown(f"[Get a free Gemini API key →]({GEMINI_KEY_URL})")

    if st.session_state.gemini_api_key:
        st.success("AI classifier enabled (Gemini).")
    else:
        st.warning("No API key — using offline keyword classifier.")

    st.caption("Your key stays in this session and is never stored server-side.")


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("🧭 SmartRoute AI")
st.subheader("Find the cheapest AI API for your task")

# --------------------------------------------------------------------------- #
# SECTION 1 -- Input form
# --------------------------------------------------------------------------- #
st.markdown("### 1 · Describe your task")

with st.form("task_form"):
    task_description = st.text_area(
        "Describe your AI task",
        placeholder="e.g. Summarize customer support emails into 2-line summaries",
        height=100,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        avg_input_words = st.number_input(
            "Average input length (words)", min_value=1, value=300, step=50
        )
    with col2:
        avg_output_words = st.number_input(
            "Average output length (words)", min_value=1, value=100, step=25
        )
    with col3:
        requests_per_day = st.number_input(
            "Requests per day", min_value=1, value=500, step=100
        )

    quality_label = st.selectbox(
        "Quality preference",
        ["Any (optimize for cost)", "Mid-tier and above", "Premium only"],
    )

    submitted = st.form_submit_button("🔍 Find cheapest model", type="primary")


# --------------------------------------------------------------------------- #
# Run the pipeline on submit, store results in session state
# --------------------------------------------------------------------------- #
if submitted:
    if not task_description.strip():
        st.error("Please describe your task first.")
    else:
        api_key = st.session_state.gemini_api_key.strip() or None
        try:
            with st.spinner("Classifying your task..."):
                classification = classify_task(task_description, api_key=api_key)

            estimate = estimate_tokens(
                classification["task_type"],
                int(avg_input_words),
                int(avg_output_words),
            )

            recommendations = get_recommendations(
                task_type=classification["task_type"],
                input_tokens=estimate["input_tokens"],
                output_tokens=estimate["output_tokens"],
                requests_per_day=int(requests_per_day),
                quality_preference=map_quality_label(quality_label),
            )

            st.session_state.results = {
                "classification": classification,
                "estimate": estimate,
                "recommendations": recommendations,
                "requests_per_day": int(requests_per_day),
            }
        except Exception as exc:  # pragma: no cover -- defensive UI guard
            st.error(f"Something went wrong while analyzing your task: {exc}")


# --------------------------------------------------------------------------- #
# SECTION 2 + 3 -- Results
# --------------------------------------------------------------------------- #
def render_results(results: dict) -> None:
    classification = results["classification"]
    estimate = results["estimate"]
    recs = results["recommendations"]
    rpd = results["requests_per_day"]

    st.markdown("### 2 · Results")

    # Banner: classified task type + explanation.
    used_ai = "Gemini" not in classification["explanation"] and "fallback" not in classification["explanation"]
    banner = (
        f"**Task type:** {classification['task_type']}  ·  "
        f"**Confidence:** {classification['confidence']:.0%}\n\n"
        f"{classification['explanation']}"
    )
    if "fallback" in classification["explanation"]:
        st.info("🔌 " + banner)
    else:
        st.success("🤖 " + banner)

    st.caption(
        f"Token estimate: ~{estimate['input_tokens']:,} input / "
        f"~{estimate['output_tokens']:,} output tokens per request. "
        f"{estimate['notes']}"
    )

    if not recs:
        st.warning(
            "No models matched this task type and quality preference. "
            "Try 'Any (optimize for cost)'."
        )
        return

    best = recs[0]

    # Three metric cards.
    m1, m2, m3 = st.columns(3)
    m1.metric("🏆 Recommended model", best["model_name"], best["provider"])
    m2.metric("💰 Monthly cost", money(best["monthly_cost"]))
    m3.metric(
        "📉 Savings vs GPT-4o",
        money(best["savings_vs_gpt4o"]),
        f"{best['savings_pct_vs_gpt4o']:.1f}%",
    )

    # Horizontal bar chart -- recommended green, others blue.
    chart_rows = list(reversed(recs))  # cheapest at the top of the chart
    colors = ["#2ecc71" if r["recommended"] else "#4a90e2" for r in chart_rows]
    fig = go.Figure(
        go.Bar(
            x=[r["monthly_cost"] for r in chart_rows],
            y=[r["model_name"] for r in chart_rows],
            orientation="h",
            marker_color=colors,
            text=[money(r["monthly_cost"]) for r in chart_rows],
            textposition="auto",
            hovertemplate="%{y}<br>%{x:$,.2f}/mo<extra></extra>",
        )
    )
    fig.update_layout(
        title="Estimated monthly cost by model",
        xaxis_title="Monthly cost (USD)",
        yaxis_title="",
        height=60 + 55 * len(chart_rows),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Results table.
    table = pd.DataFrame([
        {
            "Model": r["model_name"],
            "Provider": r["provider"],
            "Quality": r["quality_tier"].capitalize(),
            "Monthly Cost": money(r["monthly_cost"]),
            "Cost/Request": money_precise(r["cost_per_request"]),
            "vs GPT-4o": f"{money(r['savings_vs_gpt4o'])} ({r['savings_pct_vs_gpt4o']:.1f}%)",
        }
        for r in recs
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)

    # ---- SECTION 3: code snippet ----
    st.markdown("### 3 · Ready-to-use code")
    snippet = generate_snippet(
        model_name=best["model_name"],
        task_type=classification["task_type"],
        cost_per_request=best["cost_per_request"],
        requests_per_day=rpd,
        monthly_cost=best["monthly_cost"],
    )
    st.code(snippet, language="python")

    safe_name = best["model_name"].lower().replace(" ", "_").replace(".", "")
    st.download_button(
        "⬇️ Download snippet (.py)",
        data=snippet,
        file_name=f"smartroute_{safe_name}.py",
        mime="text/x-python",
    )

    st.caption(
        "ℹ️ Prices are estimates based on token usage. "
        "Always verify current pricing on provider websites."
    )


if "results" in st.session_state:
    render_results(st.session_state.results)


# --------------------------------------------------------------------------- #
# How it works
# --------------------------------------------------------------------------- #
with st.expander("ℹ️ How it works"):
    st.markdown(
        """
        SmartRoute AI runs a **4-step pipeline**:

        1. **Classify** — your task description is categorized (summarization,
           code generation, RAG, etc.) using Gemini, or an offline keyword
           classifier when no API key is set.
        2. **Estimate tokens** — average input/output word counts are converted
           to tokens (~1.33 tokens/word) with a task-specific overhead
           (RAG adds context + history, code adds file context, etc.).
        3. **Rank models** — every model that fits your task and quality
           preference is priced for your volume (`req/day × 30`), then sorted
           cheapest-first.
        4. **Generate code** — a ready-to-run snippet is produced for the
           recommended model using the correct SDK.

        Pricing reflects publicly listed rates and is for estimation only.
        """
    )

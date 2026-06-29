# 🧭 SmartRoute AI

**Find the cheapest AI API for your task.**

SmartRoute AI is an intelligent LLM cost optimizer. Describe your AI task in plain
English, and it recommends the cheapest suitable model — with real cost comparisons
across 35 models from 6 providers, plus a ready-to-run code snippet.

---

## The problem

Teams routinely overpay for AI. They default to a flagship model (GPT-4o, Claude
Opus) for tasks a model 100× cheaper could handle just as well. With dozens of
models and constantly changing prices, picking the right one for each task is hard.

## The solution

SmartRoute AI runs a **4-step pipeline**:

1. **Classify** — the task description is categorized (summarization, RAG, code
   generation, translation, reasoning, etc.) using Google Gemini, with an offline
   keyword classifier as a no-API-key fallback.
2. **Estimate tokens** — input/output word counts are converted to tokens
   (~1.33 tokens/word) with a task-specific overhead (RAG adds system prompt +
   retrieved context + history; code adds file context; etc.).
3. **Rank models** — every model that fits the task and quality preference is
   priced for the user's monthly volume, then sorted cheapest-first.
4. **Generate code** — a runnable snippet is produced for the recommended model
   using the correct SDK for its provider.

---

## Key features

- 🧠 **AI task classification** (Gemini) with a robust offline fallback
- 💰 **Monthly cost projection** for the user's real request volume
- 📊 **Interactive cost-comparison chart** (Plotly) — recommended model highlighted
- 📉 **Savings vs GPT-4o** for every option
- 🎚️ **Quality filter** — optimize for cost, mid-tier and above, or premium only
- 🧑‍💻 **One-click code snippet** for the winning model, downloadable as `.py`
- 🔌 **Works with no API key** — falls back to a keyword classifier

## Models covered (35 across 6 providers)

OpenAI · Anthropic · Google · DeepSeek · Mistral · Alibaba (Qwen)
— pricing reflects publicly listed rates (June 2026).

---

## Tech stack

| Component | Technology |
|-----------|-----------|
| Web app | Python + Streamlit |
| Task classification | Google Gemini (`gemini-2.5-flash`) |
| Token counting | tiktoken |
| Charts | Plotly |
| Config | python-dotenv |

## Project structure

```
smartroute-ai/
├── app.py              # Streamlit UI (the 4-step pipeline, wired together)
├── classifier.py       # Task classifier (Gemini + keyword fallback)
├── estimator.py        # Token usage estimator
├── pricing_db.py       # Pricing + capability database for all models
├── recommender.py      # Cost calculation + ranking engine
├── code_generator.py   # Provider-aware code snippet generator
├── requirements.txt
└── .env.example
```

---

## Getting started

### 1. Install

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. (Optional) Add a Gemini API key

The app works without a key (offline classifier). For AI classification, copy
`.env.example` to `.env` and add your key:

```
GEMINI_API_KEY=your_key_here
```

Get a free key at https://aistudio.google.com/app/apikey

### 3. Run

```bash
streamlit run app.py
```

Open http://localhost:8501.

---

## Example

> **Task:** "Build a RAG chatbot that answers customer questions from our docs"
> **Volume:** 500 requests/day
>
> **Result:** Recommended **Qwen2.5-7B-Instruct** at **$0.60/month** —
> a **99% saving** versus running the same workload on GPT-4o (~$65/month).

---

## Disclaimer

Prices are estimates based on token usage and publicly listed rates. Always verify
current pricing on provider websites before committing to a model.

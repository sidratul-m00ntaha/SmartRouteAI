"""
pricing_db.py
-------------
Static pricing + capability database for all supported LLM models.

Prices are USD per 1,000,000 tokens (input / output), reflecting publicly
listed provider pricing as of June 2026. For models with tiered context
pricing (e.g. Gemini Pro >200K, GPT short/long context) the standard /
short-context rate is used. Cache pricing is ignored — the estimator works
in plain input/output tokens. Always verify current pricing on provider sites.

Each model entry contains:
  - provider:        provider/company name
  - input_price:     USD per 1M input tokens
  - output_price:    USD per 1M output tokens
  - context_window:  max context size in tokens
  - strengths:       task types the model handles well (see TASK_TYPES)
  - quality_tier:    "budget" | "mid" | "premium"
"""

# Canonical task categories. Every module imports these exact strings so the
# classifier, recommender, and pricing DB never disagree on spelling.
TASK_TYPES = [
    "summarization",
    "classification",
    "chatbot / RAG",
    "code generation",
    "translation",
    "creative writing",
    "complex reasoning",
    "data extraction",
]

# Convenience: a model good at everything.
_ALL = list(TASK_TYPES)

PRICING_DB = {
    # ---------------------------------------------------------------- OpenAI
    "GPT-5.2": {
        "provider": "OpenAI", "input_price": 1.75, "output_price": 14.00,
        "context_window": 400_000, "quality_tier": "premium",
        "strengths": list(_ALL),
    },
    "GPT-5.1": {
        "provider": "OpenAI", "input_price": 1.25, "output_price": 10.00,
        "context_window": 400_000, "quality_tier": "premium",
        "strengths": list(_ALL),
    },
    "GPT-5-mini": {
        "provider": "OpenAI", "input_price": 0.25, "output_price": 2.00,
        "context_window": 400_000, "quality_tier": "mid",
        "strengths": list(_ALL),
    },
    "GPT-5-nano": {
        "provider": "OpenAI", "input_price": 0.05, "output_price": 0.40,
        "context_window": 400_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "translation", "data extraction", "code generation",
                      "creative writing", "complex reasoning"],
    },
    "GPT-4.1": {
        "provider": "OpenAI", "input_price": 2.00, "output_price": 8.00,
        "context_window": 1_000_000, "quality_tier": "mid",
        "strengths": list(_ALL),
    },
    "GPT-4.1-mini": {
        "provider": "OpenAI", "input_price": 0.40, "output_price": 1.60,
        "context_window": 1_000_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "code generation", "translation", "creative writing",
                      "data extraction"],
    },
    "GPT-4.1-nano": {
        "provider": "OpenAI", "input_price": 0.10, "output_price": 0.40,
        "context_window": 1_000_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "translation", "data extraction"],
    },
    "GPT-4o": {
        "provider": "OpenAI", "input_price": 2.50, "output_price": 10.00,
        "context_window": 128_000, "quality_tier": "mid",
        "strengths": list(_ALL),
    },
    "GPT-4o-mini": {
        "provider": "OpenAI", "input_price": 0.15, "output_price": 0.60,
        "context_window": 128_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "code generation", "translation", "creative writing",
                      "data extraction"],
    },
    "o4-mini": {
        "provider": "OpenAI", "input_price": 1.10, "output_price": 4.40,
        "context_window": 200_000, "quality_tier": "mid",
        "strengths": ["complex reasoning", "code generation",
                      "data extraction", "classification", "summarization"],
    },

    # ------------------------------------------------------------- Anthropic
    "Claude Fable 5": {
        "provider": "Anthropic", "input_price": 10.00, "output_price": 50.00,
        "context_window": 200_000, "quality_tier": "premium",
        "strengths": list(_ALL),
    },
    "Claude Opus 4.8": {
        "provider": "Anthropic", "input_price": 5.00, "output_price": 25.00,
        "context_window": 200_000, "quality_tier": "premium",
        "strengths": list(_ALL),
    },
    "Claude Sonnet 4.6": {
        "provider": "Anthropic", "input_price": 3.00, "output_price": 15.00,
        "context_window": 200_000, "quality_tier": "mid",
        "strengths": list(_ALL),
    },
    "Claude Haiku 4.5": {
        "provider": "Anthropic", "input_price": 1.00, "output_price": 5.00,
        "context_window": 200_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "code generation", "translation", "data extraction"],
    },

    # ---------------------------------------------------------------- Google
    "Gemini 3.1 Pro": {
        "provider": "Google", "input_price": 2.00, "output_price": 12.00,
        "context_window": 2_000_000, "quality_tier": "premium",
        "strengths": list(_ALL),
    },
    "Gemini 3.5 Flash": {
        "provider": "Google", "input_price": 1.50, "output_price": 9.00,
        "context_window": 1_000_000, "quality_tier": "mid",
        "strengths": list(_ALL),
    },
    "Gemini 3.5 Flash-Lite": {
        "provider": "Google", "input_price": 0.10, "output_price": 0.40,
        "context_window": 1_000_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "translation", "data extraction"],
    },
    "Gemini 2.5 Pro": {
        "provider": "Google", "input_price": 1.25, "output_price": 10.00,
        "context_window": 2_000_000, "quality_tier": "mid",
        "strengths": list(_ALL),
    },
    "Gemini 2.5 Flash": {
        "provider": "Google", "input_price": 0.30, "output_price": 2.50,
        "context_window": 1_000_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "translation", "data extraction", "code generation",
                      "complex reasoning"],
    },
    "Gemini 2.5 Flash-Lite": {
        "provider": "Google", "input_price": 0.10, "output_price": 0.40,
        "context_window": 1_000_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "translation", "data extraction"],
    },

    # -------------------------------------------------------------- DeepSeek
    "DeepSeek V4 Pro": {
        "provider": "DeepSeek", "input_price": 0.435, "output_price": 0.87,
        "context_window": 128_000, "quality_tier": "mid",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "code generation", "complex reasoning", "data extraction"],
    },
    "DeepSeek V4 Flash": {
        "provider": "DeepSeek", "input_price": 0.14, "output_price": 0.28,
        "context_window": 128_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "data extraction", "code generation", "complex reasoning"],
    },
    "DeepSeek V4": {
        "provider": "DeepSeek", "input_price": 0.27, "output_price": 0.55,
        "context_window": 128_000, "quality_tier": "mid",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "code generation", "complex reasoning", "data extraction"],
    },
    "DeepSeek R1": {
        "provider": "DeepSeek", "input_price": 0.55, "output_price": 2.19,
        "context_window": 128_000, "quality_tier": "mid",
        "strengths": ["complex reasoning", "code generation", "data extraction"],
    },

    # --------------------------------------------------------------- Mistral
    "Mistral Large 3": {
        "provider": "Mistral", "input_price": 0.50, "output_price": 1.50,
        "context_window": 128_000, "quality_tier": "mid",
        "strengths": list(_ALL),
    },
    "Mistral Medium 3": {
        "provider": "Mistral", "input_price": 0.40, "output_price": 2.00,
        "context_window": 128_000, "quality_tier": "mid",
        "strengths": list(_ALL),
    },
    "Mistral Small 4": {
        "provider": "Mistral", "input_price": 0.15, "output_price": 0.60,
        "context_window": 128_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "translation", "data extraction", "creative writing"],
    },
    "Mistral Small 3.2": {
        "provider": "Mistral", "input_price": 0.10, "output_price": 0.30,
        "context_window": 128_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "translation", "data extraction"],
    },
    "Magistral Medium": {
        "provider": "Mistral", "input_price": 2.00, "output_price": 5.00,
        "context_window": 128_000, "quality_tier": "mid",
        "strengths": ["complex reasoning", "code generation",
                      "data extraction", "summarization", "classification"],
    },
    "Devstral 2": {
        "provider": "Mistral", "input_price": 0.40, "output_price": 2.00,
        "context_window": 256_000, "quality_tier": "mid",
        "strengths": ["code generation", "data extraction", "complex reasoning"],
    },
    "Codestral": {
        "provider": "Mistral", "input_price": 0.30, "output_price": 0.90,
        "context_window": 256_000, "quality_tier": "budget",
        "strengths": ["code generation", "data extraction"],
    },

    # ------------------------------------------------------- Alibaba (Qwen)
    "Qwen2.5-72B-Instruct": {
        "provider": "Alibaba (Qwen)", "input_price": 0.23, "output_price": 0.23,
        "context_window": 32_000, "quality_tier": "mid",
        "strengths": list(_ALL),
    },
    "Qwen2.5-Coder-32B": {
        "provider": "Alibaba (Qwen)", "input_price": 0.20, "output_price": 0.20,
        "context_window": 32_000, "quality_tier": "budget",
        "strengths": ["code generation", "data extraction"],
    },
    "Qwen2.5-14B-Instruct": {
        "provider": "Alibaba (Qwen)", "input_price": 0.10, "output_price": 0.10,
        "context_window": 32_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "translation", "data extraction", "creative writing",
                      "complex reasoning"],
    },
    "Qwen2.5-7B-Instruct": {
        "provider": "Alibaba (Qwen)", "input_price": 0.03, "output_price": 0.03,
        "context_window": 32_000, "quality_tier": "budget",
        "strengths": ["summarization", "classification", "chatbot / RAG",
                      "translation", "data extraction"],
    },
}

# Reference model used to compute "savings vs GPT-4o" in the recommender.
BASELINE_MODEL = "GPT-4o"


def get_model(model_name: str) -> dict:
    """Return the full entry for a model, or None if not found."""
    return PRICING_DB.get(model_name)


def all_models() -> dict:
    """Return the entire pricing database."""
    return PRICING_DB

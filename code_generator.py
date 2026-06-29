"""
code_generator.py
-----------------
Generates a ready-to-run Python snippet for a recommended model, using the
correct SDK / endpoint for that model's provider.

Public function:
    generate_snippet(model_name, task_type, cost_per_request,
                     requests_per_day=None, monthly_cost=None) -> str

Providers covered:
    OpenAI           -> openai SDK
    Anthropic        -> anthropic SDK
    Google           -> google-generativeai SDK
    DeepSeek         -> openai SDK with base_url
    Alibaba (Qwen)   -> openai SDK with DashScope base_url
    Mistral          -> mistralai SDK
"""

from pricing_db import get_model

DAYS_PER_MONTH = 30

# Display name -> the model id you actually pass to the provider's API.
_API_MODEL_IDS = {
    # OpenAI
    "GPT-5.2": "gpt-5.2", "GPT-5.1": "gpt-5.1", "GPT-5-mini": "gpt-5-mini",
    "GPT-5-nano": "gpt-5-nano", "GPT-4.1": "gpt-4.1", "GPT-4.1-mini": "gpt-4.1-mini",
    "GPT-4.1-nano": "gpt-4.1-nano", "GPT-4o": "gpt-4o", "GPT-4o-mini": "gpt-4o-mini",
    "o4-mini": "o4-mini",
    # Anthropic
    "Claude Fable 5": "claude-fable-5", "Claude Opus 4.8": "claude-opus-4-8",
    "Claude Sonnet 4.6": "claude-sonnet-4-6", "Claude Haiku 4.5": "claude-haiku-4-5",
    # Google
    "Gemini 3.1 Pro": "gemini-3.1-pro", "Gemini 3.5 Flash": "gemini-3.5-flash",
    "Gemini 3.5 Flash-Lite": "gemini-3.5-flash-lite", "Gemini 2.5 Pro": "gemini-2.5-pro",
    "Gemini 2.5 Flash": "gemini-2.5-flash", "Gemini 2.5 Flash-Lite": "gemini-2.5-flash-lite",
    # DeepSeek (V-series -> chat, R-series -> reasoner)
    "DeepSeek V4 Pro": "deepseek-chat", "DeepSeek V4 Flash": "deepseek-chat",
    "DeepSeek V4": "deepseek-chat", "DeepSeek R1": "deepseek-reasoner",
    # Mistral
    "Mistral Large 3": "mistral-large-latest", "Mistral Medium 3": "mistral-medium-latest",
    "Mistral Small 4": "mistral-small-latest", "Mistral Small 3.2": "mistral-small-latest",
    "Magistral Medium": "magistral-medium-latest", "Devstral 2": "devstral-medium-latest",
    "Codestral": "codestral-latest",
    # Qwen
    "Qwen2.5-72B-Instruct": "qwen2.5-72b-instruct", "Qwen2.5-Coder-32B": "qwen2.5-coder-32b-instruct",
    "Qwen2.5-14B-Instruct": "qwen2.5-14b-instruct", "Qwen2.5-7B-Instruct": "qwen2.5-7b-instruct",
}

# Task type -> an example prompt body, so the snippet is task-appropriate.
_TASK_PROMPTS = {
    "summarization":     "Summarize the following text in 2 concise lines:\n\n{your_input}",
    "classification":    "Classify the following text. Respond with one label only:\n\n{your_input}",
    "chatbot / RAG":     "Answer the user's question using ONLY the context below.\n\nContext:\n{your_context}\n\nQuestion: {your_input}",
    "code generation":   "Write Python code for the following requirement:\n\n{your_input}",
    "translation":       "Translate the following text into French:\n\n{your_input}",
    "creative writing":  "Write a short, engaging piece about:\n\n{your_input}",
    "complex reasoning": "Think step by step and solve the following:\n\n{your_input}",
    "data extraction":   "Extract the requested fields as JSON from the text:\n\n{your_input}",
}
_DEFAULT_PROMPT = "{your_input}"


def _api_id(model_name: str) -> str:
    """Resolve the provider-side model id, with a slug fallback."""
    if model_name in _API_MODEL_IDS:
        return _API_MODEL_IDS[model_name]
    return model_name.lower().replace(" ", "-")


def _header(model_name: str, task_type: str, cost_per_request: float,
            requests_per_day, monthly_cost) -> str:
    """Build the top-of-file cost comment block."""
    lines = [
        f"# SmartRoute AI -- recommended model for: {task_type}",
        f"# Model: {model_name}",
        f"# Estimated cost per request: ${cost_per_request:,.6f}",
    ]
    if monthly_cost is None and requests_per_day:
        monthly_cost = cost_per_request * requests_per_day * DAYS_PER_MONTH
    if monthly_cost is not None:
        vol = f" at {requests_per_day:,} req/day" if requests_per_day else ""
        lines.append(f"# Estimated monthly cost{vol}: ${monthly_cost:,.2f}")
    lines.append("# NOTE: prices are estimates -- verify current pricing with the provider.")
    return "\n".join(lines)


def generate_snippet(model_name: str, task_type: str, cost_per_request: float,
                     requests_per_day: int | None = None,
                     monthly_cost: float | None = None) -> str:
    """Return a runnable Python snippet string for the given model."""
    entry = get_model(model_name)
    provider = entry["provider"] if entry else "OpenAI"
    api_id = _api_id(model_name)
    prompt = _TASK_PROMPTS.get(task_type, _DEFAULT_PROMPT)
    header = _header(model_name, task_type, cost_per_request, requests_per_day, monthly_cost)

    builder = _PROVIDER_BUILDERS.get(provider, _openai_snippet)
    return builder(header, api_id, prompt)


# --------------------------------------------------------------------------- #
# Provider-specific snippet builders
# --------------------------------------------------------------------------- #
def _openai_snippet(header: str, api_id: str, prompt: str) -> str:
    return f'''{header}
# Install:  pip install openai

from openai import OpenAI

client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

prompt = """{prompt}"""

response = client.chat.completions.create(
    model="{api_id}",
    messages=[{{"role": "user", "content": prompt}}],
)

print(response.choices[0].message.content)
'''


def _anthropic_snippet(header: str, api_id: str, prompt: str) -> str:
    return f'''{header}
# Install:  pip install anthropic

import anthropic

client = anthropic.Anthropic(api_key="YOUR_ANTHROPIC_API_KEY")

prompt = """{prompt}"""

message = client.messages.create(
    model="{api_id}",
    max_tokens=1024,
    messages=[{{"role": "user", "content": prompt}}],
)

print(message.content[0].text)
'''


def _google_snippet(header: str, api_id: str, prompt: str) -> str:
    return f'''{header}
# Install:  pip install google-generativeai

import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")

prompt = """{prompt}"""

model = genai.GenerativeModel("{api_id}")
response = model.generate_content(prompt)

print(response.text)
'''


def _deepseek_snippet(header: str, api_id: str, prompt: str) -> str:
    return f'''{header}
# Install:  pip install openai   (DeepSeek is OpenAI-compatible)

from openai import OpenAI

client = OpenAI(
    api_key="YOUR_DEEPSEEK_API_KEY",
    base_url="https://api.deepseek.com",
)

prompt = """{prompt}"""

response = client.chat.completions.create(
    model="{api_id}",
    messages=[{{"role": "user", "content": prompt}}],
)

print(response.choices[0].message.content)
'''


def _qwen_snippet(header: str, api_id: str, prompt: str) -> str:
    return f'''{header}
# Install:  pip install openai   (Qwen via DashScope is OpenAI-compatible)

from openai import OpenAI

client = OpenAI(
    api_key="YOUR_DASHSCOPE_API_KEY",
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

prompt = """{prompt}"""

response = client.chat.completions.create(
    model="{api_id}",
    messages=[{{"role": "user", "content": prompt}}],
)

print(response.choices[0].message.content)
'''


def _mistral_snippet(header: str, api_id: str, prompt: str) -> str:
    return f'''{header}
# Install:  pip install mistralai

from mistralai import Mistral

client = Mistral(api_key="YOUR_MISTRAL_API_KEY")

prompt = """{prompt}"""

response = client.chat.complete(
    model="{api_id}",
    messages=[{{"role": "user", "content": prompt}}],
)

print(response.choices[0].message.content)
'''


_PROVIDER_BUILDERS = {
    "OpenAI": _openai_snippet,
    "Anthropic": _anthropic_snippet,
    "Google": _google_snippet,
    "DeepSeek": _deepseek_snippet,
    "Alibaba (Qwen)": _qwen_snippet,
    "Mistral": _mistral_snippet,
}

"""
classifier.py
-------------
Classifies a plain-language task description into one of the canonical
TASK_TYPES. Two paths:

  1. Gemini path  -> when an API key is supplied, ask Gemini for a structured
                     JSON verdict and parse it safely.
  2. Fallback path -> when no key (or the API fails), use simple keyword
                     matching so the app still works offline.

Both paths return the SAME shape:
    {"task_type": str, "confidence": float, "explanation": str}

Public function:
    classify_task(task_description: str, api_key: str | None = None) -> dict
"""

import json
import re

from pricing_db import TASK_TYPES

# The spec called for gemini-1.5-flash, but that model is retired (it's 2026).
# gemini-2.5-flash is the current fast/cheap equivalent — ideal for a quick
# classification call. Kept as a constant so it's trivial to swap.
GEMINI_MODEL = "gemini-2.5-flash"

# Keyword -> task_type rules for the offline fallback classifier.
# Order matters only for tie-breaking (earlier rules win ties).
_KEYWORD_RULES = [
    ("summarization",     ["summarize", "summary", "summarise", "shorten", "tldr", "recap"]),
    ("classification",    ["classify", "categorize", "categorise", "label", "sentiment", "tag", "intent"]),
    ("chatbot / RAG",     ["chat", "bot", "answer", "question", "rag", "assistant", "faq", "support agent"]),
    ("code generation",   ["code", "function", "script", "debug", "program", "sql", "api ", "refactor"]),
    ("translation",       ["translate", "translation", "language", "localize", "localise"]),
    ("creative writing",  ["write", "story", "creative", "blog", "poem", "marketing copy", "article"]),
    ("complex reasoning", ["reason", "analyze", "analyse", "complex", "research", "math", "plan", "strategy"]),
    ("data extraction",   ["extract", "parse", "find", "identify", "scrape", "structured data", "entities"]),
]

DEFAULT_TASK_TYPE = "summarization"


def classify_task(task_description: str, api_key: str | None = None) -> dict:
    """
    Classify a task description.

    If api_key is provided, try Gemini first and fall back to keywords on any
    error. If no api_key, use the keyword fallback directly.
    """
    task_description = (task_description or "").strip()
    if not task_description:
        return {
            "task_type": DEFAULT_TASK_TYPE,
            "confidence": 0.0,
            "explanation": "No task description provided; defaulting to summarization.",
        }

    if api_key:
        result = _classify_with_gemini(task_description, api_key)
        if result is not None:
            return result
        # Gemini failed -> fall through to keyword fallback below.

    return _classify_with_keywords(task_description, used_fallback_reason=(
        "No API key provided" if not api_key else "Gemini request failed"
    ))


# --------------------------------------------------------------------------- #
# Gemini path
# --------------------------------------------------------------------------- #
def _classify_with_gemini(task_description: str, api_key: str) -> dict | None:
    """Return a result dict, or None if anything goes wrong (caller falls back)."""
    try:
        import google.generativeai as genai
    except ImportError:
        return None

    categories = ", ".join(f'"{t}"' for t in TASK_TYPES)
    prompt = f"""You are a task classifier for an LLM cost-optimization tool.
Classify the user's task into EXACTLY ONE of these categories:
[{categories}]

Respond with ONLY a JSON object, no markdown, no extra text, in this exact shape:
{{"task_type": "<one of the categories above>", "confidence": <float 0.0-1.0>, "explanation": "<one short sentence>"}}

User task description:
\"\"\"{task_description}\"\"\""""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        raw = (response.text or "").strip()
    except Exception:
        return None

    parsed = _safe_parse_json(raw)
    if not parsed:
        return None

    task_type = _normalize_task_type(parsed.get("task_type", ""))
    if task_type is None:
        return None

    # Coerce confidence into a sane float in [0, 1].
    try:
        confidence = float(parsed.get("confidence", 0.7))
    except (TypeError, ValueError):
        confidence = 0.7
    confidence = max(0.0, min(1.0, confidence))

    explanation = str(parsed.get("explanation", "")).strip()
    if not explanation:
        explanation = f"Classified as {task_type} by Gemini."

    return {
        "task_type": task_type,
        "confidence": confidence,
        "explanation": explanation,
    }


def _safe_parse_json(raw: str) -> dict | None:
    """Extract and parse the first JSON object found in a model response."""
    if not raw:
        return None
    # Strip ```json ... ``` fences if present.
    raw = re.sub(r"^```(?:json)?", "", raw.strip())
    raw = re.sub(r"```$", "", raw.strip()).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Last resort: grab the substring between the first { and last }.
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _normalize_task_type(value: str) -> str | None:
    """Map a model-returned label onto a canonical TASK_TYPES entry, or None."""
    value = (value or "").strip().lower()
    if not value:
        return None
    for t in TASK_TYPES:
        if value == t.lower():
            return t
    # Loose contains-match (e.g. "chatbot", "rag", "coding").
    aliases = {
        "chatbot / RAG": ["chatbot", "rag", "chat", "conversation"],
        "code generation": ["code", "coding", "programming"],
        "creative writing": ["creative", "writing"],
        "complex reasoning": ["reasoning", "reason", "analysis"],
        "data extraction": ["extraction", "extract"],
    }
    for canonical, keys in aliases.items():
        if any(k in value for k in keys):
            return canonical
    for t in TASK_TYPES:
        if t.lower() in value or value in t.lower():
            return t
    return None


# --------------------------------------------------------------------------- #
# Fallback path
# --------------------------------------------------------------------------- #
def _classify_with_keywords(task_description: str, used_fallback_reason: str) -> dict:
    """Score each category by keyword hits; pick the best."""
    text = task_description.lower()

    best_type = None
    best_hits = 0
    for task_type, keywords in _KEYWORD_RULES:
        hits = sum(1 for kw in keywords if kw in text)
        if hits > best_hits:
            best_hits = hits
            best_type = task_type

    if best_type is None:
        return {
            "task_type": DEFAULT_TASK_TYPE,
            "confidence": 0.30,
            "explanation": (
                f"{used_fallback_reason}; no keywords matched, so defaulting "
                f"to {DEFAULT_TASK_TYPE} (keyword fallback)."
            ),
        }

    # Confidence scales modestly with the number of matched keywords.
    confidence = min(0.85, 0.45 + 0.15 * best_hits)
    return {
        "task_type": best_type,
        "confidence": round(confidence, 2),
        "explanation": (
            f"{used_fallback_reason}; matched {best_hits} keyword(s) for "
            f"'{best_type}' (keyword fallback, no AI used)."
        ),
    }

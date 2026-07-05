"""LLM-backed column mapping for messy BI export files."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request


ALLOWED_CANONICAL_FIELDS = {
    "chart_title",
    "chart_type",
    "sql_query",
    "weekly_views",
    "avg_view_duration_sec",
    "render_time_sec",
    "data_scanned_gb",
    "runs_per_week",
    "dashboard_name",
    "business_unit",
    "owner",
    "bi_tool",
}

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class LLMMappingError(RuntimeError):
    """Raised when an LLM backend cannot return a validated column mapping."""


def map_columns(raw_headers: list[str], sample_rows: list[dict]) -> dict:
    """Map raw headers to DashWise canonical fields using the configured LLM."""
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if provider == "gemini":
        response_text = _call_gemini(_build_prompt(raw_headers, sample_rows))
    elif provider == "ollama":
        response_text = _call_ollama(_build_prompt(raw_headers, sample_rows))
    else:
        raise LLMMappingError(f"Unsupported LLM_PROVIDER: {provider}")
    return validate_mapping_response(response_text, raw_headers)


def validate_mapping_response(response_text: str, raw_headers: list[str]) -> dict:
    """Parse and validate strict JSON from an LLM mapping response."""
    try:
        parsed = json.loads(_strip_code_fences(response_text))
    except json.JSONDecodeError as exc:
        raise LLMMappingError("LLM column mapping response was not valid JSON") from exc

    if not isinstance(parsed, dict):
        raise LLMMappingError("LLM column mapping response must be a JSON object")

    allowed_headers = set(raw_headers)
    mapping = {header: None for header in raw_headers}
    for raw_header, canonical_field in parsed.items():
        if raw_header not in allowed_headers:
            raise LLMMappingError(f"LLM returned an unknown raw header: {raw_header}")
        if canonical_field is None:
            mapping[raw_header] = None
            continue
        if canonical_field not in ALLOWED_CANONICAL_FIELDS:
            raise LLMMappingError(f"LLM returned an unsupported canonical field: {canonical_field}")
        mapping[raw_header] = canonical_field
    return mapping


def _build_prompt(raw_headers: list[str], sample_rows: list[dict]) -> str:
    allowed_fields = ", ".join(sorted(ALLOWED_CANONICAL_FIELDS))
    payload = {
        "raw_headers": raw_headers,
        "sample_rows": sample_rows[:5],
        "allowed_canonical_fields": sorted(ALLOWED_CANONICAL_FIELDS),
    }
    return (
        "You map messy BI dashboard export columns into the DashWise ingestion schema.\n"
        "Return strict JSON only, with each raw column name as a key and either one allowed "
        "canonical field name or null as the value. Do not include prose, markdown, comments, "
        "confidence scores, or nested objects.\n"
        f"Allowed canonical fields: {allowed_fields}.\n"
        "The cost context is INR-only. Do not introduce any non-INR currency assumptions.\n"
        f"Input:\n{json.dumps(payload, ensure_ascii=False, default=str)}"
    )


def _call_ollama(prompt: str) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).rstrip("/")
    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    request_body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    data = json.dumps(request_body).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise LLMMappingError("Ollama column mapping request failed") from exc

    response_text = payload.get("response")
    if not isinstance(response_text, str):
        raise LLMMappingError("Ollama response did not contain text")
    return response_text


def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMMappingError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    data = json.dumps(request_body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise LLMMappingError("Gemini column mapping request failed") from exc

    try:
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMMappingError("Gemini response did not contain text") from exc


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return stripped

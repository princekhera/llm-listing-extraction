"""Thin Gemini client: disk cache (re-runs are free and reproducible), a
throttle for free-tier rate limits, retries on 429/5xx, and a --mock mode so
the pipeline can be tested without an API key.

Get a free key at Google AI Studio, then:  export GEMINI_API_KEY=...
"""
import hashlib
import json
import os
import time

from .schema import DATA

GEN_MODEL = os.environ.get("GEN_MODEL", "gemini-3.8-flash")
EXTRACT_MODEL = os.environ.get("EXTRACT_MODEL", "gemini-3.1-flash-lite")
# Free tier allows only a handful of requests per minute; 13 s keeps under 5 RPM.
MIN_INTERVAL_S = float(os.environ.get("MIN_INTERVAL_S", "13"))
CACHE = DATA / "cache"

_client = None
_last_call = 0.0


def _key(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]


def _gemini(payload: dict) -> dict:
    global _client, _last_call
    from google import genai
    from google.genai import errors, types

    if _client is None:
        _client = genai.Client()  # reads GEMINI_API_KEY
    model = payload["model"]
    if model.startswith("gemini-2"):
        # 2.x: integer thinking budget; 0 disables thinking. Temperature honoured.
        extra = {"temperature": payload["temperature"],
                 "thinking_config": types.ThinkingConfig(thinking_budget=0)}
    else:
        # 3.x: thinking_budget is replaced by thinking_level, and Google advises
        # against setting temperature, so we leave it at the model default.
        extra = {"thinking_config": types.ThinkingConfig(thinking_level="LOW")}
    cfg = types.GenerateContentConfig(
        # Thinking tokens count against this limit, so leave generous headroom.
        max_output_tokens=payload["max_tokens"],
        system_instruction=payload.get("system"),
        response_mime_type="application/json" if payload.get("json_schema") else None,
        response_json_schema=payload.get("json_schema"),
        **extra,
    )
    for attempt in range(6):
        wait = MIN_INTERVAL_S - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()
        try:
            r = _client.models.generate_content(model=model,
                                                contents=payload["prompt"], config=cfg)
            if r.text:
                return {"text": r.text}
            reason = r.candidates[0].finish_reason if r.candidates else "no candidates"
            if attempt < 2:  # empty/blocked output: retry, then give up loudly
                print(f"  empty response ({reason}), retrying")
                continue
            raise RuntimeError(f"empty response after retries ({reason})")
        except errors.APIError as e:
            if e.code in (429, 500, 503) and attempt < 5:
                backoff = 30 * (attempt + 1)
                print(f"  API {e.code}, retrying in {backoff}s")
                time.sleep(backoff)
                continue
            if e.code == 429:
                raise SystemExit("Daily free-tier quota hit. Re-run tomorrow: cached "
                                 "calls are skipped, so it resumes where it stopped.")
            raise
    raise RuntimeError("API failed after retries")


def call(payload: dict, mock_fn=None) -> dict:
    """payload: model, prompt, temperature, max_tokens, optional system, json_schema.
    Returns {"text": ...}."""
    cache = CACHE.with_name("cache_mock") if mock_fn else CACHE  # never mix mock + real
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{_key(payload)}.json"
    if path.exists():
        return json.loads(path.read_text())
    resp = mock_fn(payload) if mock_fn else _gemini(payload)
    path.write_text(json.dumps(resp))
    return resp

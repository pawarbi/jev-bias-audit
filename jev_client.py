"""Thin client for TypeSafe Jev on OpenRouter's alpha decisions endpoint.

Every call is appended to a JSONL log with the exact request, the raw
response, the model that answered and a timestamp, so any result can be
traced back to what was sent.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"  # pinned, not the ~latest alias

_lock = threading.Lock()


def decide(state: str, questions: dict[str, dict], *, log_path: Path | None = None,
           tag: dict | None = None, retries: int = 4) -> dict:
    body = {"model": MODEL, "state": state, "questions": questions}
    headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(URL, json=body, headers=headers, timeout=60)
            if r.status_code == 200:
                out = r.json()
                break
            last = f"HTTP {r.status_code}: {r.text[:300]}"
            if r.status_code < 500 and r.status_code != 429:
                raise RuntimeError(last)
        except requests.RequestException as e:
            last = repr(e)
        time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"Jev call failed after {retries} tries: {last}")
    if log_path is not None:
        rec = {"ts": datetime.now(timezone.utc).isoformat(), "tag": tag or {},
               "request": body, "response": out}
        with _lock, open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return out


def choice(instructions: str, criteria: dict[str, str]) -> dict:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}

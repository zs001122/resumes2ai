from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx


API_BASE_URL = os.getenv("RESUMES2AI_API_BASE_URL", "http://localhost:8010")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESUME_PATH = PROJECT_ROOT / "简历数据" / "数据开发-杨晓飞.pdf"


def api_url(path: str) -> str:
    return f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def print_json(title: str, data: Any) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def assert_status(response: httpx.Response, expected: int | tuple[int, ...]) -> None:
    expected_codes = expected if isinstance(expected, tuple) else (expected,)
    if response.status_code not in expected_codes:
        try:
            body = response.json()
        except json.JSONDecodeError:
            body = response.text
        raise RuntimeError(
            f"{response.request.method} {response.request.url} expected {expected_codes}, "
            f"got {response.status_code}: {body}"
        )


def client() -> httpx.Client:
    # Local API tests should call the backend directly and ignore proxy env settings.
    return httpx.Client(base_url=API_BASE_URL, timeout=60.0, trust_env=False)

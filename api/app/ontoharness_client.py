"""HTTP client for OntoHarness validation sidecar."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings


def validate_turtle(content: str, domain: str | None = None) -> dict[str, Any]:
    """POST RDF Turtle to OntoHarness. Returns parsed JSON or a soft-fail envelope."""
    if not settings.ontoharness_enabled:
        return {"conforms": True, "skipped": True, "reason": "ontoharness_disabled"}

    base = settings.ontoharness_base_url.rstrip("/")
    payload = json.dumps(
        {
            "domain": domain or settings.ontoharness_domain,
            "format": "turtle",
            "content": content,
        }
    ).encode("utf-8")
    req = Request(
        f"{base}/api/v1/validate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=settings.ontoharness_timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "conforms": False,
            "error": f"HTTP {exc.code}",
            "detail": body,
        }
    except URLError as exc:
        if settings.ontoharness_fail_open:
            return {
                "conforms": True,
                "skipped": True,
                "reason": "ontoharness_unreachable",
                "error": str(exc.reason),
            }
        return {
            "conforms": False,
            "error": "ontoharness_unreachable",
            "detail": str(exc.reason),
        }


def blocks_approval(result: dict[str, Any]) -> bool:
    if result.get("skipped"):
        return False
    return not bool(result.get("conforms"))

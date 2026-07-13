"""Discern policy version and per-tier dimension thresholds."""
from __future__ import annotations

from typing import Any

POLICY_VERSION = "gapforge-discern-v1"

# Minimum score [0,1] to pass each dimension by risk tier.
# Missing dimensions in a request use these defaults.
DEFAULT_THRESHOLDS: dict[str, dict[str, float]] = {
    "L0": {
        "compliance": 0.8,
        "reliability": 0.3,
        "provenance": 0.3,
        "safety_language": 1.0,
    },
    "L1": {
        "compliance": 0.9,
        "reliability": 0.5,
        "provenance": 0.5,
        "safety_language": 1.0,
    },
    "L2": {
        "compliance": 1.0,
        "reliability": 0.6,
        "provenance": 0.7,
        "safety_language": 1.0,
    },
    "L3": {
        # L3 is blocked by policy; thresholds exist for reporting only.
        "compliance": 1.0,
        "reliability": 0.9,
        "provenance": 0.9,
        "safety_language": 1.0,
    },
}

ALL_DIMENSIONS = ("compliance", "reliability", "provenance", "safety_language")


def default_thresholds(risk_tier: str) -> dict[str, float]:
    tier = (risk_tier or "L2").upper()
    return dict(DEFAULT_THRESHOLDS.get(tier, DEFAULT_THRESHOLDS["L2"]))


def merge_thresholds(
    risk_tier: str, overrides: dict[str, float] | None = None
) -> dict[str, float]:
    base = default_thresholds(risk_tier)
    if overrides:
        for k, v in overrides.items():
            if k in ALL_DIMENSIONS:
                base[k] = float(v)
    return base


def policy_snapshot(risk_tier: str) -> dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION,
        "risk_tier": risk_tier,
        "thresholds": default_thresholds(risk_tier),
        "note": (
            "Discern scores + reasons; it never auto-approves L2 team conclusions. "
            "hard_fail blocks; soft_fail requires HITL."
        ),
    }

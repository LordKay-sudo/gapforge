"""Universal discernment: weigh input/output against policy thresholds."""
from __future__ import annotations

from app.discern.engine import discern
from app.discern.policy import POLICY_VERSION, default_thresholds

__all__ = ["discern", "POLICY_VERSION", "default_thresholds"]

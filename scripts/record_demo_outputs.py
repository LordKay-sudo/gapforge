#!/usr/bin/env python3
"""Record demo terminal outputs for docs/demo-recordings/ (no Docker required for OntoHarness parts)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "demo-recordings"
ONTOHARNESS_ROOT = ROOT.parent / "ontoharness"
BASE = os.environ.get("ONTOHARNESS_BASE_URL", "http://localhost:8010")


def write(name: str, content: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def ping(url: str) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return True, resp.read().decode("utf-8")[:500]
    except urllib.error.URLError as exc:
        return False, str(exc)


def run_validate_demo() -> str:
    py = ONTOHARNESS_ROOT / ".venv" / "Scripts" / "python.exe"
    if not py.is_file():
        py = Path(sys.executable)
    script = ONTOHARNESS_ROOT / "examples" / "validate_demo.py"
    if not script.is_file():
        return "# validate_demo.py not found\n"
    proc = subprocess.run(
        [str(py), str(script), "--base-url", BASE],
        capture_output=True,
        text=True,
        cwd=str(ONTOHARNESS_ROOT),
    )
    return proc.stdout + proc.stderr


def bridge_gap_record() -> str:
    payload = json.dumps(
        {
            "record": {
                "id": "gap-flurizan-endpoint",
                "claim": "Clinical endpoints may have been insufficiently sensitive.",
                "confidence": 0.62,
                "gap_class": "endpoint",
                "genes": [{"id": "ENSG00000130203", "symbol": "BRCA1"}],
                "disease": {"id": "MONDO_0004975", "name": "Alzheimer disease"},
            }
        }
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/api/v1/bridge/gap-record",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
        return json.dumps(json.loads(body), indent=2)
    except urllib.error.HTTPError as exc:
        return json.dumps(
            {"error": exc.code, "detail": exc.read().decode("utf-8", errors="replace")[:500]},
            indent=2,
        )


def fabricated_validation() -> str:
    bad = """
@prefix bio: <https://ontoharness.dev/biomedical#> .
bio:g1 a bio:Gene ;
    bio:hasTherapeuticTarget bio:d1 .
bio:d1 a bio:Disease .
""".strip()
    payload = json.dumps({"domain": "biomedical", "format": "turtle", "content": bad}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/v1/validate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.dumps(json.loads(resp.read()), indent=2)


def run_gapforge_api_tests() -> str:
    api = ROOT / "api"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_ontoharness.py", "-q", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=str(api),
    )
    return proc.stdout + proc.stderr


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = f"# Demo recording — {stamp} (UTC)\n\n"

    ok, health = ping(f"{BASE}/health")
    write(
        "00-preflight.txt",
        header
        + f"OntoHarness {BASE}/health: {'OK' if ok else 'UNREACHABLE'}\n\n"
        + health
        + "\n",
    )
    if not ok:
        print("Start OntoHarness: python -m uvicorn api.app.main:app --port 8010")
        return 1

    write("01-validate-demo.txt", header + run_validate_demo())
    bridge_out = bridge_gap_record()
    write("02-bridge-gap-record.json", header + bridge_out)
    write("03-fabricated-predicate.json", header + fabricated_validation())
    write("04-gapforge-ontology-tests.txt", header + run_gapforge_api_tests())

    bridge_body = bridge_out.split("\n", 1)[-1].strip()
    bridge_ok = '"conforms": true' in bridge_body or '"conforms":true' in bridge_body.replace(" ", "")

    manifest = {
        "recorded_at": stamp,
        "ontoharness_base": BASE,
        "files": [
            "00-preflight.txt",
            "01-validate-demo.txt",
            "02-bridge-gap-record.json",
            "03-fabricated-predicate.json",
            "04-gapforge-ontology-tests.txt",
        ],
        "ui_screenshots": [
            "screenshot-ontoharness-api-v0.5.png",
            "screenshot-ontoharness-docs.png",
            "screenshot-review-ontology-fail.png",
            "screenshot-review-ontology-pass.png",
            "demo-walkthrough.webm",
        ],
        "note": "Live Docker capture: docker compose -f docker-compose.yml -f docker-compose.ontoharness.yml up — then node scripts/capture_ontoharness_demo.mjs && node scripts/capture_demo_walkthrough.mjs",
        "bridge_endpoint_ok": bridge_ok,
    }
    write("manifest.json", json.dumps(manifest, indent=2) + "\n")
    print("Recording complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

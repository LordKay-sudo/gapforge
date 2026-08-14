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


def competency_score_validation() -> str:
    bad_score = """
@prefix bio: <https://ontoharness.dev/biomedical#> .
bio:gene1 a bio:Gene ;
    bio:hasSymbol "BRCA1" ;
    bio:associatedWith bio:disease1 ;
    bio:hasScore "1.5"^^<http://www.w3.org/2001/XMLSchema#decimal> .
bio:disease1 a bio:Disease ;
    bio:hasIdentifier "MONDO:0007254" .
""".strip()
    payload = json.dumps({"domain": "biomedical", "format": "turtle", "content": bad_score}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/v1/validate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.dumps(json.loads(resp.read()), indent=2)


def gapforge_api_post(path: str, payload: dict | None = None) -> str:
    url = f"http://localhost:8000/api/v1{path}"
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"} if payload else {}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            try:
                return json.dumps(json.loads(body), indent=2)
            except json.JSONDecodeError:
                return body
    except urllib.error.HTTPError as exc:
        return json.dumps(
            {"error": exc.code, "detail": exc.read().decode("utf-8", errors="replace")[:2000]},
            indent=2,
        )


def export_approved_rdf(gap_id: str) -> str:
    url = f"http://localhost:8000/api/v1/export/approved-rdf?gap_id={gap_id}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return f"# HTTP {exc.code}\n{exc.read().decode('utf-8', errors='replace')[:1000]}"


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
    write("05-competency-score.json", header + competency_score_validation())

    write(
        "06-ontology-validate-endpoint.json",
        header + gapforge_api_post("/gaps/gap-flurizan-endpoint/ontology-validate"),
    )
    write(
        "07-approve-endpoint.json",
        header
        + gapforge_api_post(
            "/reviews/gap-flurizan-endpoint",
            {"decision": "approve", "reviewer": "demo-recorder", "notes": "OntoHarness v0.6 demo capture"},
        ),
    )
    write(
        "08-export-approved-rdf.ttl",
        header + export_approved_rdf("gap-flurizan-endpoint"),
    )

    bridge_body = bridge_out.split("\n", 1)[-1].strip()
    bridge_ok = '"conforms": true' in bridge_body or '"conforms":true' in bridge_body.replace(" ", "")

    manifest = {
        "recorded_at": stamp,
        "ontoharness_base": BASE,
        "gapforge_api": "http://localhost:8000/api/v1",
        "files": [
            "00-preflight.txt",
            "01-validate-demo.txt",
            "02-bridge-gap-record.json",
            "03-fabricated-predicate.json",
            "04-gapforge-ontology-tests.txt",
            "05-competency-score.json",
            "06-ontology-validate-endpoint.json",
            "07-approve-endpoint.json",
            "08-export-approved-rdf.ttl",
        ],
        "ui_screenshots": [
            "screenshot-ontoharness-api-v0.6.png",
            "screenshot-ontoharness-docs.png",
            "screenshot-review-ontology-fail.png",
            "screenshot-review-competency-fail.png",
            "screenshot-review-ontology-pass.png",
            "demo-walkthrough.webm",
        ],
        "note": "Full stack: docker compose -f docker-compose.full.yml up --build (MCP needs OPENAI_API_KEY). Capture order: node scripts/capture_ontoharness_demo.mjs && node scripts/capture_demo_walkthrough.mjs (UI first), then python scripts/record_demo_outputs.py (approve + export)",
        "bridge_endpoint_ok": bridge_ok,
    }
    write("manifest.json", json.dumps(manifest, indent=2) + "\n")
    print("Recording complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

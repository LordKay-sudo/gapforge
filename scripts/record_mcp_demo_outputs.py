#!/usr/bin/env python3
"""Record MCP full-stack demo outputs (requires docker-compose.full.yml + OPENAI_API_KEY)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "demo-recordings"
MCP_BASE = os.environ.get("MCP_BASE_URL", "http://localhost:1337")
GAPFORGE_API = os.environ.get("GAPFORGE_API_BASE", "http://localhost:8000/api/v1")
PROGRAM_ID = "prog-flurizan-ad"


def write(name: str, content: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def ping(url: str, timeout: int = 10) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return True, resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        return False, str(exc)


def gapforge_get(path: str) -> str:
    url = f"{GAPFORGE_API}{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
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


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = f"# Demo recording — {stamp} (UTC)\n\n"

    checks = [
        ("GapForge API", f"{GAPFORGE_API}/health"),
        ("OntoHarness", "http://localhost:8010/health"),
        ("Embabel MCP", f"{MCP_BASE}/actuator/health"),
    ]
    preflight_lines = [header]
    mcp_ok = False
    for label, url in checks:
        ok, body = ping(url)
        preflight_lines.append(f"{label} {url}: {'OK' if ok else 'UNREACHABLE'}\n")
        preflight_lines.append(body[:800] + "\n\n")
        if label == "Embabel MCP":
            mcp_ok = ok

    write("09-mcp-fullstack-preflight.txt", "".join(preflight_lines))
    if not mcp_ok:
        print("Start full stack: docker compose -f docker-compose.full.yml up --build")
        print("Set OPENAI_API_KEY in .env for MCP.")
        return 1

    mcp_health, mcp_body = ping(f"{MCP_BASE}/actuator/health")
    write(
        "10-mcp-health.json",
        header + json.dumps(json.loads(mcp_body) if mcp_health else {"error": mcp_body}, indent=2) + "\n",
    )

    write(
        "11-program-dossier.json",
        header + gapforge_get(f"/programs/{PROGRAM_ID}/dossier"),
    )

    gaps = gapforge_get(f"/gaps?program_id={PROGRAM_ID}")
    write("12-flurizan-gaps.json", header + gaps)

    manifest_path = OUT / "manifest.json"
    manifest: dict = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    mcp_files = [
        "09-mcp-fullstack-preflight.txt",
        "10-mcp-health.json",
        "11-program-dossier.json",
        "12-flurizan-gaps.json",
    ]
    manifest["mcp_recorded_at"] = stamp
    manifest["mcp_base"] = MCP_BASE
    manifest["mcp_files"] = mcp_files
    manifest.setdefault("files", [])
    for name in mcp_files:
        if name not in manifest["files"]:
            manifest["files"].append(name)
    manifest.setdefault("ui_screenshots", [])
    for shot in [
        "screenshot-gapforge-api-docs.png",
        "screenshot-mcp-health.png",
        "screenshot-program-detail.png",
        "demo-fullstack-walkthrough.webm",
    ]:
        if shot not in manifest["ui_screenshots"]:
            manifest["ui_screenshots"].append(shot)
    manifest["full_stack_ok"] = mcp_ok
    write("manifest.json", json.dumps(manifest, indent=2) + "\n")
    print("MCP recording complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

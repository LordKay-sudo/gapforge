"""Measure search/read latency against a running BioInsight API (roadmap 5.3).

Usage:
    py -3 scripts/benchmark_api.py --base-url http://localhost:8000 --iterations 200

Reports p50/p95/p99 latency per endpoint. Requires the stack to be up and seeded
(see docs/PLATFORM.md). Numbers are environment-dependent; record them in
docs/BENCHMARKS.md alongside the host spec.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request


def _time_request(url: str, *, timeout: float) -> float:
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        resp.read()
    return (time.perf_counter() - start) * 1000.0


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(pct / 100.0 * (len(ordered) - 1))))
    return ordered[idx]


def _discover_gene(base_url: str, gene_id: str | None) -> tuple[str, str]:
    if gene_id:
        return gene_id, gene_id

    base = base_url.rstrip("/")
    for query in ("BRCA1", "TP53", "EGFR", "BRCA", "E"):
        url = f"{base}/api/v1/genes?q={urllib.parse.quote(query)}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                hits = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            continue
        if hits:
            gene = hits[0]
            return gene["id"], gene.get("symbol") or gene["id"]
    raise SystemExit("Could not discover a benchmark gene from /api/v1/genes — pass --gene-id")


def _build_endpoints(gene_id: str, symbol: str) -> list[tuple[str, str]]:
    return [
        ("search_genes", "/api/v1/genes?q=BRCA"),
        ("resolve_gene", f"/api/v1/resolve?query={urllib.parse.quote(symbol)}&entity_type=gene"),
        ("gene_detail", f"/api/v1/genes/{gene_id}"),
        ("gene_diseases", f"/api/v1/genes/{gene_id}/diseases"),
        ("gene_evidence", f"/api/v1/genes/{gene_id}/evidence"),
        ("stats", "/api/v1/stats"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark BioInsight API latency")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-request timeout seconds")
    parser.add_argument("--gene-id", default=None, help="Override benchmark gene (default: auto-discover)")
    args = parser.parse_args()

    gene_id, symbol = _discover_gene(args.base_url, args.gene_id)
    endpoints = _build_endpoints(gene_id, symbol)
    print(f"benchmark_gene={gene_id} ({symbol})")

    print(f"{'endpoint':<16}{'p50 ms':>10}{'p95 ms':>10}{'p99 ms':>10}{'mean ms':>10}")
    for name, path in endpoints:
        url = args.base_url.rstrip("/") + path
        for _ in range(args.warmup):
            _time_request(url, timeout=args.timeout)
        samples = [_time_request(url, timeout=args.timeout) for _ in range(args.iterations)]
        print(
            f"{name:<16}"
            f"{_percentile(samples, 50):>10.1f}"
            f"{_percentile(samples, 95):>10.1f}"
            f"{_percentile(samples, 99):>10.1f}"
            f"{statistics.mean(samples):>10.1f}"
        )


if __name__ == "__main__":
    main()

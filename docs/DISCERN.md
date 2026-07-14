# Discern

Universal **input/output weighing** against policy thresholds (compliance, reliability, provenance, safety language).

Discern **scores and gates**; it does **not** replace human approval for L2 team conclusions.

| Field | Value |
|-------|--------|
| Policy version | `gapforge-discern-v1` |
| API | `POST /api/v1/discern`, `GET /api/v1/discern/policy`, `POST /api/v1/gaps/{id}/discern` |
| MCP | `discern_artifact`, `run_gap_discern` |

## Overall / action

| overall | action | Meaning |
|---------|--------|---------|
| `pass` | `allow` (L0/L1) or `require_hitl` (L2) | Cleared thresholds |
| `soft_fail` | `require_hitl` | Below threshold or soft reasons — continue only with review |
| `hard_fail` | `block` | Compliance/safety/L3 — do not create/approve |

## Dimensions

| Dimension | Examples |
|-----------|----------|
| `compliance` | COU present; no regulatory-submission claims; L3 blocked |
| `safety_language` | No dosing / prescribing / patient advice / synthesis language |
| `reliability` | Dual-channel evidence; confidence vs evidence density; critic concerns |
| `provenance` | `provenance_hash`, `data_version`, citation ids |

Thresholds are per risk tier (see `GET /api/v1/discern/policy?risk_tier=L2`).

## Example

```bash
curl -s -X POST http://localhost:8000/api/v1/discern \
  -H "Content-Type: application/json" \
  -d '{
    "artifact_type": "gap_hypothesis",
    "risk_tier": "L2",
    "cou": "Generate literature-backed gap hypotheses for scientific discussion; not for clinical care or regulatory submission.",
    "output": {
      "claim": "Endpoint sensitivity may have been insufficient.",
      "confidence": 0.55,
      "supported_by_trial_ids": ["trial-flurizan-p3"],
      "literature_refs": [{"title": "PMC", "url": "https://pmc.ncbi.nlm.nih.gov/"}],
      "provenance_hash": "abc",
      "program_id": "prog-flurizan-ad"
    }
  }'
```

## Integration

- `POST /gaps/propose` — runs Discern first; **blocks** on `hard_fail`; stores `discern_json` on the node
- `POST /gaps/{id}/discern` — scores a stored gap and **persists** `discern_json` (approve gate source of truth)
- `POST /gaps/{id}/critic` — attaches Discern result after critic notes
- `POST /reviews/{id}` — **rejects approve** with 422 when stored Discern `action` is `block`
- UI: review queue **Discern** panel + Approve disabled on `block`; program gap cards show last score
- MCP `discern_artifact` / `run_gap_discern` — same contract for agents

See [GAPFORGE.md](./GAPFORGE.md) risk tiers.

# Recorded demo outputs

Captured from a **live Docker stack** (GapForge + OntoHarness).

**Re-record (stack running on localhost):**

```bash
docker compose -f docker-compose.yml -f docker-compose.ontoharness.yml up --build

# Terminal outputs + manifest
ONTOHARNESS_BASE_URL=http://localhost:8010 python scripts/record_demo_outputs.py

# UI screenshots (Playwright)
node scripts/capture_ontoharness_demo.mjs

# Short WebM walkthrough (review queue + Swagger)
node scripts/capture_demo_walkthrough.mjs
```

Convert WebM → GIF locally (optional, requires ffmpeg):

```bash
ffmpeg -i demo-walkthrough.webm -vf "fps=8,scale=1280:-1" demo-walkthrough.gif
```

## Files

| File | What it shows |
|------|----------------|
| [01-validate-demo.txt](./01-validate-demo.txt) | Valid graph passes; `hasTherapeuticTarget` blocked |
| [02-bridge-gap-record.json](./02-bridge-gap-record.json) | Flurizan endpoint gap → Turtle + `conforms: true` |
| [03-fabricated-predicate.json](./03-fabricated-predicate.json) | Raw API response for LLM-hallucinated predicate |
| [04-gapforge-ontology-tests.txt](./04-gapforge-ontology-tests.txt) | GapForge approve gate tests (3 passed) |
| [screenshot-review-ontology-fail.png](./screenshot-review-ontology-fail.png) | Live HITL — `gap-flurizan-efficacy` OntoHarness **failed** (Approve disabled) |
| [screenshot-review-ontology-pass.png](./screenshot-review-ontology-pass.png) | Live HITL — review queue with OntoHarness panel |
| [screenshot-ontoharness-api-v0.5.png](./screenshot-ontoharness-api-v0.5.png) | Live Swagger — validate + `bridge/gap-record` |
| [screenshot-ontoharness-docs.png](./screenshot-ontoharness-docs.png) | Swagger UI (alias capture) |
| [demo-walkthrough.webm](./demo-walkthrough.webm) | Screen recording — Swagger → review queue → efficacy fail |
| [review-ui-capture.html](./review-ui-capture.html) | Static fallback when Docker unavailable |
| [manifest.json](./manifest.json) | Recording metadata |

## Highlights (2026-08-10)

**Live Docker capture** — stack healthy on `:8080`, `:8000`, `:8010`.

**Fabricated predicate blocked:**

```json
"term": "https://ontoharness.dev/biomedical#hasTherapeuticTarget",
"message": "Undeclared property in policed namespace"
```

Seeded on `gap-flurizan-efficacy` in the HITL review UI (see screenshots + WebM).

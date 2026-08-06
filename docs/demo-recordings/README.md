# Recorded demo outputs

Captured by `scripts/record_demo_outputs.py` against a live OntoHarness sidecar.

**Re-record:**

```bash
# Terminal 1 — OntoHarness (latest code)
cd ../ontoharness
python -m uvicorn api.app.main:app --port 8011

# Terminal 2 — record
cd gapforge
ONTOHARNESS_BASE_URL=http://localhost:8011 python scripts/record_demo_outputs.py
```

**UI screenshots (full stack required):**

```bash
docker compose -f docker-compose.full.yml up --build
node scripts/capture_ontoharness_demo.mjs
```

## Files

| File | What it shows |
|------|----------------|
| [01-validate-demo.txt](./01-validate-demo.txt) | Valid graph passes; `hasTherapeuticTarget` blocked |
| [02-bridge-gap-record.json](./02-bridge-gap-record.json) | Flurizan endpoint gap → Turtle + `conforms: true` |
| [03-fabricated-predicate.json](./03-fabricated-predicate.json) | Raw API response for LLM-hallucinated predicate |
| [04-gapforge-ontology-tests.txt](./04-gapforge-ontology-tests.txt) | GapForge approve gate tests (3 passed) |
| [screenshot-ontoharness-api-v0.5.png](./screenshot-ontoharness-api-v0.5.png) | Swagger UI including `bridge/gap-record` |
| [screenshot-ontoharness-docs.png](./screenshot-ontoharness-docs.png) | Swagger UI (earlier capture) |
| [manifest.json](./manifest.json) | Recording metadata |

## Highlights (2026-08-06)

**Bridge — gap-flurizan-endpoint conforms:**

```json
"conforms": true,
"turtle": "... bio:supports bio:gap-flurizan-endpoint ..."
```

**Fabricated predicate blocked:**

```json
"term": "https://ontoharness.dev/biomedical#hasTherapeuticTarget",
"message": "Undeclared property in policed namespace"
```

This is the same failure seeded on `gap-flurizan-efficacy` in the HITL review UI.

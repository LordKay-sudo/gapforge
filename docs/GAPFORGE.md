# BioInsight GapForge

**Translational gap hunter** for stalled or failed-but-promising drug programs.
Agents **propose**; humans **dispose**. Not a molecule generator. Not clinical decision support.

| Field | Value |
|-------|--------|
| Status | MVP (educational case studies) |
| COU | Generate literature- and graph-backed *gap hypotheses* for scientific discussion |
| Non-use | Clinical care, prescribing, regulatory submission evidence, synthesis planning |

---

## Context of Use (COU)

> GapForge helps translational scientists assemble **evidence-backed hypotheses** about *why* a public development program may have stalled (efficacy, safety, PK, formulation, biomarker, endpoint, competitive), with citations and a mandatory human review step before any card is treated as a team conclusion.

Every agent run and API write for L2 outputs must carry this COU (see `cou` on hypothesis records and MCP tool responses).

---

## Risk tiers

| Tier | Capability | Policy |
|------|------------|--------|
| **L0** | Read-only graph / program explore | Auto-allowed |
| **L1** | Summaries with citations | Auto + post-hoc spot check |
| **L2** | Gap hypotheses / ranked next experiments | **HITL required** — status stays `needs_review` until approve/reject |
| **L3** | Chemistry generation, dose advice, patient-level recommendations | **Blocked** in v1 |

---

## Gap taxonomy

| Code | Class | Typical signals |
|------|-------|-----------------|
| `efficacy` | Lack of clinical efficacy | Phase 2/3 primary endpoint miss |
| `safety` | Safety / toxicity | AE rates, FAERS clusters, discontinuations |
| `pk_exposure` | PK / bioavailability / exposure | Dose–exposure inadequacy |
| `formulation` | Formulation / delivery | Stability, route, adherence |
| `biomarker` | Stratification / predictive biomarker | All-comers vs enriched; Phase 2→3 divergence |
| `endpoint` | Endpoint / surrogate mismatch | Mechanistic biomarker ≠ clinical outcome |
| `target_validity` | Wrong or weak biological hypothesis | Poor genetic support, species translation |
| `competitive` | SoC / portfolio (non-scientific) | Marked as extrinsic; still documented |

---

## Dual-channel evidence rule

An L2 hypothesis must include **either**:

1. At least one **structured** fact (graph edge, trial registry record, curated program field), **and** at least one **citable** literature/trial passage; **or**
2. Explicit `insufficient_evidence: true` with empty or weak bundles (honest failure mode).

Silent promotion of association scores to causal claims is forbidden.

---

## Discern (universal I/O weighing)

`POST /api/v1/discern` and MCP `discern_artifact` score artifacts on **compliance**, **reliability**, **provenance**, and **safety_language** against tier thresholds (`gapforge-discern-v1`).

- `hard_fail` → `block` (e.g. dosing language, L3)
- `soft_fail` / L2 pass → `require_hitl` (never auto-approve team conclusions)

Details: [DISCERN.md](./DISCERN.md).

---

## Neo4j model (GapForge)

```cypher
(:Drug {id, name, synonyms, chembl_id?})
(:Program {id, name, status, indication_name, moa, cou_note})
(:Trial {id, nct_id, phase, status, primary_endpoint, outcome_summary})
(:GapHypothesis {
  id, gap_class, claim, confidence,
  suggested_experiment, status,  // draft|needs_review|approved|rejected
  insufficient_evidence, provenance_hash, risk_tier, cou
})
(:Review {id, decision, reviewer, notes, decided_at})

(:Program)-[:INVESTIGATES]->(:Drug)
(:Program)-[:FOR_INDICATION]->(:Disease)
(:Program)-[:TARGETS]->(:Gene)
(:Program)-[:TESTED_IN]->(:Trial)
(:Trial)-[:FOR_INDICATION]->(:Disease)
(:GapHypothesis)-[:ABOUT]->(:Program)
(:GapHypothesis)-[:SUPPORTED_BY]->(:Trial|:Gene|:Disease|:DocumentRef)
(:GapHypothesis)-[:CONTRADICTED_BY]->(:Trial|:Gene|:Disease|:DocumentRef)
(:GapHypothesis)-[:DERIVED_FROM]->(:Trial|:Program)
(:Review)-[:REVIEWS]->(:GapHypothesis)
```

Main target–disease associations remain curated Open Targets ingest only.
Literature informs RAG / citations; it does **not** silently write new association edges.

---

## API surface (MVP)

| Method | Path | Tier |
|--------|------|------|
| `GET` | `/api/v1/programs` | L0 |
| `GET` | `/api/v1/programs/{id}` | L0 |
| `GET` | `/api/v1/programs/{id}/dossier` | L1 |
| `GET` | `/api/v1/programs/{id}/taxonomy` | L1 |
| `GET` | `/api/v1/gaps` | L0 |
| `GET` | `/api/v1/gaps/{id}` | L0 |
| `POST` | `/api/v1/gaps/propose` | L2 create → `needs_review` |
| `POST` | `/api/v1/gaps/{id}/critic` | L2 critic notes |
| `GET` | `/api/v1/reviews/queue` | HITL |
| `POST` | `/api/v1/reviews/{gap_id}` | approve / reject / request_more |
| `GET` | `/api/v1/export/review-bundle?gap_id=` | Provenance export |

---

## MCP tools (embabel-mcp)

| Tool | Purpose |
|------|---------|
| `plan_gap_investigation` | Intent + tool sequence + stop rules + COU |
| `build_program_dossier` | Structured program + trials + linked genes/diseases |
| `propose_gap_hypotheses` | Create/list L2 cards (HITL pending) |
| `run_critic` | Adversarial pass: counter-evidence + confidence clamp |
| `export_review_bundle` | Audit JSON: meta, dossier, cards, reviews, hashes |

Default MCP mode: propose-only. UI review queue is ground truth (see [HUMAN_IN_THE_LOOP.md](./HUMAN_IN_THE_LOOP.md)).

---

## Seeded case study (MVP)

**Flurizan (tarenflurbil) — Alzheimer's disease**

| Field | Value |
|-------|--------|
| Program id | `prog-flurizan-ad` |
| Public framing | Historical educational case study — not a recommendation to resurrect the asset |
| Disease | Alzheimer disease (`MONDO_0004975`) |
| Linked gene (graph) | APOE (`ENSG00000130203`) — stratification / AD genetics context |
| Exemplar trial | NCT00105547-style Phase 3 efficacy miss (curated summary) |
| Gap themes | `endpoint`, `biomarker`, `efficacy` / target engagement |

See `data/gapforge/flurizan_case.json` and [HUMAN_IN_THE_LOOP.md](./HUMAN_IN_THE_LOOP.md) GapForge section.

---

## Explicit non-goals (v1)

- De novo molecule design or synthesis planning (ChemCrow-class tools deferred)
- Clinical decision support or dosing advice
- Regulatory-grade credibility claims without wet-lab / clinical validation
- Replacing Open Targets, ChEMBL, ClinicalTrials.gov, or FDA systems
- Auto-approving L2 hypotheses

---

## Compliance posture

Aligned with FDA/EMA **Guiding Principles of Good AI Practice in Drug Development**:

1. Human-centric by design (HITL for L2)
2. Risk-based approach (tiers L0–L3)
3. Clear context of use
4. Data governance and provenance (`PROVENANCE.md`, `/meta`, review bundles)
5. Life-cycle documentation (this file + schema migration notes)

---

## Implementation map

| Layer | Location |
|-------|----------|
| Design (this doc) | `docs/GAPFORGE.md` |
| Constraints | `scripts/neo4j/init.cypher` |
| Seed | `scripts/seed_gapforge.py` + `data/gapforge/` |
| API | `api/app/routers/programs.py`, `gaps.py`, `reviews.py` |
| UI | `/programs`, `/program/:id`, `/gaps/review` |
| MCP | `BioInsightGapMcpTools.java` |
| Literature | kg-rag ClinicalTrials + Europe PMC corpora; PeerLens pre-filter |

---

*Update when adding case studies or changing risk-tier policy.*

# Human-in-the-loop (HITL)

BioInsight Graph is a **research demo**, not a clinical system. Human review is part of the intended workflow when agents or automation surface results.

## Three layers of human intervention

### 1. BioInsight web UI (ground truth)

Researchers validate associations visually — this is the primary HITL surface.

| Step | Action |
|------|--------|
| Search | Open http://localhost:8080 and search **BRCA1** |
| Inspect graph | Open gene detail → **Graph** tab, pan/zoom the force-directed view |
| Compare scores | Switch to **Table** view for association scores |
| Neo4j | Optional: confirm in Neo4j Browser http://localhost:7474 |

The UI screenshots in the README are the reference for what “correct” looks like in this dataset.

### 2. MCP + Cursor (agent assistant)

When using [embabel-mcp](https://github.com/LordKay-sudo/embabel-mcp):

1. Run tools with `format=markdown`.
2. Use MCP prompt **`review-gene-report`** — instructs the human to cross-check http://localhost:8080 before trusting the model’s summary.
3. Do not treat MCP output as medical advice.

### 3. Embabel `GeneResearchAgent` (optional form gate)

With `bioinsight.hitl.enabled=true` (interactive Embabel shell / supported clients), the agent pauses after loading graph data and waits for **`GeneResearchApproval`** (approve + notes) before emitting the final report.

Default for MCP server mode: **HITL off** (auto-approved) so Cursor is not blocked waiting for a form the client cannot render.

```yaml
# embabel-mcp application.yml or env
BIOINSIGHT_HITL_ENABLED=true
```

## Checklist before sharing a gene report

- [ ] Symbol resolves to the intended Ensembl ID
- [ ] Top disease scores match the graph/table in the web UI
- [ ] Disclaimer stated: Open Targets–style **sample** data
- [ ] Reviewer name or “demo review” noted if required by your process

---

## GapForge HITL (translational gap hypotheses)

GapForge L2 outputs (**gap hypotheses**) always start as `needs_review`. Agents and MCP tools may **propose** and **criticize**; only the web review queue (or explicit `POST /reviews/{gap_id}`) can **approve** or **reject**.

### UI workflow (ground truth)

| Step | Action |
|------|--------|
| Open programs | http://localhost:8080/programs — select **Flurizan AD program** |
| Inspect dossier | Trials, linked genes/diseases, taxonomy densities |
| Review queue | http://localhost:8080/gaps/review — approve / reject / request more |
| Export | Only **approved** cards appear in `team_conclusions` of the review bundle |

### Risk tiers (reminder)

- **L0–L1** — explore / cited summaries (auto)
- **L2** — gap hypotheses — **HITL required**
- **L3** — chemistry / dosing / patient advice — **blocked**

See [GAPFORGE.md](./GAPFORGE.md) for COU and dual-channel evidence rules.

### Checklist before treating a gap card as a team conclusion

- [ ] Claim is explanatory, not a treatment recommendation
- [ ] Dual-channel evidence present (structured + citation) or `insufficient_evidence` flagged
- [ ] Critic notes reviewed
- [ ] Cross-checked program page / Neo4j
- [ ] Reviewer name recorded on approve/reject

## Related

- [ARCHITECTURE.md](ARCHITECTURE.md) — URLs and ERD
- [GAPFORGE.md](GAPFORGE.md) — GapForge design
- [DEMO.md](DEMO.md) — recording walkthrough GIFs
- [ROADMAP.md](ROADMAP.md) — task IDs including GapForge G0–G5

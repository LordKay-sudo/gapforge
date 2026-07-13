# Contributing to GapForge

Thank you for helping build safer open tooling for translational research.

## Ground rules

1. **No clinical claims** — demos and docs must state educational / research-only use.
2. **L2 stays HITL** — do not auto-approve gap hypotheses in MCP or API defaults.
3. **L3 stays blocked** — no chemistry generation, dosing, or patient-level advice in v1.
4. **Provenance first** — new data sources need licence, version, and `PROVENANCE.md` updates.
5. **Curated fact graph** — do not silently write LLM-extracted edges into the main association graph.

## Dev setup

See [README.md](README.md) and [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

## PR checklist

- [ ] Tests added/updated for API changes (`api/tests/`)
- [ ] Docs updated (`docs/GAPFORGE.md` if policy/schema changes)
- [ ] Disclaimers preserved in UI/API `/meta`
- [ ] No secrets committed

## Code of conduct

Be respectful. This project touches life-and-death domains — prefer caution and clarity over hype.

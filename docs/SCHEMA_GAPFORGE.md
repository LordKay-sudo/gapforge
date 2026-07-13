# GapForge schema notes

Adds Program / Drug / Trial / GapHypothesis / Review labels and PROV-style edges on top of the Gene–Disease–Protein association graph.

| Change | Location |
|--------|----------|
| Constraints | `scripts/neo4j/init.cypher` |
| Seed | `scripts/seed_gapforge.py` (invoked from `seed_neo4j.py`) |
| Design | `docs/GAPFORGE.md` |
| Ontology | `docs/ONTOLOGY_SCHEMA.md` |

Association edges remain Open Targets curated ingest only — GapForge does not write `ASSOCIATED_WITH` from LLM extraction.

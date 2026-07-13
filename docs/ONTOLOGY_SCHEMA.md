# BioInsight ontology schema

Compact schema \(S = (E, R, \Phi)\) for the disease–target knowledge graph. Matches Neo4j labels, API `/api/v1` models, and MCP tools in [embabel-mcp](https://github.com/LordKay-sudo/embabel-mcp).

## Entity types (E)

| Type | ID rule | Key properties | Example |
|------|---------|----------------|---------|
| **Gene** | `ENSG` + 11 digits | `id`, `symbol`, `name` | `ENSG00000012048` / BRCA1 |
| **Disease** | `EFO_*` or `MONDO_*` (demo slice) | `id`, `name` | `MONDO_0007254` |
| **Protein** | UniProt accession | `id`, `name` | `P38398` |
| **Drug** | `drug-*` or ChEMBL-backed id | `id`, `name`, `synonyms`, `chembl_id?` | `drug-tarenflurbil` |
| **Program** | `prog-*` | `id`, `name`, `status`, `moa`, `cou_note` | `prog-flurizan-ad` |
| **Trial** | `trial-*` (+ `nct_id`) | `phase`, `status`, endpoints | `trial-flurizan-p3` |
| **GapHypothesis** | `gap-*` | `gap_class`, `claim`, `status`, `confidence`, `cou` | `gap-flurizan-endpoint` |
| **Review** | `review-*` | `decision`, `reviewer`, `notes` | — |

## Relation types (R)

| Relation | From → To | Properties (Φ) |
|----------|-----------|----------------|
| `ASSOCIATED_WITH` | Gene → Disease | `score`, `source`, `evidence_type`, `evidence_json`, optional `study_id` |
| `ENCODED_BY` | Protein → Gene | — |
| `INVESTIGATES` | Program → Drug | — |
| `FOR_INDICATION` | Program\|Trial → Disease | — |
| `TARGETS` | Program → Gene | — |
| `TESTED_IN` | Program → Trial | — |
| `ABOUT` | GapHypothesis → Program | — |
| `SUPPORTED_BY` | GapHypothesis → Trial\|Gene\|… | PROV support |
| `CONTRADICTED_BY` | GapHypothesis → Trial\|Gene\|… | PROV counter-evidence |
| `DERIVED_FROM` | GapHypothesis → Program\|Trial | lineage |
| `REVIEWS` | Review → GapHypothesis | HITL decision |

`evidence_json` holds a JSON array of `{evidence_type, source, score, study_id?}` — Open Targets–style decomposition.

GapForge details: [GAPFORGE.md](./GAPFORGE.md).

## Validation (ingest)

- Gene ids must match `^ENSG\d{11}$` (frozen catalog may include synthetic `OT####` placeholders for scale demos; production bulk ingest uses real Ensembl ids).
- Disease ids should be ontology-backed (`EFO_`, `MONDO_`, etc.).
- Association scores ∈ [0, 1].

## API surfaces

| Consumer need | Endpoint |
|---------------|----------|
| Ranked targets | `GET /genes/{id}/diseases`, `GET /diseases/{id}/genes` |
| Evidence breakdown | `GET /genes/{id}/evidence` |
| Federated identity | `GET /genes/{id}/external-links` |
| Entity resolution | `GET /resolve?query=&entity_type=gene\|disease` |
| Dataset trust | `GET /meta` |

## MCP mapping

| MCP tool | API |
|----------|-----|
| `get_target_evidence` | `/genes/{id}/evidence` |
| `get_gene_external_links` | `/genes/{id}/external-links` |
| `resolve_identifier` | `GET /resolve` |

See [SCHEMA_MIGRATION.md](./SCHEMA_MIGRATION.md) for Neo4j migration notes.

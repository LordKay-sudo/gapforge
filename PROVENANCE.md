# Data provenance

## Dataset

| Field | Value |
|-------|--------|
| **Data version** | `opentargets-24.06-frozen-slice-v2+gapforge-flurizan+astegolimab` |
| **Release date** | 2024-06-01 |
| **Scope** | Frozen slice: 500 genes, ~3,000 disease–target associations with decomposed evidence; plus GapForge educational case studies (Flurizan AD, Astegolimab COPD) |
| **Inspiration** | [Open Targets Platform](https://platform.opentargets.org/) association + evidence model |

## GapForge case studies

| Field | Value |
|-------|--------|
| **Seed files** | `data/gapforge/*.json` (Flurizan + Astegolimab) |
| **Loader** | `scripts/seed_gapforge.py` (also invoked at end of `seed_neo4j.py`) |
| **Framing** | Historical educational hypotheses — not clinical advice |
| **Public refs** | ClinicalTrials.gov; PMC / public trial-design discussion |

## Bulk ingest source (production path)

| Field | Value |
|-------|--------|
| **Provider** | Open Targets Platform (EMBL-EBI & Wellcome Sanger Institute) |
| **Release pinned** | **24.06** (June 2024) |
| **FTP base** | `https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/24.06/output/etl/json/` |
| **Association file** | `associationByOverallDirect` — target–disease scores |
| **Evidence file** | `evidence` — datatype + datasource rows per association |
| **Documentation** | [Open Targets datasets](https://platform-docs.opentargets.org/data-access/datasets) |
| **Licence** | **CC0 1.0** for platform data ([terms](https://platform-docs.opentargets.org/licence)); cite Open Targets in publications |

### Download and load (full ingest)

```bash
py -3 scripts/download_opentargets_bulk.py --release 24.06 --max-genes 500
py -3 scripts/etl_opentargets.py --input data/raw/opentargets_bulk.json
py -3 scripts/seed_neo4j.py
```

### Frozen slice (CI / offline demo)

CI and default Docker seed use a **deterministic frozen subset** derived from the same schema (not a live FTP pull):

```bash
py -3 scripts/build_frozen_slice.py   # writes data/raw/opentargets_slice_v2.json + processed CSV
py -3 scripts/seed_neo4j.py
```

Fixture copies for tests: `api/tests/fixtures/opentargets_slice_v2.json`, `api/tests/fixtures/gene_catalog.json`.

## Sources

- **Open Targets Platform 24.06** — bulk JSON/Parquet releases via EBI FTP  
  Licence: CC0 1.0; see [platform-docs.opentargets.org/licence](https://platform-docs.opentargets.org/licence)
- **Frozen slice v2** — reproducible subset for CI (see `scripts/build_frozen_slice.py`)

## Scientific scope

- Graph edges are **disease–target associations** with an overall **score** (0–1) plus **decomposed evidence** (`evidence_type`, `source`, optional `study_id`).
- Scores indicate **correlative strength** in curated public data, not causation, mechanism, or clinical actionability.
- This system does **not** provide diagnosis, treatment recommendations, or regulatory-grade evidence.

## Schema

Relationship properties on `ASSOCIATED_WITH`: `score`, `source`, `evidence_type`, `evidence_json`, optional `study_id`.  
See [docs/SCHEMA_MIGRATION.md](docs/SCHEMA_MIGRATION.md).

## API

Live metadata: `GET /api/v1/meta` (also exposed as MCP resource `bioinsight://meta` when using [embabel-mcp](https://github.com/LordKay-sudo/embabel-mcp)).

Evidence breakdown: `GET /api/v1/genes/{id}/evidence` (consumed by embabel-mcp `get_target_evidence`).

## Citations

If you reference this graph in a write-up, cite Open Targets and note the release/slice:

> Open Targets Platform, EMBL-EBI & Wellcome Sanger Institute. Release 24.06 (or frozen slice v2 for demo/CI).

## Updates

When ingesting a new Open Targets release:

1. Update `scripts/download_opentargets_bulk.py` default `--release`
2. Update `api/app/metadata.py` (`DATA_VERSION`, `RELEASE_DATE`, `SOURCES`)
3. Update this file and re-run ETL + `scripts/seed_neo4j.py`

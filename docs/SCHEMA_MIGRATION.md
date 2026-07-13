# Neo4j schema migration — evidence on `ASSOCIATED_WITH`

## P0 task 1.2

### Relationship: `(:Gene)-[:ASSOCIATED_WITH]->(:Disease)`

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `score` | float | yes | Overall association score (0–1), aligned with Open Targets `associationScore` |
| `source` | string | yes | Dataset identifier, e.g. `opentargets` |
| `evidence_type` | string | yes | Primary datatype for the edge (highest-scoring evidence row) |
| `evidence_json` | string (JSON) | yes | JSON array of decomposed evidence rows (see below) |
| `study_id` | string | no | Optional top study / GWAS catalog ID when applicable |

### Evidence row shape (`evidence_json` array elements)

```json
{
  "evidence_type": "genetic_association",
  "source": "gwas_catalog",
  "score": 0.42,
  "study_id": "GCST90002357"
}
```

`evidence_type` values follow [Open Targets evidence datatypes](https://platform-docs.opentargets.org/data-access/datasets#evidence) (`genetic_association`, `somatic_mutation`, `known_drug`, `literature`, `rna_expression`, `animal_model`, …).

### Migration from demo v1

Previous demo edges stored only `score` and `source = opentargets_sample`.

1. Re-run ETL + seed (no in-place migration script required for demo deployments):

   ```bash
   python scripts/build_frozen_slice.py   # or scripts/download_opentargets_bulk.py + scripts/etl_opentargets.py
   python scripts/etl_opentargets.py
   python scripts/seed_neo4j.py
   ```

2. `seed_neo4j.py` clears the graph and reloads from `data/processed/associations.csv`.

3. API clients should read typed evidence via `evidence` arrays on ranked association responses or `GET /api/v1/genes/{id}/evidence`.

### Constraints

Node uniqueness constraints are unchanged (`scripts/neo4j/init.cypher`).

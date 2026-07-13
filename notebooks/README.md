# Notebooks

| Notebook | Roadmap | Description |
|----------|---------|-------------|
| [one_gene_exploration.ipynb](./one_gene_exploration.ipynb) | **4.4** | One gene (BRCA1) → REST + optional Neo4j Cypher + literature links |

## Quick start

From the repo root, with the stack running (`docker compose up` — see [GETTING_STARTED.md](../docs/GETTING_STARTED.md)):

```bash
cd api
py -3 -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt -r ../notebooks/requirements.txt
jupyter notebook ../notebooks/one_gene_exploration.ipynb
```

API base URL defaults to `http://localhost:8000/api/v1`. Override with `BIOINSIGHT_API_URL` if needed.

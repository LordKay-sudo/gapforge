"""One-off helper to regenerate api/tests/fixtures/gene_catalog.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "api" / "tests" / "fixtures" / "gene_catalog.json"

REAL = [
    ("ENSG00000012048", "BRCA1", "BRCA1 DNA repair associated"),
    ("ENSG00000139618", "BRCA2", "BRCA2 DNA repair associated"),
    ("ENSG00000141510", "TP53", "tumor protein p53"),
    ("ENSG00000171862", "PTEN", "phosphatase and tensin homolog"),
    ("ENSG00000157764", "BRAF", "B-Raf proto-oncogene"),
    ("ENSG00000133703", "KRAS", "KRAS proto-oncogene"),
    ("ENSG00000146648", "EGFR", "epidermal growth factor receptor"),
    ("ENSG00000140443", "CFTR", "CF transmembrane conductance regulator"),
    ("ENSG00000130203", "APOE", "apolipoprotein E"),
    ("ENSG00000198947", "DMD", "dystrophin"),
]

genes = [{"target_id": t, "symbol": s, "name": n} for t, s, n in REAL]
seen = {g["target_id"] for g in genes}
for i in range(1, 600):
    ens = "ENSG" + str(i).zfill(11)
    if ens in seen:
        continue
    genes.append({"target_id": ens, "symbol": f"OT{i:04d}", "name": f"Open Targets catalog gene {i}"})
    seen.add(ens)
    if len(genes) >= 500:
        break

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(genes, indent=2), encoding="utf-8")
print(f"Wrote {len(genes)} genes to {OUT}")

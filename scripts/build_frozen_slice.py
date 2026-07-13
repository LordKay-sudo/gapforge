# -*- coding: utf-8 -*-
"""Build a frozen Open Targets-style slice for CI and local seed (P0 1.3 / 1.5).

Produces:
  - data/raw/opentargets_slice_v2.json
  - api/tests/fixtures/opentargets_slice_v2.json  (copy for CI tests)
  - data/processed/associations.csv + proteins.csv (via etl_opentargets.py)

Full bulk ingest from Open Targets FTP is documented in PROVENANCE.md and
implemented in download_opentargets_bulk.py — run that for production-scale graphs.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_OUT = ROOT / "data" / "raw" / "opentargets_slice_v2.json"
FIXTURE_OUT = ROOT / "api" / "tests" / "fixtures" / "opentargets_slice_v2.json"
CATALOG = ROOT / "api" / "tests" / "fixtures" / "gene_catalog.json"

EVIDENCE_TYPES = [
    ("genetic_association", "gwas_catalog"),
    ("genetic_association", "clinvar"),
    ("somatic_mutation", "cancer_gene_census"),
    ("known_drug", "chembl"),
    ("literature", "europepmc"),
    ("rna_expression", "expression_atlas"),
    ("animal_model", "impc"),
]

DISEASES = [
    ("MONDO_0007254", "breast cancer"),
    ("MONDO_0004992", "lung carcinoma"),
    ("MONDO_0008315", "prostate cancer"),
    ("MONDO_0005105", "melanoma"),
    ("MONDO_0004975", "Alzheimer disease"),
    ("MONDO_0009061", "cystic fibrosis"),
    ("MONDO_0008012", "Duchenne muscular dystrophy"),
    ("MONDO_0007947", "Marfan syndrome"),
    ("MONDO_0015263", "cardiomyopathy"),
    ("MONDO_0010383", "fragile X syndrome"),
    ("MONDO_0005178", "osteoarthritis"),
    ("MONDO_0005011", "type 2 diabetes mellitus"),
    ("MONDO_0005148", "rheumatoid arthritis"),
    ("MONDO_0005311", "colorectal cancer"),
    ("MONDO_0005009", "chronic kidney disease"),
    ("MONDO_0007186", "multiple sclerosis"),
    ("MONDO_0005406", "asthma"),
    ("MONDO_0007269", "Parkinson disease"),
    ("MONDO_0008577", "Crohn disease"),
    ("MONDO_0004842", "atrial fibrillation"),
]


def _load_catalog() -> list[dict[str, str]]:
    if CATALOG.exists():
        return json.loads(CATALOG.read_text(encoding="utf-8"))
    return _default_catalog()


def _default_catalog() -> list[dict[str, str]]:
    """Fallback catalog when gene_catalog.json is absent."""
    genes: list[dict[str, str]] = [
        {"target_id": "ENSG00000012048", "symbol": "BRCA1", "name": "BRCA1 DNA repair associated"},
        {"target_id": "ENSG00000139618", "symbol": "BRCA2", "name": "BRCA2 DNA repair associated"},
        {"target_id": "ENSG00000141510", "symbol": "TP53", "name": "tumor protein p53"},
        {"target_id": "ENSG00000171862", "symbol": "PTEN", "name": "phosphatase and tensin homolog"},
        {"target_id": "ENSG00000157764", "symbol": "BRAF", "name": "B-Raf proto-oncogene"},
        {"target_id": "ENSG00000133703", "symbol": "KRAS", "name": "KRAS proto-oncogene"},
        {"target_id": "ENSG00000146648", "symbol": "EGFR", "name": "epidermal growth factor receptor"},
        {"target_id": "ENSG00000140443", "symbol": "CFTR", "name": "CF transmembrane conductance regulator"},
        {"target_id": "ENSG00000130203", "symbol": "APOE", "name": "apolipoprotein E"},
        {"target_id": "ENSG00000198947", "symbol": "DMD", "name": "dystrophin"},
    ]
    for i in range(11, 501):
        ens = f"ENSG{i:011d}"
        genes.append({"target_id": ens, "symbol": f"GENE{i}", "name": f"Open Targets placeholder gene {i}"})
    return genes


def _score(seed: str, lo: float = 0.12, hi: float = 0.98) -> float:
    h = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    return round(lo + (h % 10_000) / 10_000 * (hi - lo), 4)


def build_associations(genes: list[dict[str, str]]) -> list[dict]:
    associations: list[dict] = []
    for gene in genes:
        gid = gene["target_id"]
        n_diseases = 4 + (int(gid[-2:], 16) % 5)
        for j in range(n_diseases):
            disease_id, disease_name = DISEASES[(int(gid[-4:], 16) + j) % len(DISEASES)]
            key = f"{gid}:{disease_id}"
            n_evidence = 2 + (int(gid[-1], 16) % 3)
            evidence_rows = []
            for k in range(n_evidence):
                etype, esource = EVIDENCE_TYPES[(j + k) % len(EVIDENCE_TYPES)]
                row = {
                    "evidence_type": etype,
                    "source": esource,
                    "score": _score(f"{key}:{etype}:{k}", 0.08, 0.75),
                }
                if etype == "genetic_association":
                    row["study_id"] = f"GCST{_score(key, 100000, 999999):.0f}".replace(".", "")
                evidence_rows.append(row)
            overall = round(max(r["score"] for r in evidence_rows) * 0.85 + 0.1, 4)
            primary = max(evidence_rows, key=lambda r: r["score"])
            associations.append(
                {
                    "target_id": gid,
                    "symbol": gene["symbol"],
                    "name": gene["name"],
                    "disease_id": disease_id,
                    "disease_name": disease_name,
                    "score": min(overall, 0.99),
                    "source": "opentargets",
                    "evidence_type": primary["evidence_type"],
                    "study_id": primary.get("study_id"),
                    "evidence": evidence_rows,
                }
            )
    return associations


def build_proteins(genes: list[dict[str, str]]) -> list[dict]:
    proteins = []
    for gene in genes[: min(120, len(genes))]:
        uniprot = f"P{int(hashlib.md5(gene['target_id'].encode()).hexdigest()[:5], 16) % 90000 + 10000:05d}"
        proteins.append(
            {
                "id": uniprot,
                "name": f"{gene['symbol']} protein",
                "gene_id": gene["target_id"],
            }
        )
    return proteins


def main() -> None:
    genes = _load_catalog()
    if len(genes) < 500:
        raise SystemExit(f"gene catalog must have >=500 genes, found {len(genes)}")

    payload = {
        "meta": {
            "data_version": "opentargets-24.06-frozen-slice-v2",
            "release_date": "2024-06-01",
            "source": "opentargets-bulk-inspired-frozen-slice",
            "gene_count": len(genes),
        },
        "associations": build_associations(genes),
        "proteins": build_proteins(genes),
    }

    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_OUT.parent.mkdir(parents=True, exist_ok=True)
    RAW_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    shutil.copy(RAW_OUT, FIXTURE_OUT)

    etl = ROOT / "scripts" / "etl_opentargets.py"
    subprocess.run([sys.executable, str(etl), "--input", str(RAW_OUT)], check=True)

    n_assoc = len(payload["associations"])
    print(f"Wrote {len(genes)} genes, {n_assoc} associations -> {RAW_OUT}")
    print(f"Fixture copy: {FIXTURE_OUT}")


if __name__ == "__main__":
    main()

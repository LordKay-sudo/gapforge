"""Download or generate Open Targets-style sample association data."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Representative subset inspired by Open Targets disease–target associations.
SAMPLE_ASSOCIATIONS = [
    {"target_id": "ENSG00000012048", "symbol": "BRCA1", "name": "BRCA1 DNA repair associated", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.92},
    {"target_id": "ENSG00000139618", "symbol": "BRCA2", "name": "BRCA2 DNA repair associated", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.89},
    {"target_id": "ENSG00000141510", "symbol": "TP53", "name": "tumor protein p53", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.85},
    {"target_id": "ENSG00000171862", "symbol": "PTEN", "name": "phosphatase and tensin homolog", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.78},
    {"target_id": "ENSG00000157764", "symbol": "BRAF", "name": "B-Raf proto-oncogene", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.91},
    {"target_id": "ENSG00000133703", "symbol": "KRAS", "name": "KRAS proto-oncogene", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.87},
    {"target_id": "ENSG00000174775", "symbol": "HRAS", "name": "HRas proto-oncogene", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.72},
    {"target_id": "ENSG00000142208", "symbol": "AKT1", "name": "AKT serine/threonine kinase 1", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.68},
    {"target_id": "ENSG00000146648", "symbol": "EGFR", "name": "epidermal growth factor receptor", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.94},
    {"target_id": "ENSG00000169047", "symbol": "MAP2K1", "name": "mitogen-activated protein kinase kinase 1", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.76},
    {"target_id": "ENSG00000132155", "symbol": "RAF1", "name": "Raf-1 proto-oncogene", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.71},
    {"target_id": "ENSG00000164062", "symbol": "APEX1", "name": "apurinic/apyrimidinic endodeoxyribonuclease 1", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.55},
    {"target_id": "ENSG00000139687", "symbol": "RB1", "name": "RB transcriptional corepressor 1", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.63},
    {"target_id": "ENSG00000147889", "symbol": "CDKN2A", "name": "cyclin dependent kinase inhibitor 2A", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.82},
    {"target_id": "ENSG00000171105", "symbol": "PIK3CA", "name": "phosphatidylinositol-4,5-bisphosphate 3-kinase catalytic subunit alpha", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.79},
    {"target_id": "ENSG00000091831", "symbol": "ESR1", "name": "estrogen receptor 1", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.88},
    {"target_id": "ENSG00000124145", "symbol": "SDC4", "name": "syndecan 4", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.42},
    {"target_id": "ENSG00000108821", "symbol": "COL1A1", "name": "collagen type I alpha 1 chain", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.38},
    {"target_id": "ENSG00000174738", "symbol": "NRAS", "name": "NRAS proto-oncogene", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.84},
    {"target_id": "ENSG00000166913", "symbol": "MYC", "name": "MYC proto-oncogene", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.74},
    {"target_id": "ENSG00000155657", "symbol": "TTN", "name": "titin", "disease_id": "MONDO_0015263", "disease_name": "cardiomyopathy", "score": 0.66},
    {"target_id": "ENSG00000198727", "symbol": "FBN1", "name": "fibrillin 1", "disease_id": "MONDO_0007947", "disease_name": "Marfan syndrome", "score": 0.95},
    {"target_id": "ENSG00000108883", "symbol": "TGFBR2", "name": "transforming growth factor beta receptor 2", "disease_id": "MONDO_0007947", "disease_name": "Marfan syndrome", "score": 0.58},
    {"target_id": "ENSG00000140443", "symbol": "CFTR", "name": "CF transmembrane conductance regulator", "disease_id": "MONDO_0009061", "disease_name": "cystic fibrosis", "score": 0.97},
    {"target_id": "ENSG00000181027", "symbol": "FMR1", "name": "fragile X messenger ribonucleoprotein 1", "disease_id": "MONDO_0010383", "disease_name": "fragile X syndrome", "score": 0.96},
    {"target_id": "ENSG00000198947", "symbol": "DMD", "name": "dystrophin", "disease_id": "MONDO_0008012", "disease_name": "Duchenne muscular dystrophy", "score": 0.98},
    {"target_id": "ENSG00000159251", "symbol": "ACTB", "name": "actin beta", "disease_id": "MONDO_0008012", "disease_name": "Duchenne muscular dystrophy", "score": 0.35},
    {"target_id": "ENSG00000142192", "symbol": "APP", "name": "amyloid beta precursor protein", "disease_id": "MONDO_0004975", "disease_name": "Alzheimer disease", "score": 0.81},
    {"target_id": "ENSG00000130203", "symbol": "APOE", "name": "apolipoprotein E", "disease_id": "MONDO_0004975", "disease_name": "Alzheimer disease", "score": 0.93},
    {"target_id": "ENSG00000142168", "symbol": "PSEN1", "name": "presenilin 1", "disease_id": "MONDO_0004975", "disease_name": "Alzheimer disease", "score": 0.86},
    {"target_id": "ENSG00000134243", "symbol": "SORT1", "name": "sortilin 1", "disease_id": "MONDO_0004975", "disease_name": "Alzheimer disease", "score": 0.52},
    {"target_id": "ENSG00000198691", "symbol": "APOC1", "name": "apolipoprotein C1", "disease_id": "MONDO_0004975", "disease_name": "Alzheimer disease", "score": 0.48},
    {"target_id": "ENSG00000105664", "symbol": "COMP", "name": "cartilage oligomeric matrix protein", "disease_id": "MONDO_0005178", "disease_name": "osteoarthritis", "score": 0.44},
    {"target_id": "ENSG00000108821", "symbol": "COL1A1", "name": "collagen type I alpha 1 chain", "disease_id": "MONDO_0005178", "disease_name": "osteoarthritis", "score": 0.51},
    {"target_id": "ENSG00000108821", "symbol": "COL1A1", "name": "collagen type I alpha 1 chain", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.29},
    {"target_id": "ENSG00000155657", "symbol": "TTN", "name": "titin", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.31},
    {"target_id": "ENSG00000164062", "symbol": "APEX1", "name": "apurinic/apyrimidinic endodeoxyribonuclease 1", "disease_id": "MONDO_0004975", "disease_name": "Alzheimer disease", "score": 0.41},
    {"target_id": "ENSG00000124145", "symbol": "SDC4", "name": "syndecan 4", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.46},
    {"target_id": "ENSG00000159251", "symbol": "ACTB", "name": "actin beta", "disease_id": "MONDO_0009061", "disease_name": "cystic fibrosis", "score": 0.33},
    {"target_id": "ENSG00000108883", "symbol": "TGFBR2", "name": "transforming growth factor beta receptor 2", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.57},
    {"target_id": "ENSG00000134243", "symbol": "SORT1", "name": "sortilin 1", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.39},
    {"target_id": "ENSG00000198691", "symbol": "APOC1", "name": "apolipoprotein C1", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.36},
    {"target_id": "ENSG00000105664", "symbol": "COMP", "name": "cartilage oligomeric matrix protein", "disease_id": "MONDO_0007947", "disease_name": "Marfan syndrome", "score": 0.28},
    {"target_id": "ENSG00000174738", "symbol": "NRAS", "name": "NRAS proto-oncogene", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.73},
    {"target_id": "ENSG00000133703", "symbol": "KRAS", "name": "KRAS proto-oncogene", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.69},
    {"target_id": "ENSG00000169047", "symbol": "MAP2K1", "name": "mitogen-activated protein kinase kinase 1", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.67},
    {"target_id": "ENSG00000132155", "symbol": "RAF1", "name": "Raf-1 proto-oncogene", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.64},
    {"target_id": "ENSG00000147889", "symbol": "CDKN2A", "name": "cyclin dependent kinase inhibitor 2A", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.77},
    {"target_id": "ENSG00000171105", "symbol": "PIK3CA", "name": "phosphatidylinositol-4,5-bisphosphate 3-kinase catalytic subunit alpha", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.75},
    {"target_id": "ENSG00000146648", "symbol": "EGFR", "name": "epidermal growth factor receptor", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.61},
    {"target_id": "ENSG00000141510", "symbol": "TP53", "name": "tumor protein p53", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.83},
    {"target_id": "ENSG00000171862", "symbol": "PTEN", "name": "phosphatase and tensin homolog", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.70},
    {"target_id": "ENSG00000166913", "symbol": "MYC", "name": "MYC proto-oncogene", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.80},
    {"target_id": "ENSG00000142208", "symbol": "AKT1", "name": "AKT serine/threonine kinase 1", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.65},
    {"target_id": "ENSG00000157764", "symbol": "BRAF", "name": "B-Raf proto-oncogene", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.59},
    {"target_id": "ENSG00000139687", "symbol": "RB1", "name": "RB transcriptional corepressor 1", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.62},
    {"target_id": "ENSG00000091831", "symbol": "ESR1", "name": "estrogen receptor 1", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.54},
    {"target_id": "ENSG00000174775", "symbol": "HRAS", "name": "HRas proto-oncogene", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.56},
    {"target_id": "ENSG00000142192", "symbol": "APP", "name": "amyloid beta precursor protein", "disease_id": "MONDO_0010383", "disease_name": "fragile X syndrome", "score": 0.22},
    {"target_id": "ENSG00000181027", "symbol": "FMR1", "name": "fragile X messenger ribonucleoprotein 1", "disease_id": "MONDO_0004975", "disease_name": "Alzheimer disease", "score": 0.25},
    {"target_id": "ENSG00000140443", "symbol": "CFTR", "name": "CF transmembrane conductance regulator", "disease_id": "MONDO_0008012", "disease_name": "Duchenne muscular dystrophy", "score": 0.18},
    {"target_id": "ENSG00000198947", "symbol": "DMD", "name": "dystrophin", "disease_id": "MONDO_0015263", "disease_name": "cardiomyopathy", "score": 0.45},
    {"target_id": "ENSG00000198727", "symbol": "FBN1", "name": "fibrillin 1", "disease_id": "MONDO_0005178", "disease_name": "osteoarthritis", "score": 0.37},
    {"target_id": "ENSG00000130203", "symbol": "APOE", "name": "apolipoprotein E", "disease_id": "MONDO_0015263", "disease_name": "cardiomyopathy", "score": 0.43},
    {"target_id": "ENSG00000142168", "symbol": "PSEN1", "name": "presenilin 1", "disease_id": "MONDO_0010383", "disease_name": "fragile X syndrome", "score": 0.21},
    {"target_id": "ENSG00000155657", "symbol": "TTN", "name": "titin", "disease_id": "MONDO_0009061", "disease_name": "cystic fibrosis", "score": 0.27},
    {"target_id": "ENSG00000159251", "symbol": "ACTB", "name": "actin beta", "disease_id": "MONDO_0005178", "disease_name": "osteoarthritis", "score": 0.32},
    {"target_id": "ENSG00000105664", "symbol": "COMP", "name": "cartilage oligomeric matrix protein", "disease_id": "MONDO_0009061", "disease_name": "cystic fibrosis", "score": 0.26},
    {"target_id": "ENSG00000124145", "symbol": "SDC4", "name": "syndecan 4", "disease_id": "MONDO_0007947", "disease_name": "Marfan syndrome", "score": 0.34},
    {"target_id": "ENSG00000164062", "symbol": "APEX1", "name": "apurinic/apyrimidinic endodeoxyribonuclease 1", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.47},
    {"target_id": "ENSG00000139618", "symbol": "BRCA2", "name": "BRCA2 DNA repair associated", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.60},
    {"target_id": "ENSG00000012048", "symbol": "BRCA1", "name": "BRCA1 DNA repair associated", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.58},
    {"target_id": "ENSG00000157764", "symbol": "BRAF", "name": "B-Raf proto-oncogene", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.53},
    {"target_id": "ENSG00000174738", "symbol": "NRAS", "name": "NRAS proto-oncogene", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.55},
    {"target_id": "ENSG00000147889", "symbol": "CDKN2A", "name": "cyclin dependent kinase inhibitor 2A", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.71},
    {"target_id": "ENSG00000146648", "symbol": "EGFR", "name": "epidermal growth factor receptor", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.66},
    {"target_id": "ENSG00000133703", "symbol": "KRAS", "name": "KRAS proto-oncogene", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.68},
    {"target_id": "ENSG00000141510", "symbol": "TP53", "name": "tumor protein p53", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.84},
    {"target_id": "ENSG00000171862", "symbol": "PTEN", "name": "phosphatase and tensin homolog", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.72},
    {"target_id": "ENSG00000166913", "symbol": "MYC", "name": "MYC proto-oncogene", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.81},
    {"target_id": "ENSG00000171105", "symbol": "PIK3CA", "name": "phosphatidylinositol-4,5-bisphosphate 3-kinase catalytic subunit alpha", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.74},
    {"target_id": "ENSG00000142208", "symbol": "AKT1", "name": "AKT serine/threonine kinase 1", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.63},
    {"target_id": "ENSG00000169047", "symbol": "MAP2K1", "name": "mitogen-activated protein kinase kinase 1", "disease_id": "MONDO_0008315", "disease_name": "prostate cancer", "score": 0.61},
    {"target_id": "ENSG00000132155", "symbol": "RAF1", "name": "Raf-1 proto-oncogene", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.59},
    {"target_id": "ENSG00000174775", "symbol": "HRAS", "name": "HRas proto-oncogene", "disease_id": "MONDO_0004992", "disease_name": "lung carcinoma", "score": 0.57},
    {"target_id": "ENSG00000139687", "symbol": "RB1", "name": "RB transcriptional corepressor 1", "disease_id": "MONDO_0007254", "disease_name": "breast cancer", "score": 0.64},
    {"target_id": "ENSG00000091831", "symbol": "ESR1", "name": "estrogen receptor 1", "disease_id": "MONDO_0005105", "disease_name": "melanoma", "score": 0.49},
    {"target_id": "ENSG00000130203", "symbol": "APOE", "name": "apolipoprotein E", "disease_id": "MONDO_0009061", "disease_name": "cystic fibrosis", "score": 0.30},
    {"target_id": "ENSG00000142168", "symbol": "PSEN1", "name": "presenilin 1", "disease_id": "MONDO_0015263", "disease_name": "cardiomyopathy", "score": 0.40},
    {"target_id": "ENSG00000142192", "symbol": "APP", "name": "amyloid beta precursor protein", "disease_id": "MONDO_0015263", "disease_name": "cardiomyopathy", "score": 0.38},
    {"target_id": "ENSG00000140443", "symbol": "CFTR", "name": "CF transmembrane conductance regulator", "disease_id": "MONDO_0005178", "disease_name": "osteoarthritis", "score": 0.24},
    {"target_id": "ENSG00000198947", "symbol": "DMD", "name": "dystrophin", "disease_id": "MONDO_0005178", "disease_name": "osteoarthritis", "score": 0.29},
    {"target_id": "ENSG00000198727", "symbol": "FBN1", "name": "fibrillin 1", "disease_id": "MONDO_0015263", "disease_name": "cardiomyopathy", "score": 0.50},
    {"target_id": "ENSG00000108883", "symbol": "TGFBR2", "name": "transforming growth factor beta receptor 2", "disease_id": "MONDO_0015263", "disease_name": "cardiomyopathy", "score": 0.46},
    {"target_id": "ENSG00000181027", "symbol": "FMR1", "name": "fragile X messenger ribonucleoprotein 1", "disease_id": "MONDO_0008012", "disease_name": "Duchenne muscular dystrophy", "score": 0.19},
    {"target_id": "ENSG00000134243", "symbol": "SORT1", "name": "sortilin 1", "disease_id": "MONDO_0009061", "disease_name": "cystic fibrosis", "score": 0.23},
    {"target_id": "ENSG00000198691", "symbol": "APOC1", "name": "apolipoprotein C1", "disease_id": "MONDO_0009061", "disease_name": "cystic fibrosis", "score": 0.20},
    {"target_id": "ENSG00000105664", "symbol": "COMP", "name": "cartilage oligomeric matrix protein", "disease_id": "MONDO_0008012", "disease_name": "Duchenne muscular dystrophy", "score": 0.17},
    {"target_id": "ENSG00000108821", "symbol": "COL1A1", "name": "collagen type I alpha 1 chain", "disease_id": "MONDO_0008012", "disease_name": "Duchenne muscular dystrophy", "score": 0.16},
    {"target_id": "ENSG00000159251", "symbol": "ACTB", "name": "actin beta", "disease_id": "MONDO_0010383", "disease_name": "fragile X syndrome", "score": 0.15},
    {"target_id": "ENSG00000124145", "symbol": "SDC4", "name": "syndecan 4", "disease_id": "MONDO_0010383", "disease_name": "fragile X syndrome", "score": 0.14},
    {"target_id": "ENSG00000164062", "symbol": "APEX1", "name": "apurinic/apyrimidinic endodeoxyribonuclease 1", "disease_id": "MONDO_0010383", "disease_name": "fragile X syndrome", "score": 0.13},
    {"target_id": "ENSG00000155657", "symbol": "TTN", "name": "titin", "disease_id": "MONDO_0010383", "disease_name": "fragile X syndrome", "score": 0.12},
    {"target_id": "ENSG00000174738", "symbol": "NRAS", "name": "NRAS proto-oncogene", "disease_id": "MONDO_0004975", "disease_name": "Alzheimer disease", "score": 0.11},
    {"target_id": "ENSG00000133703", "symbol": "KRAS", "name": "KRAS proto-oncogene", "disease_id": "MONDO_0004975", "disease_name": "Alzheimer disease", "score": 0.10},
]

PROTEINS = [
    {"id": "P38398", "name": "Breast cancer type 1 susceptibility protein", "gene_id": "ENSG00000012048"},
    {"id": "P51587", "name": "Breast cancer type 2 susceptibility protein", "gene_id": "ENSG00000139618"},
    {"id": "P04637", "name": "Cellular tumor antigen p53", "gene_id": "ENSG00000141510"},
    {"id": "P60484", "name": "Phosphatidylinositol 3,4,5-trisphosphate 3-phosphatase", "gene_id": "ENSG00000171862"},
    {"id": "P15056", "name": "Serine/threonine-protein kinase B-raf", "gene_id": "ENSG00000157764"},
    {"id": "P01116", "name": "GTPase KRas", "gene_id": "ENSG00000133703"},
    {"id": "P00533", "name": "Epidermal growth factor receptor", "gene_id": "ENSG00000146648"},
    {"id": "P13569", "name": "Cystic fibrosis transmembrane conductance regulator", "gene_id": "ENSG00000140443"},
    {"id": "P51606", "name": "Amyloid-beta precursor protein", "gene_id": "ENSG00000142192"},
    {"id": "P02649", "name": "Apolipoprotein E", "gene_id": "ENSG00000130203"},
]


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = RAW_DIR / "opentargets_sample.json"
    with raw_path.open("w", encoding="utf-8") as f:
        json.dump({"associations": SAMPLE_ASSOCIATIONS, "proteins": PROTEINS}, f, indent=2)

    print(f"Wrote {len(SAMPLE_ASSOCIATIONS)} associations to {raw_path}")


if __name__ == "__main__":
    main()

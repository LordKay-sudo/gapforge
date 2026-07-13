import type {
  GeneDetail,
  GeneSummary,
  NeighborsResponse,
  StatsResponse,
  SubgraphResponse,
} from "../api/client";

export const DEMO_STATS: StatsResponse = {
  genes: 30,
  diseases: 12,
  proteins: 10,
  associations: 105,
};

export const DEMO_GENES: GeneSummary[] = [
  { id: "ENSG00000012048", symbol: "BRCA1", name: "BRCA1 DNA repair associated" },
  { id: "ENSG00000139618", symbol: "BRCA2", name: "BRCA2 DNA repair associated" },
  { id: "ENSG00000141510", symbol: "TP53", name: "tumor protein p53" },
  { id: "ENSG00000146648", symbol: "EGFR", name: "epidermal growth factor receptor" },
  { id: "ENSG00000157764", symbol: "BRAF", name: "B-Raf proto-oncogene" },
];

export const DEMO_GENE_DETAIL: GeneDetail = {
  id: "ENSG00000012048",
  symbol: "BRCA1",
  name: "BRCA1 DNA repair associated",
  disease_count: 4,
  protein_count: 1,
};

export const DEMO_SUBGRAPH: SubgraphResponse = {
  gene_id: "ENSG00000012048",
  nodes: [
    { id: "ENSG00000012048", label: "Gene", symbol: "BRCA1", name: "BRCA1 DNA repair associated" },
    { id: "MONDO_0007254", label: "Disease", name: "breast cancer" },
    { id: "MONDO_0004992", label: "Disease", name: "lung carcinoma" },
    { id: "MONDO_0008315", label: "Disease", name: "prostate cancer" },
    { id: "P38398", label: "Protein", name: "Breast cancer type 1 susceptibility protein" },
  ],
  links: [
    { source: "ENSG00000012048", target: "MONDO_0007254", type: "ASSOCIATED_WITH", score: 0.92 },
    { source: "ENSG00000012048", target: "MONDO_0004992", type: "ASSOCIATED_WITH", score: 0.58 },
    { source: "ENSG00000012048", target: "MONDO_0008315", type: "ASSOCIATED_WITH", score: 0.7 },
    { source: "P38398", target: "ENSG00000012048", type: "ENCODED_BY", score: null },
  ],
};

export const DEMO_NEIGHBORS: NeighborsResponse = {
  gene_id: DEMO_SUBGRAPH.gene_id,
  nodes: DEMO_SUBGRAPH.nodes,
  edges: DEMO_SUBGRAPH.links.map((l) => ({
    source: l.source,
    target: l.target,
    type: l.type,
    score: l.score,
  })),
};

export function filterDemoGenes(q: string): GeneSummary[] {
  const lower = q.toLowerCase();
  return DEMO_GENES.filter(
    (g) =>
      g.symbol.toLowerCase().includes(lower) ||
      (g.name ?? "").toLowerCase().includes(lower)
  );
}

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export interface GeneSummary {
  id: string;
  symbol: string;
  name?: string | null;
}

export interface DiseaseSummary {
  id: string;
  name: string;
}

export interface GeneDetail extends GeneSummary {
  disease_count: number;
  protein_count: number;
}

export interface NeighborNode {
  id: string;
  label: string;
  name?: string | null;
  symbol?: string | null;
}

export interface NeighborEdge {
  source: string;
  target: string;
  type: string;
  score?: number | null;
}

export interface NeighborsResponse {
  gene_id: string;
  nodes: NeighborNode[];
  edges: NeighborEdge[];
}

export interface StatsResponse {
  genes: number;
  diseases: number;
  proteins: number;
  associations: number;
}

export interface MetaResponse {
  service: string;
  api_version: string;
  data_version: string;
  release_date: string;
  disclaimer: string;
  associations_are_correlative: boolean;
}

export interface DiseaseDetail extends DiseaseSummary {
  gene_count: number;
}

export interface ScoredGeneTarget {
  gene_id: string;
  symbol: string;
  name?: string | null;
  score: number;
  source?: string | null;
  evidence: EvidenceItem[];
}

export interface DiseaseGenesResponse {
  disease_id: string;
  disease_name: string;
  min_score: number;
  genes: ScoredGeneTarget[];
}

export interface ScoredDiseaseAssociation {
  disease_id: string;
  name: string;
  score: number;
  source?: string | null;
  evidence: EvidenceItem[];
}

export interface GeneCompareSummary {
  gene_id: string;
  symbol: string;
  name?: string | null;
  disease_count: number;
  top_diseases: ScoredDiseaseAssociation[];
}

export interface CompareGenesResponse {
  symbols: string[];
  genes: GeneCompareSummary[];
  overlapping_disease_names: string[];
}

export interface SubgraphNode {
  id: string;
  label: string;
  name?: string | null;
  symbol?: string | null;
}

export interface SubgraphLink {
  source: string;
  target: string;
  type: string;
  score?: number | null;
}

export interface SubgraphResponse {
  gene_id: string;
  nodes: SubgraphNode[];
  links: SubgraphLink[];
}

export interface EvidenceItem {
  evidence_type: string;
  source: string;
  score: number;
  study_id?: string | null;
}

export interface AssociationEvidenceBundle {
  disease_id: string;
  disease_name: string;
  score: number;
  source: string;
  evidence: EvidenceItem[];
}

export interface GeneEvidenceResponse {
  gene_id: string;
  symbol: string;
  disease_id?: string | null;
  evidence: AssociationEvidenceBundle[];
}

export interface ExternalLink {
  label: string;
  provider: string;
  url: string;
}

export interface GeneExternalLinksResponse {
  gene_id: string;
  symbol: string;
  links: ExternalLink[];
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  searchGenes: (q: string) =>
    fetchJson<GeneSummary[]>(`/api/v1/genes?q=${encodeURIComponent(q)}`),
  searchDiseases: (q: string) =>
    fetchJson<DiseaseSummary[]>(`/api/v1/diseases?q=${encodeURIComponent(q)}`),
  getGene: (id: string) => fetchJson<GeneDetail>(`/api/v1/genes/${encodeURIComponent(id)}`),
  getNeighbors: (id: string) =>
    fetchJson<NeighborsResponse>(`/api/v1/genes/${encodeURIComponent(id)}/neighbors`),
  getStats: () => fetchJson<StatsResponse>("/api/v1/stats"),
  getSubgraph: (geneId: string) =>
    fetchJson<SubgraphResponse>(
      `/api/v1/export/subgraph?gene_id=${encodeURIComponent(geneId)}`
    ),
  health: () => fetchJson<{ status: string; neo4j: boolean }>("/api/v1/health"),
  getMeta: () => fetchJson<MetaResponse>("/api/v1/meta"),
  getGeneEvidence: (id: string, limit = 15) =>
    fetchJson<GeneEvidenceResponse>(
      `/api/v1/genes/${encodeURIComponent(id)}/evidence?limit=${limit}`
    ),
  getGeneExternalLinks: (id: string) =>
    fetchJson<GeneExternalLinksResponse>(
      `/api/v1/genes/${encodeURIComponent(id)}/external-links`
    ),
  getDisease: (id: string) =>
    fetchJson<DiseaseDetail>(`/api/v1/diseases/${encodeURIComponent(id)}`),
  getDiseaseGenes: (id: string, minScore = 0, limit = 25) =>
    fetchJson<DiseaseGenesResponse>(
      `/api/v1/diseases/${encodeURIComponent(id)}/genes?min_score=${minScore}&limit=${limit}`
    ),
  compareGenes: (symbols: string[], topN = 5) =>
    fetchJson<CompareGenesResponse>(
      `/api/v1/genes/compare?symbols=${encodeURIComponent(symbols.join(","))}&top_n=${topN}`
    ),
  geneReportUrl: (id: string, format: "json" | "tsv" = "tsv") =>
    `${API_BASE}/api/v1/export/gene-report?gene_id=${encodeURIComponent(id)}&format=${format}`,

  // GapForge
  listPrograms: () => fetchJson<ProgramSummary[]>("/api/v1/programs"),
  getProgram: (id: string) =>
    fetchJson<ProgramDetail>(`/api/v1/programs/${encodeURIComponent(id)}`),
  getProgramDossier: (id: string) =>
    fetchJson<ProgramDossier>(`/api/v1/programs/${encodeURIComponent(id)}/dossier`),
  getProgramTaxonomy: (id: string) =>
    fetchJson<ProgramTaxonomy>(`/api/v1/programs/${encodeURIComponent(id)}/taxonomy`),
  listGaps: (programId?: string, status?: string) => {
    const q = new URLSearchParams();
    if (programId) q.set("program_id", programId);
    if (status) q.set("status", status);
    const qs = q.toString();
    return fetchJson<GapHypothesisSummary[]>(`/api/v1/gaps${qs ? `?${qs}` : ""}`);
  },
  getGap: (id: string) => fetchJson<GapHypothesisDetail>(`/api/v1/gaps/${encodeURIComponent(id)}`),
  runCritic: (id: string, extra?: string) =>
    fetch(`${API_BASE}/api/v1/gaps/${encodeURIComponent(id)}/critic`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(extra ? { extra_counter_evidence: extra } : {}),
    }).then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json() as Promise<CriticResponse>;
    }),
  reviewQueue: (status = "needs_review") =>
    fetchJson<ReviewQueueItem[]>(
      `/api/v1/reviews/queue?status=${encodeURIComponent(status)}`
    ),
  decideReview: (gapId: string, decision: string, reviewer: string, notes: string) =>
    fetch(`${API_BASE}/api/v1/reviews/${encodeURIComponent(gapId)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, reviewer, notes }),
    }).then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json() as Promise<ReviewDecisionResponse>;
    }),
  reviewBundleUrl: (programId: string) =>
    `${API_BASE}/api/v1/export/review-bundle?program_id=${encodeURIComponent(programId)}`,
  discern: (body: DiscernRequest) =>
    fetch(`${API_BASE}/api/v1/discern`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json() as Promise<DiscernResult>;
    }),
  discernPolicy: (riskTier = "L2") =>
    fetchJson<Record<string, unknown>>(
      `/api/v1/discern/policy?risk_tier=${encodeURIComponent(riskTier)}`
    ),
};

export interface ProgramSummary {
  id: string;
  name: string;
  status?: string | null;
  indication_name?: string | null;
  moa?: string | null;
  stall_summary?: string | null;
  drug_name?: string | null;
  trial_count: number;
  gap_count: number;
}

export interface TrialSummary {
  id: string;
  nct_id?: string | null;
  phase?: string | null;
  status?: string | null;
  primary_endpoint?: string | null;
  outcome_summary?: string | null;
  url?: string | null;
}

export interface DimensionScore {
  score: number;
  threshold: number;
  passed: boolean;
}

export interface DiscernReason {
  code: string;
  severity: string;
  message: string;
  dimension?: string | null;
  evidence_span?: string | null;
}

export interface DiscernResult {
  overall: string;
  action: string;
  scores: Record<string, DimensionScore>;
  reasons: DiscernReason[];
  policy_version: string;
  risk_tier: string;
  artifact_type: string;
  cou?: string | null;
  provenance_hash: string;
  note?: string | null;
}

export interface DiscernRequest {
  artifact_type: string;
  risk_tier?: string;
  cou?: string | null;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  dimensions?: string[];
  thresholds?: Record<string, number>;
}

export interface GapHypothesisSummary {
  id: string;
  gap_class: string;
  claim: string;
  confidence: number;
  status: string;
  risk_tier: string;
  insufficient_evidence: boolean;
  program_id?: string | null;
  suggested_experiment?: string | null;
  provenance_hash?: string | null;
  critic_notes?: string | null;
  literature_refs: Array<{ title?: string; url?: string; note?: string }>;
  discern?: DiscernResult | null;
}

export interface GapHypothesisDetail extends GapHypothesisSummary {
  program_name?: string | null;
  cou?: string | null;
  critic_confidence?: number | null;
  supported_by: unknown[];
  contradicted_by: unknown[];
  reviews: unknown[];
}

export interface ProgramDetail extends ProgramSummary {
  cou_note?: string | null;
  case_study_id?: string | null;
  drug?: {
    id: string;
    name: string;
    synonyms: string[];
    chembl_id?: string | null;
  } | null;
  disease?: { id: string; name?: string } | null;
  genes: Array<{ id?: string; symbol?: string; name?: string }>;
  trials: TrialSummary[];
  gaps: GapHypothesisSummary[];
}

export interface ProgramDossier {
  program: ProgramDetail;
  cou: string;
  risk_tier_note: string;
  verify_ui_path: string;
}

export interface ProgramTaxonomy {
  program_id: string;
  program_name: string;
  dimensions: Array<{ code: string; label: string; evidence_density: number }>;
  note?: string | null;
}

export interface ReviewQueueItem {
  hypothesis: GapHypothesisSummary;
  program_id: string;
  program_name?: string | null;
  verify_ui_path: string;
}

export interface CriticResponse {
  gap_id: string;
  critic_notes: string;
  confidence_after: number;
  status: string;
  cou: string;
  ran_at: string;
  discern?: DiscernResult | null;
}

export interface ReviewDecisionResponse {
  gap_id: string;
  review_id: string;
  decision: string;
  status: string;
  reviewer: string;
  decided_at: string;
  message: string;
  cou: string;
}

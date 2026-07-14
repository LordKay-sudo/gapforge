from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    neo4j: bool


class GeneSummary(BaseModel):
    id: str
    symbol: str
    name: str | None = None


class DiseaseSummary(BaseModel):
    id: str
    name: str


class GeneDetail(GeneSummary):
    disease_count: int = 0
    protein_count: int = 0


class DiseaseDetail(DiseaseSummary):
    gene_count: int = 0


class EvidenceItem(BaseModel):
    evidence_type: str
    source: str
    score: float = Field(ge=0.0, le=1.0)
    study_id: str | None = None


class ScoredGeneTarget(BaseModel):
    gene_id: str
    symbol: str
    name: str | None = None
    score: float
    source: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)


class ScoredDiseaseAssociation(BaseModel):
    disease_id: str
    name: str
    score: float
    source: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)


class AssociationEvidenceBundle(BaseModel):
    disease_id: str
    disease_name: str
    score: float
    source: str
    evidence: list[EvidenceItem] = Field(default_factory=list)


class GeneEvidenceResponse(BaseModel):
    gene_id: str
    symbol: str
    disease_id: str | None = None
    evidence: list[AssociationEvidenceBundle] = Field(default_factory=list)


class DiseaseGenesResponse(BaseModel):
    disease_id: str
    disease_name: str
    min_score: float
    genes: list[ScoredGeneTarget]


class GeneDiseasesResponse(BaseModel):
    gene_id: str
    symbol: str
    min_score: float
    diseases: list[ScoredDiseaseAssociation]


class GeneCompareSummary(BaseModel):
    gene_id: str
    symbol: str
    name: str | None = None
    disease_count: int = 0
    top_diseases: list[ScoredDiseaseAssociation] = Field(default_factory=list)


class CompareGenesResponse(BaseModel):
    symbols: list[str]
    genes: list[GeneCompareSummary]
    overlapping_disease_names: list[str] = Field(default_factory=list)


class NeighborNode(BaseModel):
    id: str
    label: str
    name: str | None = None
    symbol: str | None = None


class NeighborEdge(BaseModel):
    source: str
    target: str
    type: str
    score: float | None = None


class NeighborsResponse(BaseModel):
    gene_id: str
    nodes: list[NeighborNode]
    edges: list[NeighborEdge]


class StatsResponse(BaseModel):
    genes: int
    diseases: int
    proteins: int
    associations: int


class DataSourceMeta(BaseModel):
    name: str
    url: str
    license: str | None = None


class MetaResponse(BaseModel):
    service: str
    api_version: str
    data_version: str
    release_date: str
    sources: list[DataSourceMeta]
    disclaimer: str
    associations_are_correlative: bool = True
    provenance_doc: str = "PROVENANCE.md"
    web_ui_gene_path: str = "/gene/{gene_id}"


class SubgraphNode(BaseModel):
    id: str
    label: str
    name: str | None = None
    symbol: str | None = None


class SubgraphLink(BaseModel):
    source: str
    target: str
    type: str
    score: float | None = None


class SubgraphResponse(BaseModel):
    gene_id: str
    nodes: list[SubgraphNode]
    links: list[SubgraphLink]


class ExternalLink(BaseModel):
    label: str
    provider: str
    url: str


class GeneExternalLinksResponse(BaseModel):
    gene_id: str
    symbol: str
    links: list[ExternalLink] = Field(default_factory=list)


class BatchLookupRequest(BaseModel):
    queries: list[str] = Field(..., min_length=1, max_length=100)


class BatchLookupHit(BaseModel):
    query: str
    gene_id: str
    symbol: str
    name: str | None = None
    disease_count: int = 0


class BatchLookupResponse(BaseModel):
    hits: list[BatchLookupHit] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)


# --- GapForge ---


class DrugSummary(BaseModel):
    id: str
    name: str
    synonyms: list[str] = Field(default_factory=list)
    chembl_id: str | None = None


class TrialSummary(BaseModel):
    id: str
    nct_id: str | None = None
    phase: str | None = None
    status: str | None = None
    primary_endpoint: str | None = None
    outcome_summary: str | None = None
    url: str | None = None


class LiteratureRef(BaseModel):
    title: str
    url: str | None = None
    note: str | None = None


class GapHypothesisSummary(BaseModel):
    id: str
    gap_class: str
    claim: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: str = "needs_review"
    risk_tier: str = "L2"
    insufficient_evidence: bool = False
    program_id: str | None = None
    suggested_experiment: str | None = None
    provenance_hash: str | None = None
    critic_notes: str | None = None
    literature_refs: list = Field(default_factory=list)
    discern: dict | None = None


class GapHypothesisDetail(GapHypothesisSummary):
    program_name: str | None = None
    cou: str | None = None
    critic_confidence: float | None = None
    supported_by: list = Field(default_factory=list)
    contradicted_by: list = Field(default_factory=list)
    reviews: list = Field(default_factory=list)


class ProgramSummary(BaseModel):
    id: str
    name: str
    status: str | None = None
    indication_name: str | None = None
    moa: str | None = None
    stall_summary: str | None = None
    drug_name: str | None = None
    trial_count: int = 0
    gap_count: int = 0


class ProgramDetail(ProgramSummary):
    cou_note: str | None = None
    case_study_id: str | None = None
    drug: DrugSummary | None = None
    disease: dict | None = None
    genes: list = Field(default_factory=list)
    trials: list[TrialSummary] = Field(default_factory=list)
    gaps: list[GapHypothesisSummary] = Field(default_factory=list)


class ProgramDossier(BaseModel):
    program: ProgramDetail
    cou: str
    risk_tier_note: str
    verify_ui_path: str


class TaxonomyDimension(BaseModel):
    code: str
    label: str
    evidence_density: float = Field(ge=0.0, le=1.0)


class ProgramTaxonomy(BaseModel):
    program_id: str
    program_name: str
    dimensions: list[TaxonomyDimension]
    note: str | None = None


class ProposeGapsRequest(BaseModel):
    program_id: str
    gap_class: str
    claim: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    suggested_experiment: str | None = None
    insufficient_evidence: bool = False
    supported_by_trial_ids: list[str] = Field(default_factory=list)
    supported_by_gene_ids: list[str] = Field(default_factory=list)
    literature_refs: list[LiteratureRef] = Field(default_factory=list)
    id: str | None = None


class ProposeGapsResponse(BaseModel):
    hypothesis: GapHypothesisDetail
    message: str
    cou: str
    discern: dict | None = None


class CriticRequest(BaseModel):
    extra_counter_evidence: str | None = None
    link_trial_as_contradiction: str | None = None


class CriticResponse(BaseModel):
    gap_id: str
    critic_notes: str
    confidence_after: float
    status: str
    cou: str
    ran_at: str
    discern: dict | None = None


class ReviewQueueItem(BaseModel):
    hypothesis: GapHypothesisSummary
    program_id: str
    program_name: str | None = None
    verify_ui_path: str


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., description="approve | reject | request_more")
    reviewer: str | None = None
    notes: str | None = None


class ReviewDecisionResponse(BaseModel):
    gap_id: str
    review_id: str
    decision: str
    status: str
    reviewer: str
    decided_at: str
    message: str
    cou: str


class ReviewBundle(BaseModel):
    exported_at: str
    cou: str
    data_version: str
    api_version: str
    program_id: str | None = None
    program_name: str | None = None
    hypotheses: list[GapHypothesisSummary] = Field(default_factory=list)
    team_conclusions: list[GapHypothesisSummary] = Field(default_factory=list)
    disclaimer: str
    note: str | None = None
    raw_meta: dict = Field(default_factory=dict)


# --- Discern ---


class DiscernRequest(BaseModel):
    artifact_type: str = Field(
        ...,
        description="gap_hypothesis | rag_answer | mcp_tool_result | paper | generic",
    )
    risk_tier: str = Field(default="L2", description="L0 | L1 | L2 | L3")
    cou: str | None = None
    input: dict = Field(default_factory=dict)
    output: dict = Field(default_factory=dict)
    dimensions: list[str] | None = Field(
        default=None,
        description="Subset of compliance, reliability, provenance, safety_language",
    )
    thresholds: dict[str, float] | None = Field(
        default=None,
        description="Optional per-dimension threshold overrides [0,1]",
    )


class DimensionScore(BaseModel):
    score: float
    threshold: float
    passed: bool


class DiscernReason(BaseModel):
    code: str
    severity: str
    message: str
    dimension: str | None = None
    evidence_span: str | None = None


class DiscernResponse(BaseModel):
    overall: str
    action: str
    scores: dict[str, DimensionScore]
    reasons: list[DiscernReason]
    policy_version: str
    risk_tier: str
    artifact_type: str
    cou: str | None = None
    provenance_hash: str
    note: str | None = None

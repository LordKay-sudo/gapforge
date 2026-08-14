# MCP tool session — 2026-08-14T09:32:10Z (UTC)

Endpoint: http://127.0.0.1:1337/sse

## bioinsight_health

```json
{
  "format": "json"
}
```

{"status":"ok","neo4j":true}

---

## plan_gap_investigation

```json
{
  "question": "Why did the Flurizan AD program stall?",
  "programId": "prog-flurizan-ad",
  "format": "markdown"
}
```

## Gap investigation plan

## Investigation plan

- **Intent:** `GAP_INVESTIGATION`
- **Question:** Why did the Flurizan AD program stall?

### Tool sequence

1. `plan_gap_investigation`
1. `build_program_dossier`
1. `propose_gap_hypotheses`
1. `run_critic`
1. `discern_artifact`
1. `run_gap_discern`
1. `run_gap_ontology_validate`
1. `export_review_bundle`
1. `export_approved_rdf`

### Stop rules

- Do not approve L2 hypotheses via MCP — use web HITL review queue
- Do not invent chemistry, doses, or patient advice (L3 blocked)
- If dual-channel evidence missing, set insufficient_evidence=true
- Always run critic, run_gap_discern, and run_gap_ontology_validate before asking a human to approve
- If discern action=block or OntoHarness conforms=false, do not present as a team conclusion


**COU:** Generate literature-backed gap hypotheses for scientific discussion; not for clinical care or regulatory submission.

---

## build_program_dossier

```json
{
  "programId": "prog-flurizan-ad",
  "format": "markdown"
}
```

# Program dossier

```json
{
  "program" : {
    "id" : "prog-flurizan-ad",
    "name" : "Flurizan AD program",
    "status" : "discontinued",
    "indication_name" : "Alzheimer disease",
    "moa" : "Gamma-secretase modulator (NSAID-derived); intended to reduce amyloidogenic Aβ42 processing",
    "stall_summary" : "Phase 3 trial in mild AD failed co-primary cognitive and functional endpoints; development discontinued.",
    "drug_name" : "tarenflurbil",
    "trial_count" : 1,
    "gap_count" : 4,
    "cou_note" : "Educational GapForge case study — hypotheses for scientific discussion only",
    "case_study_id" : "case-flurizan-ad",
    "drug" : {
      "id" : "drug-tarenflurbil",
      "name" : "tarenflurbil",
      "synonyms" : [ "Flurizan", "MPC-7869", "(R)-flurbiprofen" ],
      "chembl_id" : "CHEMBL2103838"
    },
    "disease" : {
      "id" : "MONDO_0004975",
      "name" : "Alzheimer disease"
    },
    "genes" : [ {
      "name" : "apolipoprotein E",
      "symbol" : "APOE",
      "id" : "ENSG00000130203"
    } ],
    "trials" : [ {
      "id" : "trial-flurizan-p3",
      "nct_id" : "NCT00105547",
      "phase" : "Phase 3",
      "status" : "Completed — primary endpoints not met",
      "primary_endpoint" : "ADAS-Cog and ADCS-ADL over ~18 months",
      "outcome_summary" : "No statistically significant efficacy vs placebo on co-primary endpoints in mild AD population; program discontinued.",
      "url" : "https://clinicaltrials.gov/study/NCT00105547"
    } ],
    "gaps" : [ {
      "id" : "gap-flurizan-cq-demo",
      "gap_class" : "exposure",
      "claim" : "Association score out of range (demo) — competency question cq-association-score blocks commit when gene–disease score exceeds 1.0.",
      "confidence" : 0.55,
      "status" : "needs_review",
      "risk_tier" : "L2",
      "insufficient_evidence" : true,
      "program_id" : "prog-flurizan-ad",
      "suggested_experiment" : "Educational demo only: OntoHarness v0.6 competency SPARQL gate.",
      "provenance_hash" : "dfc5fb9a961ee1b0",
      "critic_notes" : null,
      "literature_refs" : [ ],
      "discern" : null,
      "ontology_validation" : null
    }, {
      "id" : "gap-flurizan-efficacy",
      "gap_class" : "efficacy",
      "claim" : "Central target engagement or Aβ42 modulation may have been inadequate at clinically tolerated exposures to produce a measurable clinical benefit.",
      "confidence" : 0.55,
      "status" : "needs_review",
      "risk_tier" : "L2",
      "insufficient_evidence" : false,
      "program_id" : "prog-flurizan-ad",
      "suggested_experiment" : "Assemble public exposure–response and CSF biomarker reports for γ-secretase modulators; define a minimum PD effect size linked to clinical change before any similar MoA is reconsidered.",
      "provenance_hash" : "ab8633b5e5d40660",
      "critic_notes" : null,
      "literature_refs" : [ {
        "title" : "ClinicalTrials.gov tarenflurbil records",
        "url" : "https://clinicaltrials.gov/search?term=tarenflurbil",
        "note" : "Registry context for completed efficacy studies"
      } ],
      "discern" : null,
      "ontology_validation" : null
    }, {
      "id" : "gap-flurizan-biomarker",
      "gap_class" : "biomarker",
      "claim" : "Enrichment based on clinical mildness (e.g. MMSE bands) rather than mechanistic pathology markers may have diluted a true biological responder subgroup.",
      "confidence" : 0.58,
      "status" : "needs_review",
      "risk_tier" : "L2",
      "insufficient_evidence" : false,
      "program_id" : "prog-flurizan-ad",
      "suggested_experiment" : "Map published amyloid/tau biomarker distributions in contemporary mild AD cohorts against historical Flurizan inclusion criteria; quantify dilution risk for Aβ-pathway agents.",
      "provenance_hash" : "a042853e9fccd6e2",
      "critic_notes" : null,
      "literature_refs" : [ {
        "title" : "Translational lessons from Flurizan failure in AD",
        "url" : "https://pmc.ncbi.nlm.nih.gov/articles/PMC5350742/",
        "note" : "Post-hoc mild subgroup thinking and biomarker stratification caveats"
      } ],
      "discern" : null,
      "ontology_validation" : null
    }, {
      "id" : "gap-flurizan-endpoint",
      "gap_class" : "endpoint",
      "claim" : "Clinical endpoints (ADAS-Cog / ADCS-ADL) may have been insufficiently sensitive to detect a modest disease-modifying effect in the enrolled mild AD population over the studied duration.",
      "confidence" : 0.62,
      "status" : "needs_review",
      "risk_tier" : "L2",
      "insufficient_evidence" : false,
      "program_id" : "prog-flurizan-ad",
      "suggested_experiment" : "Re-analyse public AD trial datasets for endpoint sensitivity and power under modest effect sizes; pre-specify mechanistic PD biomarkers as co-primary or key secondary in future designs.",
      "provenance_hash" : "69f1a1f54e5b3212",
      "critic_notes" : null,
      "literature_refs" : [ {
        "title" : "Translational lessons from Flurizan failure in AD",
        "url" : "https://pmc.ncbi.nlm.nih.gov/articles/PMC5350742/",
        "note" : "Discusses Phase 3 miss and stratification/endpoint considerations"
      } ],
      "discern" : null,
      "ontology_validation" : null
    } ]
  },
  "cou" : "Generate literature-backed gap hypotheses for scientific discussion; not for clinical care or regulatory submission.",
  "risk_tier_note" : "Dossier is L1 summary; gap cards remain L2 and require HITL approval.",
  "verify_ui_path" : "/program/prog-flurizan-ad"
}
```

**Verify in UI:** http://localhost:8080/program/prog-flurizan-ad

**COU:** Generate literature-backed gap hypotheses for scientific discussion; not for clinical care or regulatory submission.


---

## run_gap_ontology_validate

```json
{
  "gapId": "gap-flurizan-efficacy",
  "format": "markdown"
}
```

## Gap OntoHarness validation

```json
{
  "domain" : "biomedical",
  "conforms" : true,
  "vocab_violations" : [ ],
  "shacl_violations" : [ ],
  "competency_violations" : [ ],
  "repair_hints" : [ ],
  "turtle_preview" : "@prefix bio: <https://ontoharness.dev/biomedical#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\nbio:gap-flurizan-efficacy a bio:Hypothesis ;\n    rdfs:label \"Central target engagement or Aβ42 modulation may have been inadequate at clinically tolerated exposures to produce a measurable clinical benefit.\" ;\n    bio:confidence \"0.55\"^^<http://www.w3.org/2001/XMLSchema#decimal> ;\n    bio:gapClass \"efficacy\" ;\n    bio:provenanceHash \"ab8633b5e5d40660\" .\n\nbio:MONDO_0004975 a bio:Disease ;\n    bio:hasIdentifier \"MONDO_0004975\" ;\n    rdfs:label \"Alzheimer disease\" .\n"
}
```

**Note:** Result is stored on the gap. If conforms=false, do not approve.

**COU:** Generate literature-backed gap hypotheses for scientific discussion; not for clinical care or regulatory submission.


---

## list_ontoharness_domains

```json
{
  "format": "json"
}
```

{"domains":[{"name":"biomedical","label":"Biomedical reference","description":"Gene-disease associations and translational hypotheses aligned with BioInsight Graph and GapForge. Demo / research use only — not clinical-grade.","policed_namespaces":["https://ontoharness.dev/biomedical#"],"competency_question_count":4}]}

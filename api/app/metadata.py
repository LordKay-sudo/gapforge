"""Static dataset and service metadata served by GET /api/v1/meta."""

from datetime import date

SERVICE_NAME = "bioinsight-graph"
API_VERSION = "0.3.1"
DATA_VERSION = "opentargets-24.06-frozen-slice-v2+gapforge-flurizan+astegolimab"

RELEASE_DATE = date(2024, 6, 1)

SOURCES = [
    {
        "name": "Open Targets Platform 24.06",
        "url": "https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/24.06/output/etl/json/",
        "license": "CC0 1.0 (see https://platform-docs.opentargets.org/licence)",
    },
    {
        "name": "Open Targets frozen slice v2 (CI/demo)",
        "url": "https://github.com/LordKay-sudo/gapforge/tree/main/api/tests/fixtures",
        "license": "CC0 1.0 (schema-aligned with Open Targets evidence model)",
    },
    {
        "name": "GapForge Flurizan educational case study",
        "url": "https://github.com/LordKay-sudo/gapforge/blob/main/data/gapforge/flurizan_case.json",
        "license": "MIT code; case framing cites public PMC / ClinicalTrials.gov (educational use)",
    },
    {
        "name": "GapForge Astegolimab COPD educational case study",
        "url": "https://github.com/LordKay-sudo/gapforge/blob/main/data/gapforge/astegolimab_case.json",
        "license": "MIT code; case framing cites public ClinicalTrials.gov / trial-design discussion (educational use)",
    },
]

DISCLAIMER = (
    "Disease–target associations from Open Targets–style public data for exploration and integration testing. "
    "Associations are correlative scores with typed evidence metadata, not evidence of causation, diagnosis, or treatment. "
    "GapForge hypotheses are L2 proposals requiring human review — not clinical or regulatory advice."
)

ASSOCIATIONS_ARE_CORRELATIVE = True
PROVENANCE_DOC_PATH = "PROVENANCE.md"


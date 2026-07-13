export default function About() {
  return (
    <>
      <h2 className="page-title">About BioInsight Graph</h2>
      <p className="page-subtitle">
        A research-oriented prototype for exploring disease–target associations as a knowledge graph.
      </p>

      <section className="about-section">
        <h2>Data source</h2>
        <p>
          MVP uses a representative sample inspired by{" "}
          <a href="https://www.opentargets.org/" target="_blank" rel="noreferrer">
            Open Targets
          </a>{" "}
          disease–target associations (~100+ genes, ~100+ edges). Full-scale production
          ingestion would pull from Open Targets Platform APIs or bulk exports.
        </p>
      </section>

      <section className="about-section">
        <h2>Graph schema</h2>
        <ul>
          <li>
            <strong>Nodes:</strong> Gene, Disease, Protein; GapForge adds Drug, Program, Trial,
            GapHypothesis, Review
          </li>
          <li>
            <strong>Edges:</strong> ASSOCIATED_WITH (Gene→Disease, with score), ENCODED_BY
            (Protein→Gene); GapForge PROV-style SUPPORTED_BY / CONTRADICTED_BY / DERIVED_FROM
          </li>
        </ul>
      </section>

      <section className="about-section">
        <h2>GapForge</h2>
        <p>
          Translational gap hunter for stalled programs (educational case: Flurizan / Alzheimer).
          Agents propose L2 hypotheses; humans approve or reject in the{" "}
          <a href="/gaps/review">review queue</a>. See{" "}
          <a
            href="https://github.com/LordKay-sudo/bioinsight-graph/blob/main/docs/GAPFORGE.md"
            target="_blank"
            rel="noreferrer"
          >
            GAPFORGE.md
          </a>
          . Not for clinical care, dosing, or molecule design.
        </p>
      </section>

      <section className="about-section">
        <h2>Limitations (MVP)</h2>
        <ul>
          <li>Sample data only — not clinical-grade</li>
          <li>No authentication or write APIs beyond GapForge review decisions</li>
          <li>Gap hypotheses are proposals until human-approved</li>
          <li>Disease search lists matches; gene detail is the primary drill-down view</li>
        </ul>
      </section>

      <section className="about-section">
        <h2>Stack</h2>
        <p>
          Neo4j · FastAPI · React + TypeScript + Vite. See the{" "}
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            OpenAPI docs
          </a>{" "}
          for API reference.
        </p>
      </section>
    </>
  );
}

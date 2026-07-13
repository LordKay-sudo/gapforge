import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  api,
  type GapHypothesisSummary,
  type ProgramDetail,
  type ProgramTaxonomy,
} from "../api/client";

export default function ProgramDetailPage() {
  const { programId } = useParams();
  const [program, setProgram] = useState<ProgramDetail | null>(null);
  const [taxonomy, setTaxonomy] = useState<ProgramTaxonomy | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!programId) return;
    Promise.all([api.getProgram(programId), api.getProgramTaxonomy(programId)])
      .then(([p, t]) => {
        setProgram(p);
        setTaxonomy(t);
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [programId]);

  if (error) return <p className="error-text">{error}</p>;
  if (!program) return <p className="muted">Loading dossier…</p>;

  return (
    <div>
      <p className="breadcrumb">
        <Link to="/programs">Programs</Link> / {program.name}
      </p>
      <h1 className="page-title">{program.name}</h1>
      <p className="page-subtitle">
        {program.drug?.name}
        {program.drug?.synonyms?.length ? ` (${program.drug.synonyms.join(", ")})` : ""}
        {program.status ? ` · ${program.status}` : ""}
      </p>

      <div className="banner-cou">{program.cou_note}</div>

      <section className="panel">
        <h2>Stall summary</h2>
        <p>{program.stall_summary}</p>
        <p>
          <strong>MoA:</strong> {program.moa}
        </p>
        {program.disease && (
          <p>
            <strong>Indication:</strong>{" "}
            <Link to={`/disease/${program.disease.id}`}>{program.disease.name}</Link> (
            <code>{program.disease.id}</code>)
          </p>
        )}
        {program.genes?.length > 0 && (
          <p>
            <strong>Linked genes:</strong>{" "}
            {program.genes.map((g, i) => (
              <span key={g.id || i}>
                {i > 0 ? ", " : ""}
                {g.id ? <Link to={`/gene/${g.id}`}>{g.symbol || g.id}</Link> : g.symbol}
              </span>
            ))}
          </p>
        )}
        <p>
          <a href={api.reviewBundleUrl(program.id)} target="_blank" rel="noreferrer">
            Export review bundle (JSON)
          </a>
          {" · "}
          <Link to="/gaps/review">Open review queue</Link>
        </p>
      </section>

      <section className="panel">
        <h2>Trials</h2>
        {program.trials.map((t) => (
          <div key={t.id} className="trial-block">
            <h3>
              {t.nct_id || t.id}{" "}
              <span className="badge">{t.phase}</span>
            </h3>
            <p className="muted">{t.status}</p>
            <p>
              <strong>Primary endpoint:</strong> {t.primary_endpoint}
            </p>
            <p>{t.outcome_summary}</p>
            {t.url && (
              <a href={t.url} target="_blank" rel="noreferrer">
                ClinicalTrials.gov
              </a>
            )}
          </div>
        ))}
      </section>

      {taxonomy && (
        <section className="panel">
          <h2>Gap taxonomy (evidence density)</h2>
          <p className="muted">{taxonomy.note}</p>
          <div className="taxonomy-grid">
            {taxonomy.dimensions.map((d) => (
              <div key={d.code} className="taxonomy-item">
                <div className="taxonomy-label">{d.label}</div>
                <div className="taxonomy-bar">
                  <div
                    className="taxonomy-fill"
                    style={{ width: `${Math.round(d.evidence_density * 100)}%` }}
                  />
                </div>
                <code>{d.code}</code> · {d.evidence_density.toFixed(2)}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="panel">
        <h2>Gap hypotheses (L2)</h2>
        <p className="muted">Status starts as needs_review until a human approves or rejects.</p>
        <div className="card-list">
          {program.gaps.map((g) => (
            <GapCard key={g.id} gap={g} />
          ))}
        </div>
      </section>
    </div>
  );
}

function GapCard({ gap }: { gap: GapHypothesisSummary }) {
  return (
    <article className="gap-card">
      <div className="program-card-header">
        <h3>
          <span className="badge badge-class">{gap.gap_class}</span> {gap.id}
        </h3>
        <span className={`badge status-${gap.status}`}>{gap.status}</span>
      </div>
      <p>{gap.claim}</p>
      <p className="muted">
        confidence {gap.confidence.toFixed(2)} · {gap.risk_tier}
        {gap.insufficient_evidence ? " · insufficient_evidence" : ""}
        {gap.provenance_hash ? ` · hash ${gap.provenance_hash}` : ""}
      </p>
      {gap.suggested_experiment && (
        <p>
          <strong>Next experiment:</strong> {gap.suggested_experiment}
        </p>
      )}
      {gap.critic_notes && (
        <p className="critic-notes">
          <strong>Critic:</strong> {gap.critic_notes}
        </p>
      )}
      {gap.literature_refs?.length > 0 && (
        <ul className="ref-list">
          {gap.literature_refs.map((r, i) => (
            <li key={i}>
              {r.url ? (
                <a href={r.url} target="_blank" rel="noreferrer">
                  {r.title || r.url}
                </a>
              ) : (
                r.title
              )}
              {r.note ? ` — ${r.note}` : ""}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

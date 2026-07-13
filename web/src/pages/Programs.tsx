import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type ProgramSummary } from "../api/client";

export default function Programs() {
  const [programs, setPrograms] = useState<ProgramSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listPrograms()
      .then(setPrograms)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="page-title">GapForge programs</h1>
      <p className="page-subtitle">
        Stalled / discontinued programs for educational gap hunting. Agents propose; humans
        dispose. Not clinical advice.
      </p>

      <div className="banner-cou">
        <strong>COU:</strong> literature-backed gap hypotheses for scientific discussion — not for
        clinical care or regulatory submission. L2 cards require HITL approval.
      </div>

      {loading && <p className="muted">Loading programs…</p>}
      {error && <p className="error-text">{error}</p>}

      <div className="card-list">
        {programs.map((p) => (
          <Link key={p.id} to={`/program/${p.id}`} className="program-card">
            <div className="program-card-header">
              <h2>{p.name}</h2>
              <span className="badge">{p.status || "unknown"}</span>
            </div>
            <p className="muted">{p.drug_name}</p>
            <p>{p.stall_summary}</p>
            <div className="meta-row">
              <span>{p.indication_name}</span>
              <span>
                {p.trial_count} trials · {p.gap_count} gaps
              </span>
            </div>
          </Link>
        ))}
        {!loading && programs.length === 0 && !error && (
          <p className="muted">
            No programs seeded. Run <code>scripts/seed_gapforge.py</code> after Neo4j seed.
          </p>
        )}
      </div>
    </div>
  );
}

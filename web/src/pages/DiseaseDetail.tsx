import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  api,
  type DiseaseDetail as DiseaseDetailType,
  type ScoredGeneTarget,
} from "../api/client";

export default function DiseaseDetail() {
  const { diseaseId } = useParams<{ diseaseId: string }>();
  const [disease, setDisease] = useState<DiseaseDetailType | null>(null);
  const [genes, setGenes] = useState<ScoredGeneTarget[]>([]);
  const [minScore, setMinScore] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!diseaseId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([api.getDisease(diseaseId), api.getDiseaseGenes(diseaseId, minScore)])
      .then(([d, g]) => {
        if (cancelled) return;
        setDisease(d);
        setGenes(g.genes);
      })
      .catch(() => {
        if (cancelled) return;
        setError("Disease not found — start Neo4j and seed data for live results.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [diseaseId, minScore]);

  if (loading) {
    return <div className="state-box">Loading disease details…</div>;
  }

  if (error || !disease) {
    return (
      <>
        <Link to="/" className="back-link">
          ← Back to search
        </Link>
        <div className="state-box error">{error ?? "Disease not found"}</div>
      </>
    );
  }

  return (
    <>
      <Link to="/" className="back-link">
        ← Back to search
      </Link>

      <div className="detail-header">
        <span className="badge badge-disease">Disease</span>
        <h2 className="page-title" style={{ marginTop: "0.5rem" }}>
          {disease.name}
        </h2>
        <p className="mono" style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
          {disease.id}
        </p>

        <div className="detail-meta">
          <div className="meta-chip">
            <strong>{disease.gene_count}</strong>
            Associated genes
          </div>
          <div className="meta-chip">
            <strong>{genes.length}</strong>
            Shown targets
          </div>
        </div>
      </div>

      <div className="filter-row">
        <label htmlFor="minScore">Min score: {minScore.toFixed(2)}</label>
        <input
          id="minScore"
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={minScore}
          onChange={(e) => setMinScore(Number(e.target.value))}
        />
      </div>

      <h3 style={{ marginBottom: "1rem" }}>Top gene targets</h3>
      {genes.length === 0 ? (
        <div className="state-box">No gene targets above this score threshold.</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Symbol</th>
                <th>Score</th>
                <th>Evidence types</th>
                <th>Gene ID</th>
              </tr>
            </thead>
            <tbody>
              {genes.map((g, i) => (
                <tr key={g.gene_id}>
                  <td>{i + 1}</td>
                  <td>
                    <Link to={`/gene/${encodeURIComponent(g.gene_id)}`}>{g.symbol}</Link>
                  </td>
                  <td>{g.score.toFixed(3)}</td>
                  <td>
                    {g.evidence.length > 0
                      ? [...new Set(g.evidence.map((e) => e.evidence_type))]
                          .map((t) => t.replace(/_/g, " "))
                          .join(", ")
                      : "—"}
                  </td>
                  <td className="mono">{g.gene_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

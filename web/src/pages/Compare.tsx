import { useState } from "react";
import { Link } from "react-router-dom";
import { api, type CompareGenesResponse } from "../api/client";

export default function Compare() {
  const [input, setInput] = useState("BRCA1, TP53");
  const [result, setResult] = useState<CompareGenesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runCompare = (e: React.FormEvent) => {
    e.preventDefault();
    const symbols = input
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (symbols.length < 2) {
      setError("Enter at least two symbols, comma-separated.");
      return;
    }
    setLoading(true);
    setError(null);
    api
      .compareGenes(symbols)
      .then((r) => setResult(r))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <>
      <h2 className="page-title">Compare gene targets</h2>
      <p className="page-subtitle">
        Side-by-side top disease associations and shared targets (2–5 genes).
      </p>

      <form className="compare-form" onSubmit={runCompare}>
        <input
          className="search-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="BRCA1, TP53, EGFR"
        />
        <button type="submit" className="tab active" disabled={loading}>
          {loading ? "Comparing…" : "Compare"}
        </button>
      </form>

      {error && <div className="state-box error">{error}</div>}

      {result && (
        <>
          {result.overlapping_disease_names.length > 0 && (
            <div className="overlap-box">
              <strong>Shared top diseases:</strong>{" "}
              {result.overlapping_disease_names.join(", ")}
            </div>
          )}

          <div className="compare-grid">
            {result.genes.map((g) => (
              <div key={g.gene_id} className="compare-card">
                <h3>
                  <Link to={`/gene/${encodeURIComponent(g.gene_id)}`}>{g.symbol}</Link>
                </h3>
                <p className="page-subtitle" style={{ marginTop: 0 }}>
                  {g.disease_count} linked diseases
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Disease</th>
                      <th>Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {g.top_diseases.map((d) => {
                      const shared = result.overlapping_disease_names.includes(d.name);
                      return (
                        <tr key={d.disease_id} className={shared ? "shared-row" : undefined}>
                          <td>{d.name}</td>
                          <td>{d.score.toFixed(3)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  );
}

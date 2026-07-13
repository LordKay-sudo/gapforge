import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type DiseaseSummary, type GeneSummary, type StatsResponse } from "../api/client";
import { DEMO_STATS, filterDemoGenes } from "../demo/data";
import { useDebounce } from "../hooks/useDebounce";

type Tab = "genes" | "diseases";

export default function Search() {
  const [tab, setTab] = useState<Tab>("genes");
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);

  const [genes, setGenes] = useState<GeneSummary[]>([]);
  const [diseases, setDiseases] = useState<DiseaseSummary[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    api
      .getStats()
      .then(setStats)
      .catch(() => {
        setStats(DEMO_STATS);
        setDemoMode(true);
      });
  }, []);

  useEffect(() => {
    if (debouncedQuery.length < 1) {
      setGenes([]);
      setDiseases([]);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    if (demoMode && tab === "genes") {
      setGenes(filterDemoGenes(debouncedQuery));
      setDiseases([]);
      setLoading(false);
      return;
    }

    const search =
      tab === "genes"
        ? api.searchGenes(debouncedQuery).then(setGenes)
        : api.searchDiseases(debouncedQuery).then(setDiseases);

    search
      .catch((e: Error) => {
        if (tab === "genes") {
          setGenes(filterDemoGenes(debouncedQuery));
          setDemoMode(true);
          setError(null);
        } else {
          setError(e.message);
        }
      })
      .finally(() => setLoading(false));
  }, [debouncedQuery, tab, demoMode]);

  const results = tab === "genes" ? genes : diseases;
  const showEmpty = debouncedQuery.length >= 1 && !loading && !error && results.length === 0;

  return (
    <>
      <h2 className="page-title">Search the knowledge graph</h2>
      <p className="page-subtitle">
        Explore genes and diseases from the Open Targets-style association dataset.
      </p>

      {stats && (
        <div className="stats-row">
          <div className="stat-card">
            <strong>{stats.genes}</strong>
            <span>Genes</span>
          </div>
          <div className="stat-card">
            <strong>{stats.diseases}</strong>
            <span>Diseases</span>
          </div>
          <div className="stat-card">
            <strong>{stats.proteins}</strong>
            <span>Proteins</span>
          </div>
          <div className="stat-card">
            <strong>{stats.associations}</strong>
            <span>Associations</span>
          </div>
        </div>
      )}

      <div className="search-panel">
        <div className="tabs">
          <button
            type="button"
            className={`tab ${tab === "genes" ? "active" : ""}`}
            onClick={() => setTab("genes")}
          >
            Genes
          </button>
          <button
            type="button"
            className={`tab ${tab === "diseases" ? "active" : ""}`}
            onClick={() => setTab("diseases")}
          >
            Diseases
          </button>
        </div>

        <div className="search-input-wrap">
          <input
            className="search-input"
            type="search"
            placeholder={
              tab === "genes"
                ? "Search by symbol or name (e.g. BRCA1)"
                : "Search diseases (e.g. breast cancer)"
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        </div>

        {loading && <div className="state-box">Searching...</div>}
        {error && <div className="state-box error">API error: {error}</div>}
        {showEmpty && (
          <div className="state-box">No results for &ldquo;{debouncedQuery}&rdquo;</div>
        )}

        {!loading && !error && results.length > 0 && (
          <ul className="results-list">
            {tab === "genes"
              ? genes.map((g) => (
                  <li key={g.id} className="result-item">
                    <Link to={`/gene/${encodeURIComponent(g.id)}`} className="result-link">
                      <span className="badge badge-gene">Gene</span>{" "}
                      <span className="result-symbol">{g.symbol}</span>
                      {g.name && <div className="result-name">{g.name}</div>}
                      <div className="result-name mono">{g.id}</div>
                    </Link>
                  </li>
                ))
              : diseases.map((d) => (
                  <li key={d.id} className="result-item">
                    <Link to={`/disease/${encodeURIComponent(d.id)}`} className="result-link">
                      <span className="badge badge-disease">Disease</span>{" "}
                      <span className="result-symbol">{d.name}</span>
                      <div className="result-name mono">{d.id}</div>
                    </Link>
                  </li>
                ))}
          </ul>
        )}

        {debouncedQuery.length < 1 && (
          <div className="state-box">Type to search genes or diseases</div>
        )}
      </div>
    </>
  );
}

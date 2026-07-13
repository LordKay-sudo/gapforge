import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

import { api, type MetaResponse } from "../api/client";

export default function Layout({ children }: { children: React.ReactNode }) {
  const [meta, setMeta] = useState<MetaResponse | null>(null);

  useEffect(() => {
    api.getMeta().then(setMeta).catch(() => setMeta(null));
  }, []);
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-inner">
          <NavLink to="/" className="brand">
            <div className="brand-icon">BI</div>
            <div>
              <h1>BioInsight Graph</h1>
              <p>Disease–target knowledge explorer</p>
            </div>
          </NavLink>
          <nav className="nav-links">
            <NavLink to="/" end>
              Search
            </NavLink>
            <NavLink to="/compare">Compare</NavLink>
            <NavLink to="/programs">GapForge</NavLink>
            <NavLink to="/gaps/review">Review</NavLink>
            <NavLink to="/about">About</NavLink>
          </nav>
        </div>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        <p>
          {meta ? (
            <>
              Data: <code>{meta.data_version}</code> ({meta.release_date}) · associations are
              correlative, not causal ·{" "}
            </>
          ) : (
            <>Data: Open Targets–style sample · </>
          )}
          <a
            href="https://github.com/LordKay-sudo/bioinsight-graph/blob/main/PROVENANCE.md"
            target="_blank"
            rel="noreferrer"
          >
            Provenance
          </a>
          {" · "}
          API:{" "}
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            OpenAPI
          </a>
        </p>
      </footer>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import EvidenceChart from "../components/EvidenceChart";
import ForceGraphView from "../components/ForceGraphView";
import {
  api,
  type EvidenceItem,
  type GeneDetail as GeneDetailType,
  type GeneExternalLinksResponse,
  type NeighborEdge,
  type NeighborNode,
  type SubgraphLink,
  type SubgraphNode,
} from "../api/client";
import { DEMO_GENE_DETAIL, DEMO_NEIGHBORS, DEMO_SUBGRAPH } from "../demo/data";

type ViewMode = "table" | "graph";

function nodeLabel(n: NeighborNode): string {
  if (n.label === "Gene") return n.symbol ?? n.id;
  return n.name ?? n.id;
}

function neighborRows(
  geneId: string,
  nodes: NeighborNode[],
  edges: NeighborEdge[]
): { type: string; name: string; id: string; relation: string; score: string }[] {
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const rows: { type: string; name: string; id: string; relation: string; score: string }[] = [];

  for (const e of edges) {
    const otherId = e.source === geneId ? e.target : e.source;
    const node = nodeMap.get(otherId);
    if (!node || node.id === geneId) continue;
    rows.push({
      type: node.label,
      name: nodeLabel(node),
      id: node.id,
      relation: e.type.replace(/_/g, " "),
      score: e.score != null ? e.score.toFixed(2) : "—",
    });
  }

  return rows.sort((a, b) => a.type.localeCompare(b.type));
}

export default function GeneDetail() {
  const { geneId } = useParams<{ geneId: string }>();
  const [view, setView] = useState<ViewMode>("graph");
  const [gene, setGene] = useState<GeneDetailType | null>(null);
  const [neighbors, setNeighbors] = useState<{ nodes: NeighborNode[]; edges: NeighborEdge[] } | null>(
    null
  );
  const [subgraph, setSubgraph] = useState<{ nodes: SubgraphNode[]; links: SubgraphLink[] } | null>(
    null
  );
  const [evidenceItems, setEvidenceItems] = useState<EvidenceItem[]>([]);
  const [externalLinks, setExternalLinks] = useState<GeneExternalLinksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!geneId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    const applyDemo = () => {
      if (geneId !== DEMO_GENE_DETAIL.id) return false;
      setGene(DEMO_GENE_DETAIL);
      setNeighbors({ nodes: DEMO_NEIGHBORS.nodes, edges: DEMO_NEIGHBORS.edges });
      setSubgraph({ nodes: DEMO_SUBGRAPH.nodes, links: DEMO_SUBGRAPH.links });
      return true;
    };

    const fallbackTimer = window.setTimeout(() => {
      if (!cancelled && applyDemo()) setLoading(false);
    }, 1200);

    Promise.all([
      api.getGene(geneId),
      api.getNeighbors(geneId),
      api.getSubgraph(geneId),
      api.getGeneEvidence(geneId).catch(() => null),
      api.getGeneExternalLinks(geneId).catch(() => null),
    ])
      .then(([g, n, sg, ev, links]) => {
        if (cancelled) return;
        setGene(g);
        setNeighbors({ nodes: n.nodes, edges: n.edges });
        setSubgraph({ nodes: sg.nodes, links: sg.links });
        if (ev) {
          const flat = ev.evidence.flatMap((b) => b.evidence);
          setEvidenceItems(flat);
        }
        if (links) setExternalLinks(links);
      })
      .catch(() => {
        if (cancelled) return;
        if (!applyDemo()) {
          setError("Gene not found — start Neo4j and seed data for live results.");
        }
      })
      .finally(() => {
        window.clearTimeout(fallbackTimer);
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      window.clearTimeout(fallbackTimer);
    };
  }, [geneId]);

  if (loading) {
    return <div className="state-box">Loading gene details…</div>;
  }

  if (error || !gene) {
    return (
      <>
        <Link to="/" className="back-link">
          ← Back to search
        </Link>
        <div className="state-box error">{error ?? "Gene not found"}</div>
      </>
    );
  }

  const rows = neighbors ? neighborRows(gene.id, neighbors.nodes, neighbors.edges) : [];

  return (
    <>
      <Link to="/" className="back-link">
        ← Back to search
      </Link>

      <div className="detail-header">
        <span className="badge badge-gene">Gene</span>
        <h2 className="page-title" style={{ marginTop: "0.5rem" }}>
          {gene.symbol}
        </h2>
        {gene.name && <p className="page-subtitle" style={{ marginBottom: 0 }}>{gene.name}</p>}
        <p className="mono" style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
          {gene.id}
        </p>

        <div className="external-links">
          {externalLinks?.links.map((link) => (
            <a
              key={link.provider + link.url}
              href={link.url}
              target="_blank"
              rel="noreferrer"
              className="external-link-chip"
            >
              Open in {link.label}
            </a>
          ))}
          <a
            href={api.geneReportUrl(gene.id, "tsv")}
            className="external-link-chip"
            download
          >
            Download report (TSV)
          </a>
        </div>

        <div className="detail-meta">
          <div className="meta-chip">
            <strong>{gene.disease_count}</strong>
            Linked diseases
          </div>
          <div className="meta-chip">
            <strong>{gene.protein_count}</strong>
            Encoded proteins
          </div>
          <div className="meta-chip">
            <strong>{rows.length}</strong>
            Neighbor edges
          </div>
        </div>
      </div>

      <EvidenceChart items={evidenceItems} />

      <div className="view-tabs">
        <button
          type="button"
          className={`tab ${view === "graph" ? "active" : ""}`}
          onClick={() => setView("graph")}
        >
          Graph view
        </button>
        <button
          type="button"
          className={`tab ${view === "table" ? "active" : ""}`}
          onClick={() => setView("table")}
        >
          Neighbor table
        </button>
      </div>

      {view === "graph" && subgraph && (
        <section className="graph-section">
          <ForceGraphView centerGeneId={gene.id} nodes={subgraph.nodes} links={subgraph.links} />
          <div className="graph-legend">
            <span className="legend-item">
              <span className="legend-dot" style={{ background: "#34d399" }} /> Gene
            </span>
            <span className="legend-item">
              <span className="legend-dot" style={{ background: "#f472b6" }} /> Disease
            </span>
            <span className="legend-item">
              <span className="legend-dot" style={{ background: "#a78bfa" }} /> Protein
            </span>
          </div>
        </section>
      )}

      {view === "table" && (
        <>
          <h3 style={{ marginBottom: "1rem" }}>1-hop neighbors</h3>
          {rows.length === 0 ? (
            <div className="state-box">No neighbors found for this gene.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Name</th>
                    <th>ID</th>
                    <th>Relationship</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={`${r.id}-${r.relation}`}>
                      <td>
                        <span
                          className={`badge badge-${r.type.toLowerCase()}`}
                          style={
                            r.type === "Protein"
                              ? { background: "rgba(167,139,250,0.15)", color: "var(--protein)" }
                              : undefined
                          }
                        >
                          {r.type}
                        </span>
                      </td>
                      <td>{r.name}</td>
                      <td className="mono">{r.id}</td>
                      <td>{r.relation}</td>
                      <td>{r.score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </>
  );
}

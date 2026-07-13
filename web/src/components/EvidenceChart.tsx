import type { EvidenceItem } from "../api/client";

interface Props {
  items: EvidenceItem[];
  title?: string;
}

/** Aggregate evidence_type scores across top associations (task 3.1). */
export default function EvidenceChart({ items, title = "Evidence by type" }: Props) {
  const totals = new Map<string, number>();
  for (const item of items) {
    totals.set(item.evidence_type, (totals.get(item.evidence_type) ?? 0) + item.score);
  }
  const rows = [...totals.entries()].sort((a, b) => b[1] - a[1]);
  const max = rows.length ? rows[0][1] : 1;

  if (rows.length === 0) {
    return (
      <div className="state-box" style={{ marginTop: "1rem" }}>
        No typed evidence in the graph for this gene yet.
      </div>
    );
  }

  return (
    <section className="evidence-section">
      <h3>{title}</h3>
      <p className="page-subtitle" style={{ marginTop: 0 }}>
        Summed scores from decomposed association evidence (demo Open Targets–style).
      </p>
      <ul className="evidence-chart">
        {rows.map(([type, sum]) => (
          <li key={type} className="evidence-row">
            <span className="evidence-label">{type.replace(/_/g, " ")}</span>
            <div className="evidence-bar-track">
              <div
                className="evidence-bar-fill"
                style={{ width: `${Math.min(100, (sum / max) * 100)}%` }}
              />
            </div>
            <span className="evidence-value">{sum.toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

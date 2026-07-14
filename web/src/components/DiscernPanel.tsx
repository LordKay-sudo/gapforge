import type { DiscernResult } from "../api/client";

function actionClass(action: string): string {
  if (action === "block") return "discern-action-block";
  if (action === "require_hitl") return "discern-action-hitl";
  return "discern-action-allow";
}

export default function DiscernPanel({
  discern,
  onRun,
  busy,
}: {
  discern?: DiscernResult | null;
  onRun?: () => void;
  busy?: boolean;
}) {
  if (!discern && !onRun) return null;

  return (
    <div className="discern-panel">
      <div className="discern-panel-header">
        <strong>Discern</strong>
        {onRun && (
          <button
            type="button"
            className="btn btn-secondary"
            disabled={busy}
            onClick={onRun}
          >
            Run discern
          </button>
        )}
      </div>
      {!discern && <p className="muted">Not scored yet — run critic or discern.</p>}
      {discern && (
        <>
          <p className="discern-summary">
            <span className={`badge ${actionClass(discern.action)}`}>{discern.action}</span>{" "}
            <span className="muted">
              overall {discern.overall}
              {discern.policy_version ? ` · ${discern.policy_version}` : ""}
            </span>
          </p>
          {discern.scores && (
            <ul className="discern-scores">
              {Object.entries(discern.scores).map(([dim, s]) => (
                <li key={dim}>
                  <code>{dim}</code> {s.score.toFixed(2)}
                  <span className="muted">
                    {" "}
                    / {s.threshold.toFixed(2)} {s.passed ? "✓" : "✗"}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {discern.reasons && discern.reasons.length > 0 && (
            <ul className="discern-reasons">
              {discern.reasons.slice(0, 4).map((r, i) => (
                <li key={i}>
                  <span className={`discern-sev-${r.severity}`}>{r.severity}</span> {r.message}
                </li>
              ))}
            </ul>
          )}
          {discern.note && <p className="muted discern-note">{discern.note}</p>}
        </>
      )}
    </div>
  );
}

export function discernBlocksApprove(discern?: DiscernResult | null): boolean {
  return discern?.action === "block";
}

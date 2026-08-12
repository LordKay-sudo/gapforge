import type { OntologyValidationResult } from "../api/client";

export default function OntologyValidationPanel({
  validation,
  onRun,
  busy,
}: {
  validation?: OntologyValidationResult | null;
  onRun?: () => void;
  busy?: boolean;
}) {
  if (!validation && !onRun) return null;

  const skipped = Boolean(validation?.skipped);
  const conforms = Boolean(validation?.conforms);
  const badgeClass = skipped
    ? "ontology-action-skipped"
    : conforms
      ? "ontology-action-pass"
      : "ontology-action-fail";

  return (
    <div className="ontology-panel discern-panel">
      <div className="discern-panel-header">
        <strong>OntoHarness</strong>
        {onRun && (
          <button
            type="button"
            className="btn btn-secondary"
            disabled={busy}
            onClick={onRun}
          >
            Re-validate
          </button>
        )}
      </div>
      {!validation && (
        <p className="muted">Not validated yet — run ontology check before approve.</p>
      )}
      {validation && (
        <>
          <p className="discern-summary">
            <span className={`badge ${badgeClass}`}>
              {skipped ? "skipped" : conforms ? "conforms" : "failed"}
            </span>{" "}
            <span className="muted">
              domain {validation.domain ?? "biomedical"}
              {validation.reason ? ` · ${validation.reason}` : ""}
            </span>
          </p>
          {validation.vocab_violations && validation.vocab_violations.length > 0 && (
            <>
              <p className="muted">Vocabulary gate</p>
              <ul className="discern-reasons">
                {validation.vocab_violations.slice(0, 4).map((v, i) => (
                  <li key={i}>
                    <code>{v.term_kind}</code> {v.term} — {v.message}
                  </li>
                ))}
              </ul>
            </>
          )}
          {validation.shacl_violations && validation.shacl_violations.length > 0 && (
            <>
              <p className="muted">SHACL</p>
              <ul className="discern-reasons">
                {validation.shacl_violations.slice(0, 4).map((v, i) => (
                  <li key={i}>{v.message}</li>
                ))}
              </ul>
            </>
          )}
          {validation.competency_violations &&
            validation.competency_violations.length > 0 && (
              <>
                <p className="muted">Competency questions</p>
                <ul className="discern-reasons">
                  {validation.competency_violations.slice(0, 4).map((v, i) => (
                    <li key={i}>
                      <code>{v.cq_id}</code> — {v.message}
                      {v.question ? (
                        <span className="muted"> ({v.question})</span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </>
            )}
          {validation.repair_hints && validation.repair_hints.length > 0 && (
            <>
              <p className="muted">Repair hints</p>
              <ul className="discern-reasons">
                {validation.repair_hints.slice(0, 4).map((hint, i) => (
                  <li key={i}>{hint}</li>
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </div>
  );
}

export function ontologyBlocksApprove(
  validation?: OntologyValidationResult | null,
  enabled = true,
): boolean {
  if (!enabled || !validation || validation.skipped) {
    return false;
  }
  return !validation.conforms;
}

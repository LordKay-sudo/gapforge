import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type ReviewQueueItem } from "../api/client";

export default function GapReviewQueue() {
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [reviewer, setReviewer] = useState("demo-reviewer");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const reload = useCallback(() => {
    api
      .reviewQueue("needs_review")
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  async function act(gapId: string, decision: "approve" | "reject" | "request_more") {
    setBusy(gapId + decision);
    setError(null);
    setMessage(null);
    try {
      const res = await api.decideReview(gapId, decision, reviewer, notes);
      setMessage(res.message);
      setNotes("");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function critic(gapId: string) {
    setBusy(gapId + "critic");
    setError(null);
    try {
      const res = await api.runCritic(gapId);
      setMessage(`Critic: ${res.critic_notes} (confidence→${res.confidence_after.toFixed(2)})`);
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <h1 className="page-title">GapForge review queue</h1>
      <p className="page-subtitle">
        Human-in-the-loop for L2 hypotheses. Only approved cards become team conclusions.
      </p>

      <div className="banner-cou">
        Approve only after checking the program page and dual-channel evidence. This is not clinical
        decision support.
      </div>

      <div className="panel review-controls">
        <label>
          Reviewer{" "}
          <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} />
        </label>
        <label>
          Notes{" "}
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional review notes"
            style={{ minWidth: "16rem" }}
          />
        </label>
      </div>

      {message && <p className="success-text">{message}</p>}
      {error && <p className="error-text">{error}</p>}

      <div className="card-list">
        {items.map((item) => (
          <article key={item.hypothesis.id} className="gap-card">
            <div className="program-card-header">
              <h3>
                <span className="badge badge-class">{item.hypothesis.gap_class}</span>{" "}
                {item.hypothesis.id}
              </h3>
              <span className="badge status-needs_review">{item.hypothesis.status}</span>
            </div>
            <p className="muted">
              Program: <Link to={`/program/${item.program_id}`}>{item.program_name}</Link>
            </p>
            <p>{item.hypothesis.claim}</p>
            <p className="muted">
              confidence {item.hypothesis.confidence.toFixed(2)}
              {item.hypothesis.critic_notes ? ` · critic: ${item.hypothesis.critic_notes}` : ""}
            </p>
            <div className="action-row">
              <button
                type="button"
                className="btn btn-secondary"
                disabled={!!busy}
                onClick={() => critic(item.hypothesis.id)}
              >
                Run critic
              </button>
              <button
                type="button"
                className="btn btn-primary"
                disabled={!!busy}
                onClick={() => act(item.hypothesis.id, "approve")}
              >
                Approve
              </button>
              <button
                type="button"
                className="btn btn-danger"
                disabled={!!busy}
                onClick={() => act(item.hypothesis.id, "reject")}
              >
                Reject
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={!!busy}
                onClick={() => act(item.hypothesis.id, "request_more")}
              >
                Request more
              </button>
            </div>
          </article>
        ))}
        {items.length === 0 && <p className="muted">Queue empty — no cards in needs_review.</p>}
      </div>
    </div>
  );
}

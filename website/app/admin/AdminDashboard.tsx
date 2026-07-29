"use client";

import { useState, useEffect, useRef } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type DigestKey = "brief" | "markets" | "sports" | "paddock";

interface Digest {
  key: DigestKey;
  label: string;
  description: string;
  previewFile: string;
  hasIngest?: boolean;
}

const DIGESTS: Digest[] = [
  {
    key: "brief",
    label: "The Operating Brief",
    description: "AI & business news for Australian operators",
    previewFile: "preview_latest.html",
  },
  {
    key: "markets",
    label: "The Markets Brief",
    description: "ASX pre-market & overnight macro",
    previewFile: "preview_markets.html",
  },
  {
    key: "sports",
    label: "The Sporting Brief",
    description: "NRL, AFL, soccer, NBA, F1 & AI in sport",
    previewFile: "preview_sports.html",
    hasIngest: true,
  },
  {
    key: "paddock",
    label: "The Paddock Brief",
    description: "Australian agriculture, AgTech & policy",
    previewFile: "preview_paddock.html",
  },
];

type Stats = Record<DigestKey, number>;

type AdminDashboardProps = {
  previewToken: string;
  isVercel: boolean;
};

// ---------------------------------------------------------------------------
// Login screen
// ---------------------------------------------------------------------------
function LoginScreen({ onLogin }: { onLogin: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    const res = await fetch("/api/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    setLoading(false);
    if (res.ok) {
      onLogin();
    } else {
      setError("Incorrect password.");
    }
  }

  return (
    <div className="admin-page admin-page--login">
      <div className="admin-login">
        <p className="admin-kicker">
          Admin
        </p>
        <h1 className="admin-login__title">
          The Operating Brief
        </h1>
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
            className="admin-input"
          />
          {error && (
            <p className="admin-error">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="admin-button admin-button--primary"
          >
            {loading ? "Checking…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main dashboard
// ---------------------------------------------------------------------------
export default function AdminDashboard({ previewToken, isVercel }: AdminDashboardProps) {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [activeJob, setActiveJob] = useState<string | null>(null);
  const [logs, setLogs] = useState<Array<{ type: string; text: string }>>([]);
  const [previewReady, setPreviewReady] = useState<Record<DigestKey, boolean>>({
    brief: false, markets: false, sports: false, paddock: false,
  });
  const logsEndRef = useRef<HTMLDivElement>(null);
  const readerRef = useRef<ReadableStreamDefaultReader | null>(null);
  const previewPollRef = useRef<number | null>(null);
  const previewPollStartedAtRef = useRef<number | null>(null);
  const previewPollLastStateRef = useRef<string | null>(null);

  // Check if already authenticated by hitting the subscribers endpoint
  useEffect(() => {
    fetch("/api/admin/subscribers")
      .then((r) => {
        if (r.ok) return r.json().then((d: Stats) => { setAuthed(true); setStats(d); });
        else setAuthed(false);
      })
      .catch(() => setAuthed(false));
  }, []);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    return () => {
      if (previewPollRef.current) {
        window.clearTimeout(previewPollRef.current);
        previewPollRef.current = null;
      }
    };
  }, []);

  function appendLog(type: string, text: string) {
    setLogs((l) => [...l, { type, text }]);
  }

  function schedulePreviewPoll() {
    if (!isVercel || previewPollStartedAtRef.current === null) return;

    if (previewPollRef.current) {
      window.clearTimeout(previewPollRef.current);
    }

    previewPollRef.current = window.setTimeout(async () => {
      try {
        const since = new Date(previewPollStartedAtRef.current ?? Date.now()).toISOString();
        const res = await fetch(`/api/admin/workflow-status?action=brief-preview&since=${encodeURIComponent(since)}`);
        if (!res.ok) {
          appendLog("err", `Status check failed: HTTP ${res.status}`);
          setActiveJob(null);
          return;
        }

        const data = await res.json() as {
          state: "pending" | "queued" | "in_progress" | "completed" | "failed";
          message: string;
          run: null | {
            id: number;
            status: string;
            conclusion: string | null;
            updated_at: string;
            html_url: string;
            display_title: string;
          };
        };

        if (data.state !== previewPollLastStateRef.current) {
          previewPollLastStateRef.current = data.state;
          appendLog(data.state === "failed" ? "err" : data.state === "completed" ? "done" : "info", data.message);
        }

        if (data.state === "completed") {
          setPreviewReady((p) => ({ ...p, brief: true }));
          setActiveJob(null);
          previewPollStartedAtRef.current = null;
          previewPollLastStateRef.current = null;
          if (previewPollRef.current) {
            window.clearTimeout(previewPollRef.current);
            previewPollRef.current = null;
          }
          return;
        }

        if (data.state === "failed") {
          setPreviewReady((p) => ({ ...p, brief: false }));
          setActiveJob(null);
          previewPollStartedAtRef.current = null;
          previewPollLastStateRef.current = null;
          if (previewPollRef.current) {
            window.clearTimeout(previewPollRef.current);
            previewPollRef.current = null;
          }
          return;
        }

        schedulePreviewPoll();
      } catch (err) {
        appendLog("err", `Status check failed: ${String(err)}`);
        setActiveJob(null);
        previewPollStartedAtRef.current = null;
        previewPollLastStateRef.current = null;
        if (previewPollRef.current) {
          window.clearTimeout(previewPollRef.current);
          previewPollRef.current = null;
        }
      }
    }, 8000);
  }

  async function runAction(digestKey: DigestKey, action: "ingest" | "preview" | "send") {
    const jobKey = `${digestKey}-${action}`;
    if (activeJob) return; // already running

    setActiveJob(jobKey);
    setLogs([{ type: "info", text: `Starting ${jobKey}…` }]);
    previewPollStartedAtRef.current = null;
    previewPollLastStateRef.current = null;
    if (previewPollRef.current) {
      window.clearTimeout(previewPollRef.current);
      previewPollRef.current = null;
    }
    if (action === "preview") {
      setPreviewReady((p) => ({ ...p, [digestKey]: false }));
    }

    try {
      const res = await fetch(`/api/admin/run?action=${jobKey}`);
      if (!res.ok || !res.body) {
        appendLog("err", `HTTP ${res.status}: failed to start`);
        setActiveJob(null);
        return;
      }

      const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
      readerRef.current = reader as ReadableStreamDefaultReader;

      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += value;

        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          try {
            const event = JSON.parse(line.slice(5).trim()) as { type: string; text: string; startedAt?: string };
            appendLog(event.type, event.text);
            if (event.type === "done") {
              if (action === "preview" && digestKey === "brief" && isVercel) {
                previewPollStartedAtRef.current = event.startedAt ? new Date(event.startedAt).getTime() : null;
                previewPollLastStateRef.current = "pending";
                appendLog("info", "Watching GitHub Actions for completion…");
                schedulePreviewPoll();
                return;
              }

              if (action === "preview") {
                setPreviewReady((p) => ({ ...p, [digestKey]: true }));
              }
            }
          } catch { /* malformed line */ }
        }
      }
    } catch (err) {
      appendLog("err", String(err));
    } finally {
      if (!(isVercel && action === "preview" && digestKey === "brief")) {
        setActiveJob(null);
      }
    }
  }

  function openPreview(digest: Digest) {
    if (digest.key === "brief" && previewToken) {
      window.open(`/preview/${previewToken}`, "_blank");
      return;
    }

    if (digest.key === "markets" && previewToken) {
      window.open(`/markets/preview/${previewToken}`, "_blank");
      return;
    }

    // The other briefs still rely on the local static preview file server in development.
    window.open(`http://localhost:8765/${digest.previewFile}`, "_blank");
  }

  if (authed === null) {
    return (
      <div className="admin-page admin-page--loading">
        <p className="admin-loading">Loading…</p>
      </div>
    );
  }

  if (!authed) {
    return <LoginScreen onLogin={() => { setAuthed(true); fetch("/api/admin/subscribers").then((r) => r.json()).then((d: Stats) => setStats(d)); }} />;
  }

  return (
    <div className="admin-page">
      <div className="admin-shell">

        {/* Header */}
        <div className="admin-header">
          <p className="admin-kicker">
            Admin
          </p>
          <h1 className="admin-title">
            The Operating Brief
          </h1>
        </div>

        {/* Subscriber stats */}
        <div className="admin-stats">
          {DIGESTS.map((d) => (
            <div key={d.key} className="admin-card admin-card--stats">
              <p className="admin-card__eyebrow">
                {d.label.replace("The ", "")}
              </p>
              <p className="admin-card__number">
                {stats ? stats[d.key] : "—"}
              </p>
              <p className="admin-card__caption">
                subscribers
              </p>
            </div>
          ))}
        </div>

        {/* Digest cards */}
        <div className="admin-grid">
          {DIGESTS.map((digest) => {
            const isRunningIngest = activeJob === `${digest.key}-ingest`;
            const isRunningPreview = activeJob === `${digest.key}-preview`;
            const isRunningSend = activeJob === `${digest.key}-send`;
            const anyRunning = !!activeJob;
            const hasPreview = previewReady[digest.key];

            return (
              <div key={digest.key} className="admin-card admin-card--digest">
                <p className="admin-card__eyebrow">
                  Brief
                </p>
                <h2 className="admin-card__title">
                  {digest.label}
                </h2>
                <p className="admin-card__description">
                  {digest.description}
                </p>

                <div className="admin-actions">
                  {/* Ingest (sports only) */}
                  {digest.hasIngest && (
                    <button
                      onClick={() => runAction(digest.key, "ingest")}
                      disabled={anyRunning}
                      className="admin-button admin-button--ghost"
                    >
                      {isRunningIngest ? "Ingesting…" : "Ingest"}
                    </button>
                  )}

                  {/* Generate + Preview */}
                  <button
                    onClick={() => runAction(digest.key, "preview")}
                    disabled={anyRunning}
                    className="admin-button admin-button--primary"
                  >
                    {isRunningPreview ? "Generating…" : "Generate"}
                  </button>

                  {/* Open preview */}
                  <button
                    onClick={() => openPreview(digest)}
                    disabled={!hasPreview}
                    className="admin-button admin-button--ghost"
                  >
                    Preview
                  </button>

                  {/* Send */}
                  <button
                    onClick={() => {
                      if (!hasPreview) return;
                      if (!confirm(`Send ${digest.label} to all subscribers?`)) return;
                      runAction(digest.key, "send");
                    }}
                    disabled={anyRunning || !hasPreview}
                    className="admin-button admin-button--success"
                  >
                    {isRunningSend ? "Sending…" : "Send"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Log output */}
        <div className="admin-log">
          <div className="admin-log__header">
            <p className="admin-log__label">
              Output {activeJob ? `— ${activeJob}` : ""}
            </p>
            {logs.length > 0 && (
              <button
                onClick={() => setLogs([])}
                className="admin-log__clear"
              >
                Clear
              </button>
            )}
          </div>
          <div className="admin-log__body">
            {logs.length === 0 ? (
              <p className="admin-log__empty">No output yet. Click Generate to run a digest.</p>
            ) : (
              logs.map((entry, i) => (
                <p
                  key={i}
                  className={`admin-log__line admin-log__line--${entry.type}`}
                >
                  {entry.text}
                </p>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </div>

        {/* Footer note */}
        <p className="admin-footer">
          Admin panel runs on the website. The Operating Brief and Markets previews open at{" "}
          <code>/preview/[token]</code> and{" "}
          <code>/markets/preview/[token]</code>; the other briefs still use{" "}
          <code>python serve.py</code> on port 8765 during local development.
        </p>
      </div>
    </div>
  );
}

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
    <div style={{ backgroundColor: "#f5f4f0", minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
      <div style={{ backgroundColor: "#ffffff", padding: "48px", width: "100%", maxWidth: "400px" }}>
        <p style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", color: "#888", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "8px" }}>
          Admin
        </p>
        <h1 style={{ fontFamily: "Georgia, serif", fontSize: "28px", fontWeight: 700, color: "#111", marginBottom: "32px", borderBottom: "3px solid #111", paddingBottom: "16px" }}>
          The Operating Brief
        </h1>
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
            style={{ width: "100%", border: "1px solid #111", padding: "12px", fontFamily: "Arial, sans-serif", fontSize: "14px", marginBottom: "12px", outline: "none", boxSizing: "border-box" }}
          />
          {error && (
            <p style={{ fontFamily: "Arial, sans-serif", fontSize: "13px", color: "#cc0000", marginBottom: "12px" }}>{error}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            style={{ backgroundColor: loading ? "#555" : "#111", color: "#fff", border: "none", padding: "12px 24px", fontFamily: "Arial, sans-serif", fontSize: "13px", letterSpacing: "0.08em", textTransform: "uppercase", cursor: loading ? "not-allowed" : "pointer" }}
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
export default function AdminDashboard({ previewToken }: AdminDashboardProps) {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [activeJob, setActiveJob] = useState<string | null>(null);
  const [logs, setLogs] = useState<Array<{ type: string; text: string }>>([]);
  const [previewReady, setPreviewReady] = useState<Record<DigestKey, boolean>>({
    brief: false, markets: false, sports: false, paddock: false,
  });
  const logsEndRef = useRef<HTMLDivElement>(null);
  const readerRef = useRef<ReadableStreamDefaultReader | null>(null);

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

  async function runAction(digestKey: DigestKey, action: "ingest" | "preview" | "send") {
    const jobKey = `${digestKey}-${action}`;
    if (activeJob) return; // already running

    setActiveJob(jobKey);
    setLogs([{ type: "info", text: `Starting ${jobKey}…` }]);

    try {
      const res = await fetch(`/api/admin/run?action=${jobKey}`);
      if (!res.ok || !res.body) {
        setLogs((l) => [...l, { type: "err", text: `HTTP ${res.status}: failed to start` }]);
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
            const event = JSON.parse(line.slice(5).trim()) as { type: string; text: string };
            setLogs((l) => [...l, event]);
            if (event.type === "done") {
              if (action === "preview") {
                setPreviewReady((p) => ({ ...p, [digestKey]: true }));
              }
            }
          } catch { /* malformed line */ }
        }
      }
    } catch (err) {
      setLogs((l) => [...l, { type: "err", text: String(err) }]);
    } finally {
      setActiveJob(null);
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
      <div style={{ backgroundColor: "#f5f4f0", minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ fontFamily: "Arial, sans-serif", fontSize: "13px", color: "#888" }}>Loading…</p>
      </div>
    );
  }

  if (!authed) {
    return <LoginScreen onLogin={() => { setAuthed(true); fetch("/api/admin/subscribers").then((r) => r.json()).then((d: Stats) => setStats(d)); }} />;
  }

  return (
    <div style={{ backgroundColor: "#f5f4f0", minHeight: "100vh", padding: "32px 16px" }}>
      <div style={{ maxWidth: "900px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{ marginBottom: "32px" }}>
          <p style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", color: "#888", letterSpacing: "0.12em", textTransform: "uppercase", margin: "0 0 4px" }}>
            Admin
          </p>
          <h1 style={{ fontFamily: "Georgia, serif", fontSize: "32px", fontWeight: 700, color: "#111", margin: "0", paddingBottom: "16px", borderBottom: "3px solid #111" }}>
            The Operating Brief
          </h1>
        </div>

        {/* Subscriber stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "32px" }}>
          {DIGESTS.map((d) => (
            <div key={d.key} style={{ backgroundColor: "#ffffff", padding: "20px 24px" }}>
              <p style={{ fontFamily: "Arial, sans-serif", fontSize: "10px", color: "#888", letterSpacing: "0.12em", textTransform: "uppercase", margin: "0 0 8px" }}>
                {d.label.replace("The ", "")}
              </p>
              <p style={{ fontFamily: "Georgia, serif", fontSize: "32px", fontWeight: 700, color: "#111", margin: 0 }}>
                {stats ? stats[d.key] : "—"}
              </p>
              <p style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", color: "#888", margin: "4px 0 0" }}>
                subscribers
              </p>
            </div>
          ))}
        </div>

        {/* Digest cards */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "24px" }}>
          {DIGESTS.map((digest) => {
            const isRunningIngest = activeJob === `${digest.key}-ingest`;
            const isRunningPreview = activeJob === `${digest.key}-preview`;
            const isRunningSend = activeJob === `${digest.key}-send`;
            const anyRunning = !!activeJob;
            const hasPreview = previewReady[digest.key];

            return (
              <div key={digest.key} style={{ backgroundColor: "#ffffff", padding: "28px" }}>
                <p style={{ fontFamily: "Arial, sans-serif", fontSize: "10px", color: "#888", letterSpacing: "0.12em", textTransform: "uppercase", margin: "0 0 6px" }}>
                  Brief
                </p>
                <h2 style={{ fontFamily: "Georgia, serif", fontSize: "20px", fontWeight: 700, color: "#111", margin: "0 0 6px" }}>
                  {digest.label}
                </h2>
                <p style={{ fontFamily: "Arial, sans-serif", fontSize: "12px", color: "#888", margin: "0 0 24px" }}>
                  {digest.description}
                </p>

                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  {/* Ingest (sports only) */}
                  {digest.hasIngest && (
                    <button
                      onClick={() => runAction(digest.key, "ingest")}
                      disabled={anyRunning}
                      style={{
                        backgroundColor: "transparent",
                        color: anyRunning && !isRunningIngest ? "#aaa" : "#111",
                        border: `1px solid ${anyRunning && !isRunningIngest ? "#ccc" : "#111"}`,
                        padding: "10px 16px",
                        fontFamily: "Arial, sans-serif",
                        fontSize: "12px",
                        letterSpacing: "0.06em",
                        textTransform: "uppercase",
                        cursor: anyRunning ? "not-allowed" : "pointer",
                        opacity: anyRunning && !isRunningIngest ? 0.4 : 1,
                      }}
                    >
                      {isRunningIngest ? "Ingesting…" : "Ingest"}
                    </button>
                  )}

                  {/* Generate + Preview */}
                  <button
                    onClick={() => runAction(digest.key, "preview")}
                    disabled={anyRunning}
                    style={{
                      backgroundColor: isRunningPreview ? "#555" : "#111",
                      color: "#fff",
                      border: "none",
                      padding: "10px 16px",
                      fontFamily: "Arial, sans-serif",
                      fontSize: "12px",
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                      cursor: anyRunning ? "not-allowed" : "pointer",
                      opacity: anyRunning && !isRunningPreview ? 0.4 : 1,
                    }}
                  >
                    {isRunningPreview ? "Generating…" : "Generate"}
                  </button>

                  {/* Open preview */}
                  <button
                    onClick={() => openPreview(digest)}
                    disabled={!hasPreview}
                    style={{
                      backgroundColor: "transparent",
                      color: hasPreview ? "#111" : "#aaa",
                      border: `1px solid ${hasPreview ? "#111" : "#ccc"}`,
                      padding: "10px 16px",
                      fontFamily: "Arial, sans-serif",
                      fontSize: "12px",
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                      cursor: hasPreview ? "pointer" : "not-allowed",
                    }}
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
                    style={{
                      backgroundColor: isRunningSend ? "#555" : (hasPreview ? "#2a6e2a" : "transparent"),
                      color: hasPreview ? "#fff" : "#aaa",
                      border: `1px solid ${hasPreview ? (isRunningSend ? "#555" : "#2a6e2a") : "#ccc"}`,
                      padding: "10px 16px",
                      fontFamily: "Arial, sans-serif",
                      fontSize: "12px",
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                      cursor: (anyRunning || !hasPreview) ? "not-allowed" : "pointer",
                      opacity: anyRunning && !isRunningSend ? 0.4 : 1,
                    }}
                  >
                    {isRunningSend ? "Sending…" : "Send"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Log output */}
        <div style={{ backgroundColor: "#1a1a1a", padding: "0" }}>
          <div style={{ padding: "12px 20px", borderBottom: "1px solid #333", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <p style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", color: "#666", letterSpacing: "0.1em", textTransform: "uppercase", margin: 0 }}>
              Output {activeJob ? `— ${activeJob}` : ""}
            </p>
            {logs.length > 0 && (
              <button
                onClick={() => setLogs([])}
                style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", color: "#555", background: "none", border: "none", cursor: "pointer", letterSpacing: "0.06em", textTransform: "uppercase" }}
              >
                Clear
              </button>
            )}
          </div>
          <div style={{ height: "320px", overflowY: "auto", padding: "16px 20px", fontFamily: "monospace", fontSize: "12px", lineHeight: "1.6" }}>
            {logs.length === 0 ? (
              <p style={{ color: "#444", margin: 0 }}>No output yet. Click Generate to run a digest.</p>
            ) : (
              logs.map((entry, i) => (
                <p
                  key={i}
                  style={{
                    margin: "0 0 2px",
                    color: entry.type === "err" ? "#f87171" : entry.type === "done" ? "#86efac" : entry.type === "start" ? "#93c5fd" : "#d1d5db",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-all",
                  }}
                >
                  {entry.text}
                </p>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </div>

        {/* Footer note */}
        <p style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", color: "#999", textAlign: "center", marginTop: "24px" }}>
          Admin panel runs on the website. The Operating Brief and Markets previews open at{" "}
          <code style={{ fontSize: "11px" }}>/preview/[token]</code> and{" "}
          <code style={{ fontSize: "11px" }}>/markets/preview/[token]</code>; the other briefs still use{" "}
          <code style={{ fontSize: "11px" }}>python serve.py</code> on port 8765 during local development.
        </p>
      </div>
    </div>
  );
}

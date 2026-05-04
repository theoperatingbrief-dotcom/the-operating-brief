"use client";

import { useState, useRef } from "react";

type SendState = "idle" | "confirming" | "sending" | "done" | "error";
type GenState = "idle" | "triggered" | "error";

export default function AdminControls({ token }: { token: string }) {
  const [sendState, setSendState] = useState<SendState>("idle");
  const [genState, setGenState] = useState<GenState>("idle");
  const [sendResult, setSendResult] = useState<{ sent: number; failed: string[] } | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  async function handleGenerate() {
    setGenState("triggered");
    try {
      const res = await fetch(`/api/preview/${token}/generate`, { method: "POST" });
      if (!res.ok) setGenState("error");
    } catch {
      setGenState("error");
    }
  }

  function handleRefresh() {
    if (iframeRef.current) {
      iframeRef.current.src = `/api/preview/${token}/html?t=${Date.now()}`;
    }
  }

  async function handleSend() {
    if (sendState === "idle") { setSendState("confirming"); return; }
    if (sendState === "confirming") {
      setSendState("sending");
      try {
        const res = await fetch(`/api/preview/${token}/send`, { method: "POST" });
        const data = await res.json();
        setSendResult(data);
        setSendState(data.failed?.length ? "error" : "done");
      } catch {
        setSendState("error");
      }
    }
  }

  return (
    <>
      {/* Sticky toolbar */}
      <div style={{
        background: "#111", padding: "12px 24px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "sticky", top: 0, zIndex: 10,
      }}>
        <span style={{ color: "#fff", fontFamily: "Georgia, serif", fontSize: "16px", fontWeight: 700 }}>
          The Operating Brief — Preview
        </span>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {/* Generate section */}
          {genState === "idle" && (
            <button onClick={handleGenerate} style={secondaryBtn}>
              Generate New Draft
            </button>
          )}
          {genState === "triggered" && (
            <>
              <span style={{ color: "#facc15", fontSize: "13px", fontFamily: "Arial, sans-serif" }}>
                ⏳ Generating (~5 min)…
              </span>
              <button onClick={handleRefresh} style={secondaryBtn}>
                Refresh Preview
              </button>
            </>
          )}
          {genState === "error" && (
            <span style={{ color: "#f87171", fontSize: "13px", fontFamily: "Arial, sans-serif" }}>
              ⚠ Generate failed
            </span>
          )}

          <div style={{ width: "1px", height: "24px", background: "#333" }} />

          {/* Send section */}
          {sendState === "done" && (
            <span style={{ color: "#4ade80", fontSize: "14px", fontFamily: "Arial, sans-serif" }}>
              ✓ Sent to {sendResult?.sent} subscribers
            </span>
          )}
          {sendState === "error" && (
            <span style={{ color: "#f87171", fontSize: "14px", fontFamily: "Arial, sans-serif" }}>
              ⚠ Sent {sendResult?.sent ?? 0}{sendResult?.failed?.length ? `, failed: ${sendResult.failed.join(", ")}` : ""}
            </span>
          )}
          {(sendState === "idle" || sendState === "confirming" || sendState === "sending") && (
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              {sendState === "confirming" && (
                <button onClick={() => setSendState("idle")} style={cancelBtn}>
                  Cancel
                </button>
              )}
              <button
                onClick={handleSend}
                disabled={sendState === "sending"}
                style={{
                  ...primaryBtn,
                  background: sendState === "confirming" ? "#dc2626" : "#fff",
                  color: sendState === "confirming" ? "#fff" : "#111",
                  opacity: sendState === "sending" ? 0.6 : 1,
                  cursor: sendState === "sending" ? "not-allowed" : "pointer",
                }}
              >
                {sendState === "sending" ? "Sending…"
                  : sendState === "confirming" ? "Confirm — Send to All"
                  : "Send to All Subscribers"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Email preview iframe */}
      <iframe
        ref={iframeRef}
        src={`/api/preview/${token}/html`}
        style={{ width: "100%", height: "calc(100vh - 48px)", border: "none", display: "block" }}
      />
    </>
  );
}

const base: React.CSSProperties = {
  border: "none", borderRadius: "4px", padding: "8px 16px",
  fontSize: "13px", fontWeight: 700, cursor: "pointer",
  fontFamily: "Arial, sans-serif",
};
const primaryBtn: React.CSSProperties = { ...base, fontSize: "14px", padding: "8px 20px" };
const secondaryBtn: React.CSSProperties = { ...base, background: "transparent", color: "#ccc", border: "1px solid #444" };
const cancelBtn: React.CSSProperties = { ...base, background: "transparent", color: "#888", border: "1px solid #444" };

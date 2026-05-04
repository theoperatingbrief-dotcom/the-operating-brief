"use client";

import { useState } from "react";

export default function SendButton({ token }: { token: string }) {
  const [state, setState] = useState<"idle" | "confirming" | "sending" | "done" | "error">("idle");
  const [result, setResult] = useState<{ sent: number; failed: string[] } | null>(null);

  async function handleClick() {
    if (state === "idle") {
      setState("confirming");
      return;
    }
    if (state === "confirming") {
      setState("sending");
      try {
        const res = await fetch(`/api/preview/${token}/send`, { method: "POST" });
        const data = await res.json();
        setResult(data);
        setState(data.failed?.length ? "error" : "done");
      } catch {
        setState("error");
      }
    }
  }

  function handleCancel() {
    setState("idle");
  }

  if (state === "done") {
    return (
      <span style={{ color: "#4ade80", fontSize: "14px", fontFamily: "Arial, sans-serif" }}>
        ✓ Sent to {result?.sent} subscribers
      </span>
    );
  }

  if (state === "error") {
    return (
      <span style={{ color: "#f87171", fontSize: "14px", fontFamily: "Arial, sans-serif" }}>
        ⚠ Sent {result?.sent ?? 0}
        {result?.failed?.length ? `, failed: ${result.failed.join(", ")}` : ", unexpected error"}
      </span>
    );
  }

  return (
    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
      {state === "confirming" && (
        <button
          onClick={handleCancel}
          style={{
            background: "transparent",
            color: "#888",
            border: "1px solid #444",
            borderRadius: "4px",
            padding: "8px 16px",
            fontSize: "13px",
            cursor: "pointer",
            fontFamily: "Arial, sans-serif",
          }}
        >
          Cancel
        </button>
      )}
      <button
        onClick={handleClick}
        disabled={state === "sending"}
        style={{
          background: state === "confirming" ? "#dc2626" : "#fff",
          color: state === "confirming" ? "#fff" : "#111",
          border: "none",
          borderRadius: "4px",
          padding: "8px 20px",
          fontSize: "14px",
          fontWeight: 700,
          cursor: state === "sending" ? "not-allowed" : "pointer",
          fontFamily: "Arial, sans-serif",
          opacity: state === "sending" ? 0.6 : 1,
        }}
      >
        {state === "sending"
          ? "Sending…"
          : state === "confirming"
          ? "Confirm — Send to All"
          : "Send to All Subscribers"}
      </button>
    </div>
  );
}

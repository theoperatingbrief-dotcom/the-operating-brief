"use client";

import { useState } from "react";
import { EditorialShell } from "../components/EditorialShell";

export default function MarketsHome() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error" | "duplicate">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");

    try {
      const res = await fetch("/api/markets/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (res.ok) {
        setStatus("success");
      } else if (res.status === 409) {
        setStatus("duplicate");
      } else {
        const data = await res.json().catch(() => ({}));
        setErrorMessage(data.error || "Something went wrong. Please try again.");
        setStatus("error");
      }
    } catch {
      setErrorMessage("Network error. Please try again.");
      setStatus("error");
    }
  }

  return (
    <EditorialShell
      activeHref="/markets"
      eyebrow="Daily · ASX Pre-Market"
      title="The Markets Brief"
      subtitle="ASX · Macro · Commodities · FX · Bitcoin"
      archiveHref="/markets/archive"
      archiveLabel="View past editions →"
      footerCopy="Your daily ASX pre-market briefing."
    >
      <section className="content-stack">
        <p style={{ fontFamily: "Georgia, serif", fontSize: "18px", color: "#222222", lineHeight: 1.7, maxWidth: "58ch" }}>
          Every weekday morning before the ASX opens, <em>The Markets Brief</em> delivers live market data, overnight US moves, ASX movers, and the macro stories driving Australian markets.
        </p>
        <p style={{ fontFamily: "Georgia, serif", fontSize: "18px", color: "#222222", lineHeight: 1.7, maxWidth: "58ch" }}>
          In your inbox by 7:30am AEST. Free.
        </p>
      </section>

      <div style={{ borderTop: "1px solid #dddddd", margin: "10px 0 0" }} />

      {status === "success" ? (
        <section className="content-stack">
          <p className="eyebrow">Confirmed</p>
          <p style={{ fontFamily: "Georgia, serif", fontSize: "22px", color: "#111111", fontWeight: 700, lineHeight: 1.35, maxWidth: "28ch" }}>
            You&apos;re in. See you at 7:30am.
          </p>
        </section>
      ) : status === "duplicate" ? (
        <section className="content-stack">
          <p className="eyebrow">Already subscribed</p>
          <p style={{ fontFamily: "Georgia, serif", fontSize: "17px", color: "#222222", lineHeight: 1.7, maxWidth: "52ch" }}>
            That email is already on the list. See you tomorrow morning.
          </p>
        </section>
      ) : (
        <form onSubmit={handleSubmit} className="content-stack">
          <p className="eyebrow">Subscribe - Free</p>

          <input
            type="email"
            placeholder="Your email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              width: "100%",
              border: "1px solid #111111",
              borderRadius: 0,
              padding: "12px",
              fontFamily: "Arial, sans-serif",
              fontSize: "14px",
              color: "#222222",
              backgroundColor: "#ffffff",
              outline: "none",
            }}
          />

          {status === "error" && (
            <p style={{ fontFamily: "Arial, sans-serif", fontSize: "13px", color: "#222222" }}>
              {errorMessage}
            </p>
          )}

          <button
            type="submit"
            disabled={status === "loading"}
            style={{
              backgroundColor: status === "loading" ? "#555555" : "#111111",
              color: "#ffffff",
              border: "none",
              borderRadius: 0,
              padding: "12px 24px",
              fontFamily: "Arial, sans-serif",
              fontSize: "14px",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              cursor: status === "loading" ? "not-allowed" : "pointer",
              width: "fit-content",
            }}
          >
            {status === "loading" ? "Subscribing…" : "Subscribe"}
          </button>
        </form>
      )}
    </EditorialShell>
  );
}

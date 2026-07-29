"use client";

import { useState } from "react";
import { EditorialShell } from "../components/EditorialShell";

export default function SportingHome() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error" | "duplicate">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");

    try {
      const res = await fetch("/api/sporting/subscribe", {
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
      activeHref="/sporting"
      eyebrow="Weekend Briefing"
      title="The Sporting Brief"
      subtitle="NRL · AFL · Football · F1 · NBA · Golf & more"
      archiveHref="/sporting/archive"
      archiveLabel="View past editions →"
      footerCopy="Your weekend AI-powered sports briefing."
    >
      <section className="content-stack">
        <p style={{ fontFamily: "Georgia, serif", fontSize: "18px", color: "#222222", lineHeight: 1.7, maxWidth: "58ch" }}>
          Every weekend, <em>The Sporting Brief</em> delivers a sharp, AI-powered wrap of the results and stories that matter.
        </p>
        <p style={{ fontFamily: "Georgia, serif", fontSize: "18px", color: "#222222", lineHeight: 1.7, maxWidth: "58ch" }}>
          All the scores. The big stories. Straight to your inbox.
        </p>
      </section>

      <div style={{ borderTop: "1px solid #dddddd", margin: "10px 0 0" }} />

      {status === "success" ? (
        <section className="content-stack">
          <p className="eyebrow">Confirmed</p>
          <p style={{ fontFamily: "Georgia, serif", fontSize: "22px", color: "#111111", fontWeight: 700, lineHeight: 1.35, maxWidth: "28ch" }}>
            You&apos;re in. Check your inbox this weekend.
          </p>
        </section>
      ) : status === "duplicate" ? (
        <section className="content-stack">
          <p className="eyebrow">Already subscribed</p>
          <p style={{ fontFamily: "Georgia, serif", fontSize: "17px", color: "#222222", lineHeight: 1.7, maxWidth: "52ch" }}>
            That email is already on the list. See you this weekend.
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

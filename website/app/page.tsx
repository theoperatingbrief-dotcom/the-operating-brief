"use client";

import { useEffect, useState } from "react";
import { EditorialShell } from "./components/EditorialShell";

export default function Home() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error" | "duplicate">("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [referralUrl, setReferralUrl] = useState<string | null>(null);
  const [refCode, setRefCode] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const ref = params.get("ref");
    if (ref) setRefCode(ref);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");

    try {
      const res = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, ref: refCode }),
      });

      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        setReferralUrl(data.referralUrl ?? null);
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
      activeHref="/"
      eyebrow="Daily Briefing"
      title="The Operating Brief"
      subtitle="For Australian business operators"
      archiveHref="/archive"
      archiveLabel="View past editions →"
      footerCopy="Your daily AI-powered business briefing."
    >
      <section className="content-stack">
        <p style={{ fontFamily: "Georgia, serif", fontSize: "18px", color: "#222222", lineHeight: 1.7, maxWidth: "58ch" }}>
          Every weekday morning, <em>The Operating Brief</em> delivers a sharp,
          AI-powered summary of the business and technology stories that matter
          to operators running companies in Australia.
        </p>
        <p style={{ fontFamily: "Georgia, serif", fontSize: "18px", color: "#222222", lineHeight: 1.7, maxWidth: "58ch" }}>
          No noise. No filler. Straight to your inbox before 7 am.
        </p>
      </section>

      <div style={{ borderTop: "1px solid #dddddd", margin: "10px 0 0" }} />

      {status === "success" ? (
        <section className="content-stack">
          <p className="eyebrow">Confirmed</p>
          <p style={{ fontFamily: "Georgia, serif", fontSize: "22px", color: "#111111", fontWeight: 700, lineHeight: 1.35, maxWidth: "28ch" }}>
            You&apos;re in. Check your inbox tomorrow morning.
          </p>
          {referralUrl && (
            <div style={{ backgroundColor: "#f7f5ef", padding: "22px", border: "1px solid #e4ddd0" }}>
              <p className="eyebrow" style={{ marginBottom: "8px" }}>
                Your referral link
              </p>
              <p style={{ fontFamily: "Georgia, serif", fontSize: "15px", color: "#222222", lineHeight: 1.65, marginBottom: "14px" }}>
                First to 10 referrals wins an official <em>Operating Brief</em> mug. Share your link and start the race.
              </p>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                <code
                  style={{
                    fontFamily: "monospace",
                    fontSize: "13px",
                    color: "#111111",
                    backgroundColor: "#ffffff",
                    padding: "8px 12px",
                    border: "1px solid #dddddd",
                    flex: 1,
                    minWidth: "0",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {referralUrl}
                </code>
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText(referralUrl)}
                  style={{
                    backgroundColor: "#111111",
                    color: "#ffffff",
                    border: "none",
                    padding: "8px 16px",
                    fontFamily: "Arial, sans-serif",
                    fontSize: "12px",
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    cursor: "pointer",
                    flexShrink: 0,
                  }}
                >
                  Copy
                </button>
              </div>
            </div>
          )}
        </section>
      ) : status === "duplicate" ? (
        <section className="content-stack">
          <p className="eyebrow">Already subscribed</p>
          <p style={{ fontFamily: "Georgia, serif", fontSize: "17px", color: "#222222", lineHeight: 1.7, maxWidth: "52ch" }}>
            That email is already on the list. See you in the morning.
          </p>
        </section>
      ) : (
        <form onSubmit={handleSubmit} className="content-stack">
          <p className="eyebrow">Subscribe - Free</p>

          <div style={{ display: "grid", gap: "12px" }}>
            <input
              type="text"
              placeholder="First name (optional)"
              value={name}
              onChange={(e) => setName(e.target.value)}
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
          </div>

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

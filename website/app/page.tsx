"use client";

import { useState, useEffect } from "react";

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

  const navLinks = [
    { label: "The Operating Brief", href: "/" },
    { label: "The Sporting Brief", href: "/sporting" },
    { label: "The Markets Brief", href: "/markets" },
  ];

  return (
    <div style={{ backgroundColor: "#f5f4f0", minHeight: "100vh", padding: "40px 16px" }}>
      <div
        style={{
          maxWidth: "620px",
          margin: "0 auto",
          backgroundColor: "#ffffff",
          padding: "48px",
        }}
      >
        {/* Cross-brief nav */}
        <nav style={{ marginBottom: "32px", paddingBottom: "16px", borderBottom: "1px solid #eeeeee" }}>
          <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
            {navLinks.map((link) => {
              const active = link.href === "/";
              return (
                <a
                  key={link.href}
                  href={link.href}
                  style={{
                    fontFamily: "Arial, sans-serif",
                    fontSize: "11px",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: active ? "#111111" : "#999999",
                    textDecoration: "none",
                    fontWeight: active ? 700 : 400,
                    borderBottom: active ? "2px solid #111111" : "none",
                    paddingBottom: "2px",
                  }}
                >
                  {link.label}
                </a>
              );
            })}
          </div>
        </nav>

        {/* Header */}
        <header style={{ marginBottom: "32px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "8px" }}>
            <p
              style={{
                fontFamily: "Arial, sans-serif",
                fontSize: "11px",
                color: "#888888",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                margin: "0",
              }}
            >
              Daily Briefing
            </p>
            <a
              href="/archive"
              style={{
                fontFamily: "Arial, sans-serif",
                fontSize: "12px",
                color: "#888888",
                textDecoration: "none",
                borderBottom: "1px solid #cccccc",
              }}
            >
              View past editions →
            </a>
          </div>
          <h1
            style={{
              fontFamily: "Georgia, serif",
              fontSize: "40px",
              fontWeight: 700,
              color: "#111111",
              lineHeight: 1.1,
              paddingBottom: "16px",
              borderBottom: "3px solid #111111",
            }}
          >
            The Operating Brief
          </h1>
          <p
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: "13px",
              color: "#555555",
              marginTop: "10px",
            }}
          >
            For Australian business operators
          </p>
        </header>

        {/* Body */}
        <div style={{ marginBottom: "40px" }}>
          <p
            style={{
              fontFamily: "Georgia, serif",
              fontSize: "16px",
              color: "#222222",
              lineHeight: 1.75,
              marginBottom: "16px",
            }}
          >
            Every weekday morning, <em>The Operating Brief</em> delivers a sharp,
            AI-powered summary of the business and technology stories that matter
            to operators running companies in Australia.
          </p>
          <p
            style={{
              fontFamily: "Georgia, serif",
              fontSize: "16px",
              color: "#222222",
              lineHeight: 1.75,
            }}
          >
            No noise. No filler. Straight to your inbox before 7 am.
          </p>
        </div>

        <div style={{ borderTop: "1px solid #dddddd", marginBottom: "40px" }} />

        {/* Subscribe Form */}
        {status === "success" ? (
          <div>
            <p
              style={{
                fontFamily: "Arial, sans-serif",
                fontSize: "11px",
                color: "#888888",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                marginBottom: "12px",
              }}
            >
              Confirmed
            </p>
            <p
              style={{
                fontFamily: "Georgia, serif",
                fontSize: "20px",
                color: "#111111",
                fontWeight: 700,
                marginBottom: "24px",
              }}
            >
              You&apos;re in. Check your inbox tomorrow morning.
            </p>
            {referralUrl && (
              <div style={{ backgroundColor: "#f5f4f0", padding: "24px", marginTop: "8px" }}>
                <p
                  style={{
                    fontFamily: "Arial, sans-serif",
                    fontSize: "11px",
                    color: "#888888",
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    margin: "0 0 8px 0",
                  }}
                >
                  Your referral link
                </p>
                <p
                  style={{
                    fontFamily: "Georgia, serif",
                    fontSize: "15px",
                    color: "#222222",
                    lineHeight: 1.6,
                    margin: "0 0 16px 0",
                  }}
                >
                  Share this link — every person who subscribes through it counts toward a reward.
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
          </div>
        ) : status === "duplicate" ? (
          <div>
            <p
              style={{
                fontFamily: "Arial, sans-serif",
                fontSize: "11px",
                color: "#888888",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                marginBottom: "12px",
              }}
            >
              Already subscribed
            </p>
            <p
              style={{
                fontFamily: "Georgia, serif",
                fontSize: "16px",
                color: "#222222",
                lineHeight: 1.75,
              }}
            >
              That email is already on the list. See you in the morning.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <p
              style={{
                fontFamily: "Arial, sans-serif",
                fontSize: "11px",
                color: "#888888",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                marginBottom: "16px",
              }}
            >
              Subscribe — Free
            </p>

            <div style={{ marginBottom: "12px" }}>
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
            </div>

            <div style={{ marginBottom: "12px" }}>
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
              <p
                style={{
                  fontFamily: "Arial, sans-serif",
                  fontSize: "13px",
                  color: "#222222",
                  marginBottom: "12px",
                }}
              >
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
                transition: "background-color 0.15s",
              }}
              onMouseEnter={(e) => {
                if (status !== "loading") (e.target as HTMLButtonElement).style.backgroundColor = "#333333";
              }}
              onMouseLeave={(e) => {
                if (status !== "loading") (e.target as HTMLButtonElement).style.backgroundColor = "#111111";
              }}
            >
              {status === "loading" ? "Subscribing…" : "Subscribe"}
            </button>
          </form>
        )}

        {/* Footer */}
        <footer style={{ marginTop: "48px", borderTop: "2px solid #111111", paddingTop: "16px" }}>
          <p
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: "12px",
              color: "#888888",
              marginBottom: "8px",
            }}
          >
            Your daily AI-powered business briefing — published weekday mornings.
          </p>
          <p style={{ fontFamily: "Arial, sans-serif", fontSize: "12px", color: "#888888", margin: 0 }}>
            <a href="/privacy" style={{ color: "#555555", marginRight: "16px", textDecoration: "underline" }}>Privacy Policy</a>
            <a href="/terms" style={{ color: "#555555", textDecoration: "underline" }}>Terms of Use</a>
          </p>
        </footer>
      </div>
    </div>
  );
}

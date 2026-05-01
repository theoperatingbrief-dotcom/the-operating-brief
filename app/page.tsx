"use client";

import { useState } from "react";

export default function Home() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error" | "duplicate">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");

    try {
      const res = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name }),
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
    <div style={{ backgroundColor: "#f5f4f0", minHeight: "100vh", padding: "40px 16px" }}>
      <div
        style={{
          maxWidth: "620px",
          margin: "0 auto",
          backgroundColor: "#ffffff",
          padding: "48px",
        }}
      >
        {/* Header */}
        <header style={{ marginBottom: "32px" }}>
          <p
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: "11px",
              color: "#888888",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              marginBottom: "8px",
            }}
          >
            Daily Briefing
          </p>
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
              }}
            >
              You&apos;re in. Check your inbox tomorrow morning.
            </p>
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
            }}
          >
            Your daily AI-powered business briefing — published weekday mornings.
          </p>
        </footer>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";

export default function MarketsUnsubscribePage() {
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) {
      setStatus("error");
      return;
    }
    fetch("/api/markets/unsubscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then((r) => setStatus(r.ok ? "success" : "error"))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <div style={{ backgroundColor: "#f5f4f0", minHeight: "100vh", padding: "40px 16px" }}>
      <div style={{ maxWidth: "620px", margin: "0 auto", backgroundColor: "#ffffff", padding: "48px" }}>
        <p style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", color: "#888888", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "8px" }}>
          The Markets Brief
        </p>
        <h1 style={{ fontFamily: "Georgia, serif", fontSize: "32px", fontWeight: 700, color: "#111111", borderBottom: "3px solid #111111", paddingBottom: "16px", marginBottom: "24px" }}>
          {status === "loading" && "Unsubscribing…"}
          {status === "success" && "You've been unsubscribed."}
          {status === "error" && "Something went wrong."}
        </h1>
        {status === "success" && (
          <p style={{ fontFamily: "Georgia, serif", fontSize: "16px", color: "#222222", lineHeight: 1.75 }}>
            You won&apos;t receive any more emails from The Markets Brief. Changed your mind?{" "}
            <a href="/markets" style={{ color: "#111111" }}>Subscribe again here.</a>
          </p>
        )}
        {status === "error" && (
          <p style={{ fontFamily: "Georgia, serif", fontSize: "16px", color: "#222222", lineHeight: 1.75 }}>
            The link may be invalid or already used. Email{" "}
            <a href="mailto:hello@theoperatingbrief.com" style={{ color: "#111111" }}>hello@theoperatingbrief.com</a>{" "}
            and we&apos;ll sort it out.
          </p>
        )}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function UnsubscribeContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "not_found" | "error">("loading");

  useEffect(() => {
    if (!token) {
      setStatus("not_found");
      return;
    }

    fetch(`/api/unsubscribe?token=${encodeURIComponent(token)}`)
      .then((res) => {
        if (res.ok) {
          setStatus("success");
        } else if (res.status === 404) {
          setStatus("not_found");
        } else {
          setStatus("error");
        }
      })
      .catch(() => setStatus("error"));
  }, [token]);

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

        <div style={{ borderTop: "1px solid #dddddd", marginBottom: "40px" }} />

        {/* Status */}
        {status === "loading" && (
          <p
            style={{
              fontFamily: "Georgia, serif",
              fontSize: "16px",
              color: "#888888",
              lineHeight: 1.75,
            }}
          >
            Processing your request…
          </p>
        )}

        {status === "success" && (
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
              Unsubscribed
            </p>
            <p
              style={{
                fontFamily: "Georgia, serif",
                fontSize: "20px",
                fontWeight: 700,
                color: "#111111",
                marginBottom: "16px",
              }}
            >
              You&apos;ve been unsubscribed.
            </p>
            <p
              style={{
                fontFamily: "Georgia, serif",
                fontSize: "16px",
                color: "#222222",
                lineHeight: 1.75,
              }}
            >
              You won&apos;t receive any more emails from us. Changed your mind?{" "}
              <a
                href="/"
                style={{
                  color: "#111111",
                  borderBottom: "1px solid #111111",
                }}
              >
                Re-subscribe here.
              </a>
            </p>
          </div>
        )}

        {status === "not_found" && (
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
              Link not found
            </p>
            <p
              style={{
                fontFamily: "Georgia, serif",
                fontSize: "20px",
                fontWeight: 700,
                color: "#111111",
                marginBottom: "16px",
              }}
            >
              This unsubscribe link is invalid.
            </p>
            <p
              style={{
                fontFamily: "Georgia, serif",
                fontSize: "16px",
                color: "#222222",
                lineHeight: 1.75,
              }}
            >
              The link may have already been used, or may have expired. If you
              still wish to unsubscribe, please reply to any email from us.
            </p>
          </div>
        )}

        {status === "error" && (
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
              Error
            </p>
            <p
              style={{
                fontFamily: "Georgia, serif",
                fontSize: "16px",
                color: "#222222",
                lineHeight: 1.75,
              }}
            >
              Something went wrong. Please try again or reply to any email from us
              to unsubscribe.
            </p>
          </div>
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

export default function UnsubscribePage() {
  return (
    <Suspense
      fallback={
        <div style={{ backgroundColor: "#f5f4f0", minHeight: "100vh", padding: "40px 16px" }}>
          <div style={{ maxWidth: "620px", margin: "0 auto", backgroundColor: "#ffffff", padding: "48px" }}>
            <p style={{ fontFamily: "Georgia, serif", fontSize: "16px", color: "#888888" }}>
              Loading…
            </p>
          </div>
        </div>
      }
    >
      <UnsubscribeContent />
    </Suspense>
  );
}

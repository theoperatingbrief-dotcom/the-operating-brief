export default function Terms() {
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
        <header style={{ marginBottom: "32px" }}>
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
            <a href="/" style={{ color: "#888888", textDecoration: "none", borderBottom: "1px solid #cccccc" }}>
              The Operating Brief
            </a>
          </p>
          <h1
            style={{
              fontFamily: "Georgia, serif",
              fontSize: "32px",
              fontWeight: 700,
              color: "#111111",
              lineHeight: 1.1,
              paddingBottom: "16px",
              borderBottom: "3px solid #111111",
            }}
          >
            Terms of Use
          </h1>
          <p style={{ fontFamily: "Arial, sans-serif", fontSize: "12px", color: "#888888", marginTop: "10px" }}>
            Last updated: May 2026
          </p>
        </header>

        <div style={{ fontFamily: "Georgia, serif", fontSize: "15px", color: "#222222", lineHeight: 1.8 }}>
          <h2 style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#888888", marginTop: "32px", marginBottom: "8px" }}>
            The service
          </h2>
          <p style={{ marginTop: 0 }}>
            The Operating Brief is a free daily email newsletter. By subscribing, you agree to receive weekday emails from us. You can unsubscribe at any time.
          </p>

          <h2 style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#888888", marginTop: "32px", marginBottom: "8px" }}>
            Content
          </h2>
          <p style={{ marginTop: 0 }}>
            The Operating Brief is an AI-assisted editorial product. Content is intended for general informational purposes only and does not constitute financial, legal, or professional advice. We make no representations as to the accuracy or completeness of any information published.
          </p>

          <h2 style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#888888", marginTop: "32px", marginBottom: "8px" }}>
            Intellectual property
          </h2>
          <p style={{ marginTop: 0 }}>
            All original content published in The Operating Brief is owned by its publishers. You may share individual stories with appropriate attribution but may not republish editions in full without permission.
          </p>

          <h2 style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#888888", marginTop: "32px", marginBottom: "8px" }}>
            Changes
          </h2>
          <p style={{ marginTop: 0 }}>
            We may update these terms at any time. Continued subscription after changes are posted constitutes acceptance of the updated terms.
          </p>

          <h2 style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#888888", marginTop: "32px", marginBottom: "8px" }}>
            Contact
          </h2>
          <p style={{ marginTop: 0 }}>
            Questions? Email us at{" "}
            <a href="mailto:hello@theoperatingbrief.com" style={{ color: "#111111" }}>
              hello@theoperatingbrief.com
            </a>
            .
          </p>
        </div>

        <footer style={{ marginTop: "48px", borderTop: "2px solid #111111", paddingTop: "16px" }}>
          <p style={{ fontFamily: "Arial, sans-serif", fontSize: "12px", color: "#888888" }}>
            <a href="/privacy" style={{ color: "#888888", marginRight: "16px" }}>Privacy Policy</a>
            <a href="/terms" style={{ color: "#888888" }}>Terms of Use</a>
          </p>
        </footer>
      </div>
    </div>
  );
}

export default function Privacy() {
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
            Privacy Policy
          </h1>
          <p style={{ fontFamily: "Arial, sans-serif", fontSize: "12px", color: "#888888", marginTop: "10px" }}>
            Last updated: May 2026
          </p>
        </header>

        <div style={{ fontFamily: "Georgia, serif", fontSize: "15px", color: "#222222", lineHeight: 1.8 }}>
          <h2 style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#888888", marginTop: "32px", marginBottom: "8px" }}>
            What we collect
          </h2>
          <p style={{ marginTop: 0 }}>
            We collect your name (optional) and email address when you subscribe to The Operating Brief.
          </p>

          <h2 style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#888888", marginTop: "32px", marginBottom: "8px" }}>
            How we use it
          </h2>
          <p style={{ marginTop: 0 }}>
            Your information is used solely to send you your daily digest. We do not sell, share, or disclose your data to any third party, ever.
          </p>

          <h2 style={{ fontFamily: "Arial, sans-serif", fontSize: "11px", letterSpacing: "0.12em", textTransform: "uppercase", color: "#888888", marginTop: "32px", marginBottom: "8px" }}>
            Unsubscribing
          </h2>
          <p style={{ marginTop: 0 }}>
            You may unsubscribe at any time using the link at the bottom of any email. Your data will be permanently deleted within 30 days of unsubscribing.
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

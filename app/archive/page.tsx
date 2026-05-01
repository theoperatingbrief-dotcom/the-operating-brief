import { createClient } from "@supabase/supabase-js";
import Link from "next/link";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

type Edition = {
  id: number;
  slug: string;
  subject: string;
  sent_at: string;
  preview_text: string;
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-AU", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

export const revalidate = 60;

export default async function ArchivePage() {
  const { data: editions, error } = await supabase
    .from("editions")
    .select("id, slug, subject, sent_at, preview_text")
    .eq("published", true)
    .order("sent_at", { ascending: false });

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
              margin: "0",
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
              marginBottom: "0",
            }}
          >
            For Australian business operators
          </p>
        </header>

        {/* Archive heading */}
        <div style={{ marginBottom: "32px" }}>
          <h2
            style={{
              margin: "0 0 8px",
              fontFamily: "Arial, sans-serif",
              fontSize: "14px",
              fontWeight: 700,
              color: "#111111",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              borderLeft: "3px solid #111111",
              paddingLeft: "10px",
            }}
          >
            Past Editions
          </h2>
          <p
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: "13px",
              color: "#888888",
              marginLeft: "13px",
            }}
          >
            <Link
              href="/"
              style={{ color: "#888888", textDecoration: "none", borderBottom: "1px solid #cccccc" }}
            >
              ← Subscribe
            </Link>
          </p>
        </div>

        <div style={{ borderTop: "1px solid #dddddd", marginBottom: "24px" }} />

        {/* Edition list */}
        {error && (
          <p style={{ fontFamily: "Arial, sans-serif", fontSize: "14px", color: "#888888" }}>
            Could not load editions.
          </p>
        )}

        {!error && (!editions || editions.length === 0) && (
          <p style={{ fontFamily: "Arial, sans-serif", fontSize: "14px", color: "#888888" }}>
            No past editions yet.
          </p>
        )}

        {editions && editions.map((edition: Edition) => (
          <div key={edition.id}>
            <Link
              href={`/archive/${edition.slug}`}
              style={{ textDecoration: "none", display: "block" }}
            >
              <div
                style={{
                  padding: "20px 0",
                  borderBottom: "1px solid #eeeeee",
                  cursor: "pointer",
                }}
              >
                <p
                  style={{
                    margin: "0 0 4px",
                    fontFamily: "Arial, sans-serif",
                    fontSize: "11px",
                    color: "#888888",
                    textTransform: "uppercase",
                    letterSpacing: "0.12em",
                  }}
                >
                  {formatDate(edition.sent_at)}
                </p>
                <h3
                  style={{
                    margin: "0 0 6px",
                    fontFamily: "Georgia, serif",
                    fontSize: "18px",
                    fontWeight: 700,
                    color: "#111111",
                    lineHeight: 1.3,
                  }}
                >
                  {edition.subject}
                </h3>
                <p
                  style={{
                    margin: "0",
                    fontFamily: "Arial, sans-serif",
                    fontSize: "14px",
                    color: "#555555",
                    lineHeight: 1.5,
                  }}
                >
                  {edition.preview_text}
                </p>
              </div>
            </Link>
          </div>
        ))}

        {/* Footer */}
        <footer style={{ marginTop: "40px", borderTop: "2px solid #111111", paddingTop: "16px" }}>
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

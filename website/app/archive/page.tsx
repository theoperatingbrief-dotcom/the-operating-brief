import { createClient } from "@supabase/supabase-js";
import Link from "next/link";
import { EditorialShell } from "../components/EditorialShell";

export const dynamic = "force-dynamic";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

type Edition = {
  id: number;
  slug: string;
  subject: string;
  preview_text: string;
};

function formatDate(slug: string): string {
  // Slug is YYYY-MM-DD or YYYY-MM-DD-mode — parse the date portion only
  const datePart = slug.slice(0, 10);
  const [year, month, day] = datePart.split("-").map(Number);
  const d = new Date(Date.UTC(year, month - 1, day));
  return d.toLocaleDateString("en-AU", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

export const revalidate = 60;

export default async function ArchivePage() {
  const supabase = getSupabase();
  const { data: editions, error } = await supabase
    .from("editions")
    .select("id, slug, subject, preview_text")
    .eq("published", true)
    .order("sent_at", { ascending: false });

  return (
    <EditorialShell
      activeHref="/"
      eyebrow="Daily Briefing"
      title="The Operating Brief"
      subtitle="For Australian business operators"
      archiveHref="/"
      archiveLabel="← Subscribe"
      footerCopy="Your daily AI-powered business briefing — published weekday mornings."
    >
      <section className="content-stack">
        <h2 style={{ fontFamily: "Arial, sans-serif", fontSize: "14px", fontWeight: 700, color: "#111111", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Past Editions
        </h2>
        <div style={{ borderTop: "1px solid #dddddd", margin: "0" }} />

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

        {editions?.map((edition: Edition) => (
          <Link href={`/archive/${edition.slug}`} key={edition.id} style={{ textDecoration: "none", display: "block" }}>
            <article style={{ padding: "18px 0", borderBottom: "1px solid #eeeeee" }}>
              <p style={{ margin: "0 0 4px", fontFamily: "Arial, sans-serif", fontSize: "11px", color: "#888888", textTransform: "uppercase", letterSpacing: "0.12em" }}>
                {formatDate(edition.slug)}
              </p>
              <h3 style={{ margin: "0 0 6px", fontFamily: "Georgia, serif", fontSize: "18px", fontWeight: 700, color: "#111111", lineHeight: 1.3 }}>
                {edition.subject}
              </h3>
              <p style={{ margin: 0, fontFamily: "Arial, sans-serif", fontSize: "14px", color: "#555555", lineHeight: 1.5 }}>
                {edition.preview_text}
              </p>
            </article>
          </Link>
        ))}
      </section>
    </EditorialShell>
  );
}

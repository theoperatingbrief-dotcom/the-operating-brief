import { createClient } from "@supabase/supabase-js";
import Link from "next/link";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

export async function generateStaticParams() {
  return [];
}

type Props = {
  params: Promise<{ slug: string }>;
};

export default async function EditionPage({ params }: Props) {
  const supabase = getSupabase();
  const { slug } = await params;

  const { data: edition } = await supabase
    .from("editions")
    .select("slug, subject, sent_at, html")
    .eq("slug", slug)
    .eq("published", true)
    .maybeSingle();

  if (!edition) {
    notFound();
  }

  return (
    <div style={{ backgroundColor: "#f5f4f0", minHeight: "100vh" }}>
      {/* Masthead */}
      <div style={{ backgroundColor: "#f5f4f0", padding: "16px 16px 0" }}>
        <div style={{ maxWidth: "620px", margin: "0 auto" }}>
          <p
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: "12px",
              color: "#888888",
              margin: "0 0 8px",
            }}
          >
            <Link
              href="/archive"
              style={{
                color: "#888888",
                textDecoration: "none",
                borderBottom: "1px solid #cccccc",
              }}
            >
              ← All editions
            </Link>
          </p>
        </div>
      </div>

      {/* Edition HTML */}
      <div dangerouslySetInnerHTML={{ __html: edition.html }} />
    </div>
  );
}

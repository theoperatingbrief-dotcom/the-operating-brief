import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";

export const dynamic = "force-dynamic";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;
  if (token !== process.env.PREVIEW_TOKEN) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const supabase = getSupabase();
  const resend = new Resend(process.env.RESEND_API_KEY);

  const { data: draft } = await supabase
    .from("editions")
    .select("html, subject")
    .eq("slug", "draft")
    .single();

  if (!draft?.html) {
    return NextResponse.json({ error: "No draft found" }, { status: 404 });
  }

  const { data: subscribers } = await supabase
    .from("subscribers")
    .select("email, token")
    .eq("active", true);

  if (!subscribers?.length) {
    return NextResponse.json({ error: "No active subscribers" }, { status: 400 });
  }

  const now = new Date().toLocaleDateString("en-AU", {
    month: "long", day: "2-digit", year: "numeric", timeZone: "Australia/Sydney",
  });
  const subject = draft.subject || `The Operating Brief – ${now}`;
  const slug = new Date().toLocaleDateString("sv-SE", { timeZone: "Australia/Sydney" }); // YYYY-MM-DD

  const sent: string[] = [];
  const failed: string[] = [];

  for (const sub of subscribers) {
    const unsubUrl = `https://theoperatingbrief.com/unsubscribe?token=${sub.token}`;
    const html = draft.html
      .replace(
        'href="mailto:hello@theoperatingbrief.com?subject=Subscribe%20to%20The%20Operating%20Brief"',
        'href="https://theoperatingbrief.com"'
      )
      .replace(
        'href="mailto:hello@theoperatingbrief.com?subject=Unsubscribe%20from%20The%20Operating%20Brief"',
        `href="${unsubUrl}"`
      );

    try {
      await resend.emails.send({
        from: "The Operating Brief <hello@theoperatingbrief.com>",
        to: [sub.email],
        subject,
        html,
        replyTo: "hello@theoperatingbrief.com",
      });
      sent.push(sub.email);
    } catch {
      failed.push(sub.email);
    }

    await sleep(600); // stay under Resend 2 req/s limit
  }

  await supabase.from("editions").upsert(
    { slug, subject, html: draft.html, preview_text: "" },
    { onConflict: "slug" }
  );

  return NextResponse.json({ sent: sent.length, failed });
}

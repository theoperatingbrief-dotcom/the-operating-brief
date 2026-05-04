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

export async function POST(request: NextRequest) {
  const supabase = getSupabase();
  try {
    const body = await request.json();
    const { email } = body;

    if (!email || typeof email !== "string") {
      return NextResponse.json({ error: "Email is required." }, { status: 400 });
    }

    const normalizedEmail = email.toLowerCase().trim();

    const { data: existing } = await supabase
      .from("sports_subscribers")
      .select("id, active, token")
      .eq("email", normalizedEmail)
      .maybeSingle();

    let token: string;

    if (existing) {
      if (existing.active) {
        return NextResponse.json({ error: "Already subscribed." }, { status: 409 });
      }
      // Reactivate
      const { error } = await supabase
        .from("sports_subscribers")
        .update({ active: true })
        .eq("id", existing.id);
      if (error) {
        console.error("Supabase reactivate error:", error);
        return NextResponse.json({ error: "Failed to subscribe. Please try again." }, { status: 500 });
      }
      token = existing.token;
    } else {
      token = crypto.randomUUID();
      const { error } = await supabase.from("sports_subscribers").insert({
        email: normalizedEmail,
        active: true,
        token,
      });
      if (error) {
        if (error.code === "23505") {
          return NextResponse.json({ error: "Already subscribed." }, { status: 409 });
        }
        console.error("Supabase insert error:", error);
        return NextResponse.json({ error: "Failed to subscribe. Please try again." }, { status: 500 });
      }
    }

    // Welcome email
    try {
      const resend = new Resend(process.env.RESEND_API_KEY);
      await resend.emails.send({
        from: "The Sporting Brief <brief@theoperatingbrief.com>",
        to: normalizedEmail,
        replyTo: "hello@theoperatingbrief.com",
        subject: "You're in — The Sporting Brief",
        html: `
          <div style="max-width:620px;margin:0 auto;background:#ffffff;padding:48px;font-family:Arial,sans-serif;">
            <p style="font-size:11px;color:#888;letter-spacing:0.12em;text-transform:uppercase;margin:0 0 8px 0;">The Sporting Brief</p>
            <h1 style="font-family:Georgia,serif;font-size:28px;font-weight:700;color:#111;border-bottom:3px solid #111;padding-bottom:16px;margin:0 0 24px 0;">You're subscribed.</h1>
            <p style="font-family:Georgia,serif;font-size:16px;color:#222;line-height:1.75;margin:0 0 16px 0;">
              You're on the list. Every weekend, <em>The Sporting Brief</em> will land in your inbox with a sharp wrap of NRL, AFL, football, F1, NBA, golf, and more.
            </p>
            <p style="font-family:Georgia,serif;font-size:16px;color:#222;line-height:1.75;margin:0 0 32px 0;">All the scores. The big stories. See you this weekend.</p>
            <div style="border-top:2px solid #111;padding-top:16px;">
              <p style="font-size:12px;color:#888;margin:0;">
                You're receiving this because you subscribed at <a href="https://theoperatingbrief.com/sporting" style="color:#888;">theoperatingbrief.com/sporting</a>.
                Not you? <a href="https://theoperatingbrief.com/sporting/unsubscribe?token=${token}" style="color:#888;">Unsubscribe here</a>.
              </p>
            </div>
          </div>
        `,
      });
    } catch (emailErr) {
      console.error("Welcome email error:", emailErr);
    }

    return NextResponse.json({ message: "Subscribed successfully." }, { status: 200 });
  } catch (err) {
    console.error("Subscribe error:", err);
    return NextResponse.json({ error: "Internal server error." }, { status: 500 });
  }
}

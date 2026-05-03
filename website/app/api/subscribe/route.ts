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
    const { email, name } = body;

    if (!email || typeof email !== "string") {
      return NextResponse.json({ error: "Email is required." }, { status: 400 });
    }

    const normalizedEmail = email.toLowerCase().trim();

    // Check if already subscribed
    const { data: existing } = await supabase
      .from("subscribers")
      .select("id, active")
      .eq("email", normalizedEmail)
      .maybeSingle();

    if (existing) {
      return NextResponse.json({ error: "Already subscribed." }, { status: 409 });
    }

    // Insert new subscriber
    const { error } = await supabase.from("subscribers").insert({
      email: normalizedEmail,
      name: name?.trim() || null,
      active: true,
      token: crypto.randomUUID(),
    });

    if (error) {
      console.error("Supabase insert error:", error);
      return NextResponse.json({ error: "Failed to subscribe. Please try again." }, { status: 500 });
    }

    // Send welcome email
    try {
      const resend = new Resend(process.env.RESEND_API_KEY);
      const firstName = name?.trim().split(" ")[0] || null;
      await resend.emails.send({
        from: "The Operating Brief <brief@theoperatingbrief.com>",
        to: normalizedEmail,
        replyTo: "hello@theoperatingbrief.com",
        subject: "You're in — The Operating Brief",
        html: `
          <div style="max-width:620px;margin:0 auto;background:#ffffff;padding:48px;font-family:Arial,sans-serif;">
            <p style="font-size:11px;color:#888;letter-spacing:0.12em;text-transform:uppercase;margin:0 0 8px 0;">The Operating Brief</p>
            <h1 style="font-family:Georgia,serif;font-size:28px;font-weight:700;color:#111;border-bottom:3px solid #111;padding-bottom:16px;margin:0 0 24px 0;">You're subscribed.</h1>
            <p style="font-family:Georgia,serif;font-size:16px;color:#222;line-height:1.75;margin:0 0 16px 0;">
              ${firstName ? `${firstName}, you're` : "You're"} on the list. Every weekday morning, <em>The Operating Brief</em> will land in your inbox before 7 am with a sharp, AI-powered summary of the business and technology stories that matter to Australian operators.
            </p>
            <p style="font-family:Georgia,serif;font-size:16px;color:#222;line-height:1.75;margin:0 0 32px 0;">No noise. No filler. See you tomorrow morning.</p>
            <div style="border-top:2px solid #111;padding-top:16px;">
              <p style="font-size:12px;color:#888;margin:0;">
                You're receiving this because you subscribed at <a href="https://theoperatingbrief.com" style="color:#888;">theoperatingbrief.com</a>.
                Not you? <a href="https://theoperatingbrief.com/unsubscribe" style="color:#888;">Unsubscribe here</a>.
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

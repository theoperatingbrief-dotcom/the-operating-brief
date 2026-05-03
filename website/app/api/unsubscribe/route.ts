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

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token");
  return handleUnsubscribe(token);
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    return handleUnsubscribe(body.token);
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }
}

async function handleUnsubscribe(token: string | null) {
  const supabase = getSupabase();
  if (!token || typeof token !== "string") {
    return NextResponse.json({ error: "Token is required." }, { status: 400 });
  }

  const { data, error } = await supabase
    .from("subscribers")
    .update({ active: false })
    .eq("token", token)
    .select("id")
    .maybeSingle();

  if (error) {
    console.error("Supabase unsubscribe error:", error);
    return NextResponse.json({ error: "Failed to unsubscribe. Please try again." }, { status: 500 });
  }

  if (!data) {
    return NextResponse.json({ error: "Token not found." }, { status: 404 });
  }

  // Fetch email to send confirmation
  const { data: subscriber } = await supabase
    .from("subscribers")
    .select("email")
    .eq("token", token)
    .maybeSingle();

  if (subscriber?.email) {
    try {
      const resend = new Resend(process.env.RESEND_API_KEY);
      await resend.emails.send({
        from: "The Operating Brief <brief@theoperatingbrief.com>",
        to: subscriber.email,
        replyTo: "hello@theoperatingbrief.com",
        subject: "You've been unsubscribed — The Operating Brief",
        html: `
          <div style="max-width:620px;margin:0 auto;background:#ffffff;padding:48px;font-family:Arial,sans-serif;">
            <p style="font-size:11px;color:#888;letter-spacing:0.12em;text-transform:uppercase;margin:0 0 8px 0;">The Operating Brief</p>
            <h1 style="font-family:Georgia,serif;font-size:28px;font-weight:700;color:#111;border-bottom:3px solid #111;padding-bottom:16px;margin:0 0 24px 0;">You're unsubscribed.</h1>
            <p style="font-family:Georgia,serif;font-size:16px;color:#222;line-height:1.75;margin:0 0 16px 0;">
              You've been removed from The Operating Brief. You won't receive any further emails from us.
            </p>
            <p style="font-family:Georgia,serif;font-size:16px;color:#222;line-height:1.75;margin:0 0 32px 0;">
              Changed your mind? You can always <a href="https://theoperatingbrief.com" style="color:#111;">resubscribe here</a>.
            </p>
            <div style="border-top:2px solid #111;padding-top:16px;">
              <p style="font-size:12px;color:#888;margin:0;">
                Questions? Reply to this email or contact us at <a href="mailto:hello@theoperatingbrief.com" style="color:#888;">hello@theoperatingbrief.com</a>.
              </p>
            </div>
          </div>
        `,
      });
    } catch (emailErr) {
      console.error("Unsubscribe confirmation email error:", emailErr);
    }
  }

  return NextResponse.json({ message: "Unsubscribed successfully." }, { status: 200 });
}

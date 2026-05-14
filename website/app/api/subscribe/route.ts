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
    const { email, name, ref } = body;

    if (!email || typeof email !== "string") {
      return NextResponse.json({ error: "Email is required." }, { status: 400 });
    }

    const normalizedEmail = email.toLowerCase().trim();

    // Validate referral code if provided
    let referrerId: string | null = null;
    if (ref && typeof ref === "string") {
      const { data: referrer } = await supabase
        .from("subscribers")
        .select("id")
        .eq("referral_code", ref)
        .eq("active", true)
        .maybeSingle();
      if (referrer) referrerId = referrer.id;
    }

    // Check if email already exists
    const { data: existing } = await supabase
      .from("subscribers")
      .select("id, active, referral_code")
      .eq("email", normalizedEmail)
      .maybeSingle();

    let subNumber: number | null = null;
    let referralCode: string | null = null;

    if (existing) {
      if (existing.active) {
        return NextResponse.json({ error: "Already subscribed." }, { status: 409 });
      }
      // Reactivate previously unsubscribed user
      const reactivatePayload: Record<string, unknown> = { active: true, name: name?.trim() || null };
      if (!existing.referral_code) {
        reactivatePayload.referral_code = Math.random().toString(36).slice(2, 10);
      }
      const { data: reactivated, error } = await supabase
        .from("subscribers")
        .update(reactivatePayload)
        .eq("id", existing.id)
        .select("sub_number, referral_code")
        .single();
      if (error) {
        console.error("Supabase reactivate error:", error);
        return NextResponse.json({ error: "Failed to subscribe. Please try again." }, { status: 500 });
      }
      subNumber = reactivated?.sub_number ?? null;
      referralCode = reactivated?.referral_code ?? null;
    } else {
      const newReferralCode = Math.random().toString(36).slice(2, 10);
      // Insert new subscriber
      const { data: inserted, error } = await supabase.from("subscribers").insert({
        email: normalizedEmail,
        name: name?.trim() || null,
        active: true,
        token: crypto.randomUUID(),
        referral_code: newReferralCode,
        referred_by: ref && referrerId ? ref : null,
      }).select("sub_number, referral_code").single();
      if (error) {
        if (error.code === "23505") {
          return NextResponse.json({ error: "Already subscribed." }, { status: 409 });
        }
        console.error("Supabase insert error:", error);
        return NextResponse.json({ error: "Failed to subscribe. Please try again." }, { status: 500 });
      }
      subNumber = inserted?.sub_number ?? null;
      referralCode = inserted?.referral_code ?? null;

      // Credit the referrer
      if (referrerId) {
        await supabase.rpc("increment_referral_count", { subscriber_id: referrerId });
      }
    }

    const referralUrl = referralCode
      ? `https://theoperatingbrief.com/?ref=${referralCode}`
      : null;

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
            ${referralUrl ? `
            <div style="background:#f5f4f0;padding:24px;margin:0 0 32px 0;">
              <p style="font-family:Arial,sans-serif;font-size:11px;color:#888;letter-spacing:0.12em;text-transform:uppercase;margin:0 0 8px 0;">Your referral link</p>
              <p style="font-family:Georgia,serif;font-size:15px;color:#222;line-height:1.6;margin:0 0 12px 0;">Know someone who'd find this useful? Share your link — every subscriber you refer counts toward a reward.</p>
              <a href="${referralUrl}" style="font-family:Arial,sans-serif;font-size:13px;color:#111;word-break:break-all;">${referralUrl}</a>
            </div>
            ` : ""}
            <div style="border-top:2px solid #111;padding-top:16px;">
              <p style="font-size:12px;color:#888;margin:0 0 4px 0;">
                You're receiving this because you subscribed at <a href="https://theoperatingbrief.com" style="color:#888;">theoperatingbrief.com</a>.
                Not you? <a href="https://theoperatingbrief.com/unsubscribe" style="color:#888;">Unsubscribe here</a>.
              </p>
              ${subNumber ? `<p style="font-size:11px;color:#aaa;margin:0;">Subscriber #${subNumber}</p>` : ""}
            </div>
          </div>
        `,
      });
    } catch (emailErr) {
      console.error("Welcome email error:", emailErr);
    }

    return NextResponse.json({ message: "Subscribed successfully.", referralUrl }, { status: 200 });
  } catch (err) {
    console.error("Subscribe error:", err);
    return NextResponse.json({ error: "Internal server error." }, { status: 500 });
  }
}

import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

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
    .from("markets_subscribers")
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

  return NextResponse.json({ message: "Unsubscribed successfully." }, { status: 200 });
}

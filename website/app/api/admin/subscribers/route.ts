import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { getAdminSecret } from "../auth";

export const dynamic = "force-dynamic";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

export async function GET(request: NextRequest) {
  const adminPassword = getAdminSecret();
  const authCookie = request.cookies.get("admin_auth")?.value;
  if (!adminPassword || authCookie !== adminPassword) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const supabase = getSupabase();

  const [brief, markets, sports, paddock] = await Promise.all([
    supabase.from("subscribers").select("id", { count: "exact", head: true }).eq("active", true),
    supabase.from("markets_subscribers").select("id", { count: "exact", head: true }).eq("active", true),
    supabase.from("sports_subscribers").select("id", { count: "exact", head: true }).eq("active", true),
    supabase.from("paddock_subscribers").select("id", { count: "exact", head: true }).eq("active", true),
  ]);

  return NextResponse.json({
    brief: brief.count ?? 0,
    markets: markets.count ?? 0,
    sports: sports.count ?? 0,
    paddock: paddock.count ?? 0,
  });
}

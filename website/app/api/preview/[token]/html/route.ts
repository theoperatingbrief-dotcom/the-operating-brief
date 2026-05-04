import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

function getSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;
  if (token !== process.env.PREVIEW_TOKEN) {
    return new NextResponse("Not found", { status: 404 });
  }

  const supabase = getSupabase();
  const { data, error } = await supabase
    .from("editions")
    .select("html")
    .eq("slug", "draft")
    .single();

  if (error || !data?.html) {
    return new NextResponse("No draft found — run python3 daily_digest.py --preview first.", {
      status: 404,
      headers: { "Content-Type": "text/plain" },
    });
  }

  return new NextResponse(data.html, {
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

import { NextRequest, NextResponse } from "next/server";
import { dispatchDigestWorkflow } from "@/lib/githubActions";

export const dynamic = "force-dynamic";

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;
  if (token !== process.env.PREVIEW_TOKEN) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const { ok, status, text } = await dispatchDigestWorkflow("daily_digest.py", "--preview");

  if (!ok) {
    return NextResponse.json({ error: `GitHub API error: ${text}` }, { status: status || 500 });
  }

  return NextResponse.json({ ok: true });
}

import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;
  if (token !== process.env.PREVIEW_TOKEN) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const ghToken = process.env.GITHUB_PAT;
  const repo = "theoperatingbrief-dotcom/the-operating-brief";

  if (!ghToken) {
    return NextResponse.json({ error: "GITHUB_PAT not configured" }, { status: 500 });
  }

  const res = await fetch(
    `https://api.github.com/repos/${repo}/actions/workflows/generate-digest.yml/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${ghToken}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "main" }),
    }
  );

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: `GitHub API error: ${text}` }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}

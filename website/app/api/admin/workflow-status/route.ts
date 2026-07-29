import { NextRequest, NextResponse } from "next/server";
import { getAdminSecret } from "../auth";
import { fetchLatestDigestWorkflowRun } from "@/lib/githubActions";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const adminPassword = getAdminSecret();
  const authCookie = request.cookies.get("admin_auth")?.value;
  if (!adminPassword || authCookie !== adminPassword) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const action = request.nextUrl.searchParams.get("action");
  if (action !== "brief-preview") {
    return NextResponse.json({ error: "Unsupported action" }, { status: 400 });
  }

  const since = request.nextUrl.searchParams.get("since") ?? undefined;
  const result = await fetchLatestDigestWorkflowRun(since);

  if (!result.ok) {
    return NextResponse.json(
      { error: result.text || `HTTP ${result.status}` },
      { status: result.status }
    );
  }

  if (!result.run) {
    return NextResponse.json({
      state: "pending",
      message: "Waiting for GitHub Actions to start…",
      run: null,
    });
  }

  const { run } = result;
  const state =
    run.status === "completed"
      ? (run.conclusion === "success" ? "completed" : "failed")
      : run.status;

  return NextResponse.json({
    state,
    message:
      state === "completed"
        ? "Preview finished successfully."
        : state === "failed"
          ? `Preview failed (${run.conclusion ?? "unknown"}).`
          : `Preview is ${run.status.replace("_", " ")}…`,
    run,
  });
}

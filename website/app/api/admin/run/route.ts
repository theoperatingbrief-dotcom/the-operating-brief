import { NextRequest } from "next/server";
import { spawn } from "child_process";
import { existsSync } from "fs";
import path from "path";
import { getAdminSecret } from "../auth";
import { dispatchDigestWorkflow, type DigestFlag, type DigestScript } from "@/lib/githubActions";

export const dynamic = "force-dynamic";

// Map action keys to script file + CLI flag
const SCRIPTS: Record<string, { file: DigestScript; flag: DigestFlag }> = {
  "brief-preview":   { file: "daily_digest.py",   flag: "--preview" },
  "brief-send":      { file: "daily_digest.py",   flag: "--send" },
  "markets-preview": { file: "markets_digest.py", flag: "--preview" },
  "markets-send":    { file: "markets_digest.py", flag: "--send" },
  "sports-ingest":   { file: "sports_digest.py",  flag: "--ingest" },
  "sports-preview":  { file: "sports_digest.py",  flag: "--preview" },
  "sports-send":     { file: "sports_digest.py",  flag: "--send" },
  "paddock-preview": { file: "paddock_digest.py", flag: "--preview" },
  "paddock-send":    { file: "paddock_digest.py", flag: "--send" },
};

const VERCEL_WORKFLOW_ACTIONS = new Set([
  "brief-preview",
  "markets-preview",
  "sports-ingest",
  "sports-preview",
  "paddock-preview",
]);

export async function GET(request: NextRequest) {
  // Auth check
  const adminPassword = getAdminSecret();
  const authCookie = request.cookies.get("admin_auth")?.value;
  if (!adminPassword || authCookie !== adminPassword) {
    return new Response("Unauthorized", { status: 401 });
  }

  const action = request.nextUrl.searchParams.get("action");
  if (!action || !SCRIPTS[action]) {
    return new Response("Invalid action", { status: 400 });
  }

  const { file, flag } = SCRIPTS[action];
  const isVercel = !!process.env.VERCEL;

  // Project root is one level above the website directory
  const projectRoot = path.resolve(process.cwd(), "..");
  const pythonPath = path.join(projectRoot, ".venv", "bin", "python");
  const pythonRunner = existsSync(pythonPath) ? pythonPath : "python3";

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const send = (type: string, text: string, extra: Record<string, unknown> = {}) => {
        const line = `data: ${JSON.stringify({ type, text, ...extra })}\n\n`;
        controller.enqueue(encoder.encode(line));
      };

      if (isVercel && VERCEL_WORKFLOW_ACTIONS.has(action)) {
        const dispatchedAt = new Date().toISOString();
        send("start", `Dispatching ${file} ${flag} to GitHub Actions…`);

        dispatchDigestWorkflow(file, flag)
          .then(({ ok, status, text }) => {
            if (!ok) {
              send("err", `GitHub API error: ${text || `HTTP ${status}`}`);
              return;
            }

            send("done", `${file} ${flag} dispatched. Check GitHub Actions and refresh the preview page shortly.`, {
              startedAt: dispatchedAt,
            });
          })
          .catch((err: Error) => {
            send("err", err.message);
          })
          .finally(() => {
            controller.close();
          });

        return;
      }

      if (isVercel) {
        send("err", "This action still requires the local Python generator and is not available from the website deployment yet.");
        controller.close();
        return;
      }

      send("start", `Running: ${file} ${flag}`);

      const proc = spawn(pythonRunner, [file, flag], {
        cwd: projectRoot,
        env: { ...process.env, PYTHONUNBUFFERED: "1" },
        // stdin must be non-interactive so scripts don't pause waiting for input
        stdio: ["ignore", "pipe", "pipe"],
      });

      proc.stdout.on("data", (data: Buffer) => {
        send("log", data.toString());
      });

      proc.stderr.on("data", (data: Buffer) => {
        send("err", data.toString());
      });

      proc.on("close", (code: number | null) => {
        send("done", `Exited with code ${code ?? "?"}`);
        controller.close();
      });

      proc.on("error", (err: Error) => {
        send("err", `Failed to start process: ${err.message}`);
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}

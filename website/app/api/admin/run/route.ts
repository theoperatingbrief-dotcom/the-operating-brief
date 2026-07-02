import { NextRequest } from "next/server";
import { spawn } from "child_process";
import path from "path";
import { getAdminSecret } from "../auth";

export const dynamic = "force-dynamic";

// Map action keys to script file + CLI flag
const SCRIPTS: Record<string, { file: string; flag: string }> = {
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

  // Project root is one level above the website directory
  const projectRoot = path.resolve(process.cwd(), "..");
  const pythonPath = path.join(projectRoot, ".venv", "bin", "python");

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const send = (type: string, text: string) => {
        const line = `data: ${JSON.stringify({ type, text })}\n\n`;
        controller.enqueue(encoder.encode(line));
      };

      send("start", `Running: ${file} ${flag}`);

      const proc = spawn(pythonPath, [file, flag], {
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

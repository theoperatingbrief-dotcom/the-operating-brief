const REPO = "theoperatingbrief-dotcom/the-operating-brief";
const WORKFLOW = "generate-digest.yml";

export type DigestScript =
  | "daily_digest.py"
  | "markets_digest.py"
  | "sports_digest.py"
  | "paddock_digest.py";

export type DigestFlag = "--preview" | "--send" | "--ingest";

export interface WorkflowRun {
  id: number;
  status: "queued" | "in_progress" | "completed" | string;
  conclusion: string | null;
  created_at: string;
  updated_at: string;
  html_url: string;
  display_title: string;
  head_branch: string;
  event: string;
}

export async function dispatchDigestWorkflow(script: DigestScript, flag: DigestFlag) {
  const token = process.env.GITHUB_PAT;
  if (!token) {
    return {
      ok: false,
      status: 500,
      text: "GITHUB_PAT not configured",
    };
  }

  const res = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ref: "main",
        inputs: {
          script,
          flag,
        },
      }),
    }
  );

  return {
    ok: res.ok,
    status: res.status,
    text: await res.text(),
  };
}

export async function fetchLatestDigestWorkflowRun(since?: string) {
  const token = process.env.GITHUB_PAT;
  if (!token) {
    return {
      ok: false,
      status: 500,
      text: "GITHUB_PAT not configured",
      run: null as WorkflowRun | null,
    };
  }

  const res = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/runs?branch=main&event=workflow_dispatch&per_page=10`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
      },
    }
  );

  if (!res.ok) {
    return {
      ok: false,
      status: res.status,
      text: await res.text(),
      run: null as WorkflowRun | null,
    };
  }

  const body = await res.json() as { workflow_runs?: WorkflowRun[] };
  const sinceMs = since ? new Date(since).getTime() : 0;
  const run = (body.workflow_runs ?? []).find((candidate) => {
    if (!sinceMs) return true;
    return new Date(candidate.created_at).getTime() >= sinceMs;
  }) ?? null;

  return {
    ok: true,
    status: res.status,
    text: "",
    run,
  };
}

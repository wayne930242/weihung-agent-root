const REPO = "wayne930242/weihung-user-claude";
const API = "https://api.github.com";

export class GitHubError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "GitHubError";
  }
}

function headers(): HeadersInit {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    throw new GitHubError("GITHUB_TOKEN 未設定", 500);
  }
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

async function request(path: string, init?: RequestInit): Promise<unknown> {
  const res = await fetch(`${API}/repos/${REPO}/contents/${path}`, {
    ...init,
    headers: { ...headers(), ...init?.headers },
    // The whole point of the console is to reflect what the repo says right now.
    cache: "no-store",
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new GitHubError(
      `GitHub API ${res.status} on ${path}: ${detail.slice(0, 300)}`,
      res.status,
    );
  }

  return res.json();
}

export type RepoFile = { path: string; text: string; sha: string };

export async function readFile(path: string): Promise<RepoFile> {
  const body = (await request(path)) as {
    content: string;
    encoding: string;
    sha: string;
  };

  if (body.encoding !== "base64") {
    throw new GitHubError(`${path} 的編碼非 base64：${body.encoding}`, 500);
  }

  return {
    path,
    text: Buffer.from(body.content, "base64").toString("utf-8"),
    sha: body.sha,
  };
}

export async function listMarkdown(dir: string): Promise<string[]> {
  const body = (await request(dir)) as { name: string; type: string }[];

  return body
    .filter((entry) => entry.type === "file" && entry.name.endsWith(".md"))
    .map((entry) => entry.name.replace(/\.md$/, ""))
    .sort();
}

export async function commitFile(
  file: RepoFile,
  message: string,
): Promise<void> {
  await request(file.path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      content: Buffer.from(file.text, "utf-8").toString("base64"),
      // Passing the sha we read makes a concurrent local push a 409 rather than
      // a silent overwrite.
      sha: file.sha,
    }),
  });
}

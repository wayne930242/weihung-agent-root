// Per-session state directory + files. See open-gui-session spec.

export function projectSlug(cwd: string): string {
  const base = cwd.replace(/[/\\]+$/, "").split(/[/\\]/).pop() ?? "project";
  return base.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "project";
}

// HOME is unset on Windows by default (USERPROFILE is the equivalent).
function homeDir(): string {
  return Deno.env.get("HOME") ?? Deno.env.get("USERPROFILE") ?? "/tmp";
}

export function stateDir(cwd: string, sessionId: string): string {
  return `${homeDir()}/.claude/state/${projectSlug(cwd)}/open-gui/${sessionId}`;
}

// Best-effort read of Claude Code's own light/dark preference (design.md D7
// revision: open-gui follows it instead of a fixed theme). `settings.json`'s
// `theme` value isn't a small closed enum across Claude Code versions, so
// match on substring rather than an exact list — anything naming "light"
// is light, everything else (including missing/unreadable settings) is dark,
// matching this tool's original fixed-dark look as the safe fallback.
export async function readThemeMode(): Promise<"light" | "dark"> {
  try {
    const text = await Deno.readTextFile(`${homeDir()}/.claude/settings.json`);
    const settings = JSON.parse(text) as { theme?: unknown };
    if (typeof settings.theme === "string" && /light/i.test(settings.theme)) {
      return "light";
    }
  } catch {
    // missing file, unreadable, or invalid JSON — fall through to dark
  }
  return "dark";
}

export async function ensureStateDir(dir: string): Promise<void> {
  await Deno.mkdir(dir, { recursive: true });
}

export function treeJsonPath(dir: string): string {
  return `${dir}/TREE.json`;
}

export function seedPromptPath(dir: string): string {
  return `${dir}/seed-prompt.txt`;
}

export function sessionRecordPath(dir: string): string {
  return `${dir}/session.json`;
}

export interface SessionRecord {
  pid: number;
  port: number;
  url: string;
  // The spawned `claude` process's own --session-id, when a real `claude`
  // binary was spawned (null for test stand-ins). Resumable from a normal
  // terminal via `claude --resume <claudeSessionId>` once this open-gui
  // session's backend is stopped — see open-gui/SKILL.md.
  claudeSessionId: string | null;
}

export async function writeSessionRecord(dir: string, record: SessionRecord): Promise<void> {
  await Deno.writeTextFile(sessionRecordPath(dir), JSON.stringify(record, null, 2) + "\n");
}

export interface TreeNode {
  id: string;
  type: "decision" | "question" | "artifact" | "info";
  parent: string | null;
  title: string;
  [key: string]: unknown;
}

export interface TreeDoc {
  topic: string;
  status: "in_progress" | "complete";
  nodes: TreeNode[];
}

export function defaultTree(topic: string): TreeDoc {
  return { topic, status: "in_progress", nodes: [] };
}

export async function readTree(dir: string): Promise<TreeDoc> {
  try {
    const text = await Deno.readTextFile(treeJsonPath(dir));
    return JSON.parse(text) as TreeDoc;
  } catch (err) {
    if (err instanceof Deno.errors.NotFound) {
      return defaultTree("");
    }
    throw err;
  }
}

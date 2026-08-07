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

// The one narrow, program-driven exception to "Claude is the sole author of
// TREE.json" (design.md D4/D12): a mechanical status flip for the
// reconsider action, safe because it's a single well-defined field on one
// node, not content authoring — the cascade reasoning still goes to Claude
// as a follow-up message, this only unblocks the UI instantly. Read-modify-
// write, not locked against a concurrent write from Claude's own process;
// accepted as a rare, low-stakes race (worst case: the flip is silently
// overwritten by Claude's own concurrent write, and the user just clicks
// reconsider again) rather than building real cross-process file locking
// for it. Writes via temp-file-then-rename, matching the atomic-write
// convention `main.ts`'s `Deno.watchFs` handling already expects.
export async function patchNodeStatus(
  dir: string,
  nodeId: string,
  status: string,
): Promise<boolean> {
  const tree = await readTree(dir);
  const node = tree.nodes.find((n) => n.id === nodeId);
  if (!node) return false;
  node.status = status;
  const path = treeJsonPath(dir);
  const tmpPath = `${path}.tmp-${crypto.randomUUID()}`;
  await Deno.writeTextFile(tmpPath, JSON.stringify(tree, null, 2) + "\n");
  await Deno.rename(tmpPath, path);
  return true;
}

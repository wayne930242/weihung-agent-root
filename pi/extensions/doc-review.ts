/**
 * Review pane for documents the agent wants the user to read, inside Herdr.
 *
 * `show_doc` opens files in one editable nvim per session, split to the right of the agent's
 * pane, with the documents stacked as rows. When the agent writes a Mini SDD
 * `docs/specs/<slug>/spec.md` whose header says `Status: proposed`, the folder's phase files
 * (decision, spec, design, verification) open the same way without a tool call, and a phase file
 * written later in a folder already on screen joins as a new row. Agent edits reload in place.
 *
 * Nothing waits for the user: the tool returns once the pane is open. When the user saves a shown
 * document, the diff from the version the agent last saw goes to the agent as review feedback,
 * steered into a running turn or attached to the user's next message when idle, so a save never
 * starts a turn by itself.
 */

import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI, type ExtensionContext } from "@earendil-works/pi-coding-agent";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, realpathSync, rmSync, unwatchFile, watchFile, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, relative, resolve } from "node:path";

export const MINI_SDD_FILE = /(^|\/)docs\/specs\/[^/]+\/(decision|spec|design|verification)\.md$/;
export const MINI_SDD_PHASES = ["decision.md", "spec.md", "design.md", "verification.md"];
export const PROPOSED_STATUS = /^Status:\s*proposed\b/m;
export const MAX_DIFF_CHARS = 20_000;
const MESSAGE_TYPE = "doc-review";
const SOCKET_WAIT_MS = 5000;
const SOCKET_POLL_MS = 100;
const CHECKTIME = 'execute("silent! checktime")';

export interface RunResult {
  status: number | null;
  stdout: string;
  stderr: string;
}

export interface DocReviewDeps {
  paneId: string | undefined;
  herdr: string;
  run: (command: string, args: string[]) => RunResult;
  makeDir: () => string;
  removeDir: (dir: string) => void;
  readFile: (path: string) => string | undefined;
  writeFile: (path: string, content: string) => void;
  realpath: (path: string) => string;
  watch: (path: string, onChange: () => void) => () => void;
  sleep: (ms: number) => Promise<void>;
}

const defaultDeps: DocReviewDeps = {
  paneId: process.env.HERDR_PANE_ID,
  herdr: process.env.HERDR_BIN_PATH ?? "herdr",
  run: (command, args) => {
    const result = spawnSync(command, args, { encoding: "utf8", timeout: 5000 });
    return { status: result.status, stdout: result.stdout ?? "", stderr: result.stderr ?? String(result.error ?? "") };
  },
  makeDir: () => mkdtempSync(join(tmpdir(), "pi-doc-review-")),
  removeDir: (dir) => rmSync(dir, { recursive: true, force: true }),
  readFile: (path) => {
    try {
      return readFileSync(path, "utf8");
    } catch {
      return undefined;
    }
  },
  writeFile: (path, content) => writeFileSync(path, content),
  realpath: (path) => (existsSync(path) ? realpathSync(path) : path),
  watch: (path, onChange) => {
    const listener = (): void => onChange();
    watchFile(path, { interval: 500 }, listener);
    return () => unwatchFile(path, listener);
  },
  sleep: (ms) => new Promise((done) => setTimeout(done, ms)),
};

interface Viewer {
  pane: string;
  dir: string;
  socket: string;
  log: string;
  logOffset: number;
  stopWatch: () => void;
}

interface ShownDoc {
  display: string;
  snapshot: string;
}

export interface ShowResult {
  opened: string[];
  text: string;
}

function shellQuote(value: string): string {
  return `'${value.replace(/'/g, `'\\''`)}'`;
}

function vimString(value: string): string {
  return `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

function vimLiteral(value: string): string {
  return `'${value.replace(/'/g, "''")}'`;
}

/** Opens `path` as a new bottom row unless a window already shows it, then evens out the rows. */
function addRowExpr(path: string): string {
  const name = vimString(path);
  return `bufwinnr(bufnr(${name})) < 0 ? execute("silent! botright split " .. fnameescape(${name}) .. " | wincmd =") : ""`;
}

function reviewScript(log: string): string {
  return [
    "set autoread",
    "augroup pi_doc_review",
    "  autocmd!",
    "  autocmd FocusGained,BufEnter * silent! checktime",
    `  autocmd BufWritePost * call writefile([expand('<afile>:p')], ${vimLiteral(log)}, 'a')`,
    "augroup END",
    "",
  ].join("\n");
}

function feedbackMessage(display: string, diff: string): string {
  const body = diff.length > MAX_DIFF_CHARS ? `${diff.slice(0, MAX_DIFF_CHARS)}\n… (diff truncated; read ${display} for the rest)\n` : diff;
  return (
    `The user edited ${display} in the review pane. Diff from the version you last saw:\n\n\`\`\`diff\n${body}\`\`\`\n\n` +
    "Treat these edits as review feedback. The file on disk holds them; build on it instead of restoring your earlier text."
  );
}

export function createDocReview(pi: ExtensionAPI, deps: DocReviewDeps = defaultDeps) {
  let viewer: Viewer | undefined;
  let ctx: ExtensionContext | undefined;
  const shown = new Map<string, ShownDoc>();

  const nvim = (socket: string, ...args: string[]): RunResult => deps.run("nvim", ["--server", socket, ...args]);
  const alive = (socket: string): boolean => nvim(socket, "--remote-expr", "1").status === 0;
  const viewerAlive = (): boolean => viewer !== undefined && alive(viewer.socket);
  const reload = (): void => {
    if (viewer && viewerAlive()) nvim(viewer.socket, "--remote-expr", CHECKTIME);
  };

  const herdr = (...args: string[]): RunResult => {
    const result = deps.run(deps.herdr, args);
    if (result.status !== 0) throw new Error(`herdr ${args.slice(0, 2).join(" ")} failed: ${(result.stderr || result.stdout).trim()}`);
    return result;
  };

  const deliver = (text: string, display: string): void => {
    const message = { customType: MESSAGE_TYPE, content: text, display: true };
    if (ctx && !ctx.isIdle()) {
      pi.sendMessage(message, { deliverAs: "steer" });
      return;
    }
    pi.sendMessage(message, { deliverAs: "nextTurn" });
    if (ctx?.hasUI) ctx.ui.notify(`Your edits to ${display} go to the agent with your next message.`, "info");
  };

  const onSave = (path: string, dir: string): void => {
    const doc = shown.get(path);
    if (!doc) return;
    const content = deps.readFile(path);
    if (content === undefined || content === doc.snapshot) return;
    const scratch = join(dir, "before");
    deps.writeFile(scratch, doc.snapshot);
    const diff = deps.run("diff", ["-u", "--label", `a/${doc.display}`, "--label", `b/${doc.display}`, scratch, path]);
    if (diff.status !== 0 && diff.status !== 1) throw new Error(`diff failed: ${diff.stderr.trim()}`);
    doc.snapshot = content;
    deliver(feedbackMessage(doc.display, diff.stdout), doc.display);
  };

  const readSaves = (): void => {
    if (!viewer) return;
    const { dir } = viewer;
    const log = deps.readFile(viewer.log) ?? "";
    const fresh = log.slice(viewer.logOffset);
    viewer.logOffset = log.length;
    for (const path of new Set(fresh.split("\n").filter(Boolean).map(deps.realpath))) {
      try {
        onSave(path, dir);
      } catch (error) {
        if (ctx?.hasUI) ctx.ui.notify(`doc-review: ${(error as Error).message}`, "error");
      }
    }
  };

  const closeViewer = (): void => {
    const current = viewer;
    viewer = undefined;
    shown.clear();
    if (!current) return;
    current.stopWatch();
    if (!alive(current.socket)) {
      deps.removeDir(current.dir);
      return;
    }
    // A buffer with unsaved edits keeps nvim, its socket, and its save log open for the user.
    const unsaved = nvim(current.socket, "--remote-expr", "len(filter(getbufinfo({'buflisted': 1}), 'v:val.changed'))");
    if (unsaved.stdout.trim() !== "0") return;
    nvim(current.socket, "--remote-send", "<C-\\><C-N>:qa<CR>");
    deps.removeDir(current.dir);
  };

  const launch = async (cwd: string, paths: string[]): Promise<void> => {
    closeViewer();
    const split = herdr("pane", "split", deps.paneId as string, "--direction", "right", "--no-focus", "--cwd", cwd);
    const pane = (JSON.parse(split.stdout) as { result?: { pane?: { pane_id?: string } } }).result?.pane?.pane_id;
    if (!pane) throw new Error(`herdr pane split returned no pane id: ${split.stdout.trim()}`);
    const dir = deps.makeDir();
    const socket = join(dir, "nvim.sock");
    const log = join(dir, "saves.log");
    const script = join(dir, "review.vim");
    deps.writeFile(log, "");
    deps.writeFile(script, reviewScript(log));
    viewer = { pane, dir, socket, log, logOffset: 0, stopWatch: deps.watch(log, readSaves) };
    // `exit` closes the pane when the user quits nvim; the next show opens a fresh one.
    herdr("pane", "run", pane, `nvim --listen ${shellQuote(socket)} -S ${shellQuote(script)} -o -- ${paths.map(shellQuote).join(" ")}; exit`);
    herdr("pane", "rename", pane, "doc review");
    for (let waited = 0; !alive(socket); waited += SOCKET_POLL_MS) {
      if (waited >= SOCKET_WAIT_MS) throw new Error(`nvim in pane ${pane} did not open its socket within ${SOCKET_WAIT_MS} ms`);
      await deps.sleep(SOCKET_POLL_MS);
    }
  };

  const show = async (cwd: string, paths: string[], reason: string): Promise<ShowResult> => {
    const docs = paths.map((path) => {
      const absolute = deps.realpath(isAbsolute(path) ? path : resolve(cwd, path));
      const content = deps.readFile(absolute);
      if (content === undefined) throw new Error(`cannot read ${path}`);
      const rel = relative(deps.realpath(cwd), absolute);
      return { absolute, content, display: rel.startsWith("..") ? absolute : rel };
    });
    const names = docs.map((doc) => doc.display).join(", ");
    if (!deps.paneId) return { opened: [], text: `Not running inside Herdr, so no review pane opened. Tell the user to read: ${names}` };
    const running = viewer !== undefined && viewerAlive();
    const fresh = running ? docs.filter((doc) => !shown.has(doc.absolute)) : docs;
    if (viewer && running) {
      for (const doc of docs) nvim(viewer.socket, "--remote-expr", addRowExpr(doc.absolute));
      reload();
    } else {
      await launch(cwd, docs.map((doc) => doc.absolute));
    }
    for (const doc of docs) shown.set(doc.absolute, shown.get(doc.absolute) ?? { display: doc.display, snapshot: doc.content });
    if (fresh.length > 0) herdr("notification", "show", "Document ready for review", "--body", `${reason}: ${names}`, "--sound", "request");
    return {
      opened: docs.map((doc) => doc.display),
      text: `Opened ${names} in Herdr pane ${viewer?.pane} (editable nvim, one row per document) and returned without waiting for the user. Their saved edits will reach you as review feedback.`,
    };
  };

  /** The Mini SDD files to open after the agent wrote `path`, or none. */
  const miniSddFollowUp = (path: string): string[] => {
    if (shown.has(path) || !MINI_SDD_FILE.test(path)) return [];
    const folder = dirname(path);
    const folderOnScreen = [...shown.keys()].some((open) => dirname(open) === folder);
    if (folderOnScreen) return [path];
    if (basename(path) !== "spec.md" || !PROPOSED_STATUS.test(deps.readFile(path) ?? "")) return [];
    return MINI_SDD_PHASES.map((phase) => join(folder, phase)).filter((phasePath) => deps.readFile(phasePath) !== undefined);
  };

  /** After the agent changes a shown document, the version it saw is the new one, and the pane reloads it. */
  const agentWrote = (path: string): void => {
    const doc = shown.get(path);
    if (!doc) return;
    doc.snapshot = deps.readFile(path) ?? doc.snapshot;
    reload();
  };

  const refreshAfterShell = (): void => {
    if (shown.size === 0) return;
    for (const [path, doc] of shown) doc.snapshot = deps.readFile(path) ?? doc.snapshot;
    reload();
  };

  return {
    show,
    get viewer() {
      return viewer;
    },
    shown,
    setContext: (next: ExtensionContext) => {
      ctx = next;
    },
    readSaves,
    miniSddFollowUp,
    agentWrote,
    refreshAfterShell,
    closeViewer,
  };
}

export default function docReview(pi: ExtensionAPI, deps: DocReviewDeps = defaultDeps): void {
  const review = createDocReview(pi, deps);

  pi.registerTool(
    defineTool({
      name: "show_doc",
      label: "Show document",
      description:
        "Open documents the user should review in an editable nvim pane beside this session, one row per document (Herdr only; elsewhere it returns the paths to name to the user). " +
        "Use it when you want the user to read or approve a document: a spec, design, plan, report, or ADR. " +
        "It returns at once without waiting for the user. Documents stay open and reload when you edit them; the user's saved edits come back to you as a diff.",
      parameters: Type.Object({
        paths: Type.Array(Type.String({ description: "File path, absolute or relative to the working directory" }), { minItems: 1 }),
        reason: Type.String({ description: "One short line telling the user what to review, e.g. 'Spec ready for approval'" }),
      }),
      async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
        review.setContext(ctx);
        const result = await review.show(ctx.cwd, params.paths, params.reason);
        return { content: [{ type: "text", text: result.text }], details: { opened: result.opened } };
      },
    }),
  );

  pi.on("session_start", (_event, ctx) => review.setContext(ctx));

  pi.on("tool_result", async (event, ctx) => {
    review.setContext(ctx);
    if (event.isError) return;
    if (event.toolName === "bash") {
      review.refreshAfterShell();
      return;
    }
    if (event.toolName !== "write" && event.toolName !== "edit") return;
    const input = event.input as { path?: unknown };
    if (typeof input.path !== "string") return;
    const path = deps.realpath(isAbsolute(input.path) ? input.path : resolve(ctx.cwd, input.path));
    review.agentWrote(path);
    if (!deps.paneId) return;
    const followUp = review.miniSddFollowUp(path);
    if (followUp.length === 0) return;
    try {
      await review.show(ctx.cwd, followUp, basename(path) === "spec.md" ? "Spec proposed for approval" : `${basename(path)} written`);
    } catch (error) {
      if (ctx.hasUI) ctx.ui.notify(`doc-review could not open ${input.path}: ${(error as Error).message}`, "warning");
    }
  });

  pi.on("session_shutdown", () => review.closeViewer());
}

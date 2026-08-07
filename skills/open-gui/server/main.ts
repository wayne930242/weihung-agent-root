// open-gui backend: Deno process for HTTP/WS/static serving + sidecar supervision.
// See PROTOCOL.md for the wire protocols this file implements.

import { SidecarClient, type SidecarMessage } from "./sidecar_client.ts";
import {
  ensureStateDir,
  readTree,
  readThemeMode,
  seedPromptPath,
  stateDir,
  treeJsonPath,
  writeSessionRecord,
  type TreeDoc,
} from "./state.ts";

// D1 requires a brand-new, independent session — but `Deno.env.toObject()` is
// this harness's own environment, which carries session-identity markers
// (e.g. CLAUDE_CODE_CHILD_SESSION) that make a spawned `claude` believe it's a
// child of the invoking session and disable its own transcript saving.
// Strip anything CLAUDE-prefixed so the spawned process starts genuinely fresh.
function independentSpawnEnv(): Record<string, string> {
  const env = Deno.env.toObject();
  const filtered: Record<string, string> = {};
  for (const [key, value] of Object.entries(env)) {
    if (/^claude/i.test(key)) continue;
    filtered[key] = value;
  }
  return filtered;
}

function parseArgs(args: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith("--")) {
      out[args[i].slice(2)] = args[i + 1] ?? "";
      i++;
    }
  }
  return out;
}

const flags = parseArgs(Deno.args);
const targetCwd = flags.cwd ?? Deno.cwd();
const topic = flags.topic ?? "open-gui session";
const sessionId = flags["session-id"] ?? crypto.randomUUID();
const claudeBin = flags["claude-bin"] ?? "claude";
const seedPromptFile = flags["seed-file"]; // optional
const staticDir = flags["static-dir"] ??
  new URL("../web/out", import.meta.url).pathname;
const sidecarDir = new URL("./sidecar", import.meta.url).pathname;

const dir = stateDir(targetCwd, sessionId);
await ensureStateDir(dir);
const themeMode = await readThemeMode();

let seedPrompt = "";
if (seedPromptFile) {
  seedPrompt = await Deno.readTextFile(seedPromptFile);
}
await Deno.writeTextFile(seedPromptPath(dir), seedPrompt);

const sidecar = await SidecarClient.start(sidecarDir, Deno.env.toObject());

// Ring buffer of all PTY output since spawn, for pty:snapshot on (re)connect.
const MAX_BUFFER = 1024 * 1024;
let outputBuffer = "";
function appendToBuffer(chunk: string) {
  outputBuffer += chunk;
  if (outputBuffer.length > MAX_BUFFER) {
    outputBuffer = outputBuffer.slice(outputBuffer.length - MAX_BUFFER);
  }
}

const sockets = new Set<WebSocket>();
function broadcast(msg: unknown) {
  const payload = JSON.stringify(msg);
  for (const socket of sockets) {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(payload);
    }
  }
}

// Closing the browser tab deliberately does NOT shut this down (D10 — a
// closed WebSocket isn't a reliable "done" signal, reopening the URL must
// still reconnect to the live session). But with no timeout at all, a
// forgotten tab (or a browser auto-open that silently failed, PROTOCOL.md's
// documented risk — nobody ever connects at all) leaves the backend, its
// sidecar, and the spawned `claude` process running indefinitely. Neither
// case is a task-completion judgment call (the thing D8/D9's "never shut
// down" rule actually protects) — it's "nothing has been connected for a
// long time," a resource-lifecycle signal. Shut down after a sustained idle
// period with zero connections; any connection arriving before it fires
// cancels it, so a quick reconnect (network blip, accidental close) is
// unaffected.
const IDLE_SHUTDOWN_MS = 15 * 60 * 1000;
let idleShutdownTimer: ReturnType<typeof setTimeout> | undefined;

function scheduleIdleShutdown() {
  if (idleShutdownTimer !== undefined) clearTimeout(idleShutdownTimer);
  idleShutdownTimer = setTimeout(() => {
    console.error(
      `[open-gui] no browser connected for ${IDLE_SHUTDOWN_MS / 1000}s — shutting down`,
    );
    shutdown();
  }, IDLE_SHUTDOWN_MS);
}

function cancelIdleShutdown() {
  if (idleShutdownTimer !== undefined) {
    clearTimeout(idleShutdownTimer);
    idleShutdownTimer = undefined;
  }
}

let seedSent = false;
let seedTimer: ReturnType<typeof setTimeout> | undefined;
const SEED_QUIET_MS = 600;
// A long single-write burst reliably trips Claude Code's own paste-detection
// (confirmed live: the seed landed as a collapsed "[Pasted text #1 +1 lines]"
// chip, never submitted) — the trailing \r sent in the same write gets
// absorbed into the paste event instead of registering as a distinct
// "submit" keystroke. Sending \r as its own write, after the paste-detection
// window has closed, submits it correctly.
const SEED_SUBMIT_DELAY_MS = 200;

function scheduleSeedSend() {
  if (seedSent || !seedPrompt) return;
  if (seedTimer !== undefined) clearTimeout(seedTimer);
  // Readiness rule (PROTOCOL.md §3): a TUI emits output (cursor moves, banners,
  // permission prompts) well before its input box actually mounts — sending on
  // the very first `data` chunk can land the seed prompt on an intermediate
  // screen (e.g. Claude Code's one-time "trust this folder?" gate) instead of
  // the chat input. Wait for a quiet period with no further output instead —
  // once the process stops producing bytes, its current screen has settled.
  seedTimer = setTimeout(() => {
    if (seedSent) return;
    seedSent = true;
    // A raw PTY in the target TUI's cooked/raw mode treats an embedded newline
    // as "insert a line" (multi-line compose), not "submit" — only the final
    // \r does that. A seed prompt file's trailing/embedded newlines would
    // otherwise land as an inserted blank line and never actually submit.
    // Collapse to one logical line, same as the frontend does for node notes.
    const singleLine = seedPrompt.replace(/\s*\n\s*/g, " ").trim();
    sidecar.write(singleLine);
    setTimeout(() => sidecar.write("\r"), SEED_SUBMIT_DELAY_MS);
  }, SEED_QUIET_MS);
}

sidecar.onMessage((msg: SidecarMessage) => {
  switch (msg.type) {
    case "data": {
      appendToBuffer(msg.data);
      broadcast({ type: "pty:data", data: msg.data });
      scheduleSeedSend();
      break;
    }
    case "exit": {
      console.error(
        `[open-gui] session process exited (code=${msg.code} signal=${msg.signal})`,
      );
      // The wrapped `claude` process is gone — there is no PTY left to serve,
      // so keeping the backend (and its browser tabs) alive would just show a
      // permanently frozen terminal. This is a different signal from D8/D9's
      // "never shut down" rule: that rule is about not inferring task/content
      // completion from TREE.json; this is the underlying process itself
      // exiting, mechanical rather than a content judgment call. Broadcast
      // first so a connected browser can show why, then shut down — same
      // `shutdown()` used for SIGINT/SIGTERM, after a short delay so the
      // broadcast has time to actually reach clients before the socket drops.
      broadcast({ type: "session:ended", code: msg.code, signal: msg.signal });
      setTimeout(shutdown, 500);
      break;
    }
    case "error": {
      console.error(`[open-gui] sidecar error: ${msg.message}`);
      broadcast({ type: "fatal", message: msg.message });
      break;
    }
  }
});

// Pin a UUID as this claude session's own id (verified: `claude --session-id
// <uuid>` accepts this at spawn) so it's known upfront rather than needing to
// be parsed out of PTY output. This lets a user later resume the SAME session
// from a normal terminal (`claude --resume <claudeSessionId>`) after this
// open-gui session is stopped — a deliberate, explicit hand-off, not an
// automatic one (see SKILL.md's "Switch to a normal terminal" section: WS
// disconnects are not a reliable "user is done" signal, so this is never
// triggered by a closed tab on its own). Independent of `sessionId` (this
// process's own state-dir id, which may be a non-UUID string when a caller
// overrides it) — only used when spawning the real `claude` binary, since a
// test stand-in like `/bin/bash` doesn't understand the flag.
const claudeSessionId = crypto.randomUUID();
const usingRealClaude = !flags["claude-bin"];

await sidecar.spawn({
  file: claudeBin,
  args: usingRealClaude ? ["--session-id", claudeSessionId] : [],
  cwd: targetCwd,
  env: independentSpawnEnv(),
  cols: 80,
  rows: 24,
});

let currentTree: TreeDoc = await readTree(dir);
if (!currentTree.topic) currentTree.topic = topic;

(async () => {
  try {
    const watcher = Deno.watchFs(dir);
    for await (const event of watcher) {
      if (!event.paths.some((p) => p === treeJsonPath(dir))) continue;
      // Atomic writers (confirmed: Claude Code's own Write tool) write to a
      // temp file and rename it over the target — that surfaces as a
      // "rename" event on the final path, not "modify"/"create". Excluding
      // it silently dropped every tree update written this way.
      if (event.kind !== "modify" && event.kind !== "create" && event.kind !== "rename") {
        continue;
      }
      try {
        currentTree = await readTree(dir);
        broadcast({ type: "tree:update", tree: currentTree });
      } catch (err) {
        console.error(`[open-gui] failed to read TREE.json: ${err}`);
      }
    }
  } catch (err) {
    console.error(`[open-gui] TREE.json watcher failed: ${err}`);
  }
})();

const CONTENT_TYPES: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
};

async function serveStatic(pathname: string): Promise<Response> {
  let rel = pathname === "/" ? "/index.html" : pathname;
  let filePath = `${staticDir}${rel}`;
  try {
    const data = await Deno.readFile(filePath);
    const ext = rel.slice(rel.lastIndexOf("."));
    return new Response(data, {
      headers: { "content-type": CONTENT_TYPES[ext] ?? "application/octet-stream" },
    });
  } catch {
    return new Response("not found", { status: 404 });
  }
}

function handleWebSocket(socket: WebSocket) {
  sockets.add(socket);
  cancelIdleShutdown();
  socket.onopen = () => {
    socket.send(JSON.stringify({ type: "config", theme: themeMode }));
    socket.send(JSON.stringify({ type: "pty:snapshot", data: outputBuffer }));
    socket.send(JSON.stringify({ type: "tree:update", tree: currentTree }));
  };
  socket.onmessage = async (event) => {
    try {
      const msg = JSON.parse(event.data as string);
      switch (msg.type) {
        case "pty:write":
          await sidecar.write(msg.data);
          break;
        case "pty:resize":
          await sidecar.resize(msg.cols, msg.rows);
          break;
        case "preview:request": {
          const requestId = msg.requestId;
          try {
            const filePath = `${targetCwd}/${msg.path}`.replace(/\/+/g, "/");
            const content = await Deno.readTextFile(filePath);
            socket.send(JSON.stringify({ type: "preview:response", requestId, content }));
          } catch (err) {
            socket.send(
              JSON.stringify({
                type: "preview:response",
                requestId,
                error: `could not read ${msg.path}: ${err}`,
              }),
            );
          }
          break;
        }
      }
    } catch (err) {
      console.error(`[open-gui] bad WS message: ${err}`);
    }
  };
  socket.onclose = () => {
    sockets.delete(socket);
    if (sockets.size === 0) scheduleIdleShutdown();
  };
  socket.onerror = () => {
    sockets.delete(socket);
    if (sockets.size === 0) scheduleIdleShutdown();
  };
}

const server = Deno.serve({ port: 0 }, (req) => {
  const url = new URL(req.url);
  if (url.pathname === "/ws") {
    const { socket, response } = Deno.upgradeWebSocket(req);
    handleWebSocket(socket);
    return response;
  }
  return serveStatic(url.pathname);
});

const port = (server.addr as Deno.NetAddr).port;
const sessionUrl = `http://localhost:${port}/`;
await writeSessionRecord(dir, {
  pid: Deno.pid,
  port,
  url: sessionUrl,
  claudeSessionId: usingRealClaude ? claudeSessionId : null,
});

scheduleIdleShutdown();

console.log(`[open-gui] session ready: ${sessionUrl}`);
console.log(`[open-gui] state dir: ${dir}`);
if (usingRealClaude) {
  console.log(`[open-gui] claude session id: ${claudeSessionId}`);
  console.log(
    `[open-gui] to switch to a normal terminal later: stop this session, then run \`claude --resume ${claudeSessionId}\``,
  );
}

function shutdown() {
  sidecar.kill();
  Deno.exit(0);
}
Deno.addSignalListener("SIGINT", shutdown);
Deno.addSignalListener("SIGTERM", shutdown);

await server.finished;

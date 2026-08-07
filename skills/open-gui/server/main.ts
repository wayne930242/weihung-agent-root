// open-gui backend: Deno process for HTTP/WS/static serving + Agent SDK session
// orchestration. See PROTOCOL.md for the wire protocols this file implements.
// design.md D11: no PTY, no Node sidecar — the Deno process drives
// @anthropic-ai/claude-agent-sdk directly via an npm: specifier.

import { query } from "npm:@anthropic-ai/claude-agent-sdk";
import {
  ensureStateDir,
  patchNodeStatus,
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
const seedPromptFile = flags["seed-file"]; // optional
const staticDir = flags["static-dir"] ??
  new URL("../web/out", import.meta.url).pathname;

const dir = stateDir(targetCwd, sessionId);
await ensureStateDir(dir);
const themeMode = await readThemeMode();

let seedPrompt = "";
if (seedPromptFile) {
  seedPrompt = await Deno.readTextFile(seedPromptFile);
}
await Deno.writeTextFile(seedPromptPath(dir), seedPrompt);

// D11: transcript entries are a lightly-summarized view of the SDK message
// stream, not the raw structured messages — the frontend renders plain text,
// not a full chat UI (advisor guidance: rendering was never what broke, no
// need to rebuild it). Ring-buffered the same way the old PTY output was, for
// transcript:snapshot on (re)connect.
type TranscriptEntry =
  | { kind: "assistant"; text: string }
  | { kind: "tool_use"; tool: string; summary: string }
  | { kind: "system"; text: string };

const MAX_TRANSCRIPT = 2000;
const transcript: TranscriptEntry[] = [];
function pushTranscript(entry: TranscriptEntry) {
  transcript.push(entry);
  if (transcript.length > MAX_TRANSCRIPT) transcript.shift();
  broadcast({ type: "transcript:event", entry });
}

function summarizeToolInput(name: string, input: Record<string, unknown>): string {
  if (name === "Bash" && typeof input.command === "string") return input.command;
  if (typeof input.file_path === "string") return input.file_path;
  if (typeof input.path === "string") return input.path;
  const json = JSON.stringify(input);
  return json.length > 140 ? json.slice(0, 140) + "…" : json;
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
// documented risk — nobody ever connects at all) leaves the backend and the
// spawned `claude` process running indefinitely. Neither case is a
// task-completion judgment call (the thing D8/D9's "never shut down" rule
// actually protects) — it's "nothing has been connected for a long time," a
// resource-lifecycle signal. Shut down after a sustained idle period with
// zero connections; any connection arriving before it fires cancels it, so a
// quick reconnect (network blip, accidental close) is unaffected.
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

// D11: streaming input is a push-driven async iterable — the seed prompt is
// the first pushed message, and further free-text messages (a node's
// FreeTextBox, or the transcript pane's own input) are pushed as they arrive
// over WebSocket, potentially hours apart. This replaces the old PTY stdin.
type SDKUserMsg = {
  type: "user";
  message: { role: "user"; content: string };
  parent_tool_use_id: null;
};
let pushMessage: (text: string) => void;
const inputStream: AsyncIterable<SDKUserMsg> = {
  [Symbol.asyncIterator]() {
    const pending: SDKUserMsg[] = [];
    let waiting: ((r: IteratorResult<SDKUserMsg>) => void) | null = null;
    pushMessage = (text: string) => {
      // A blind usability test found no way to tell "the agent is working
      // on this" from "nothing is happening" — no spinner, no indicator, at
      // all, anywhere. `agent:busy`/`agent:idle` (paired with the `result`
      // handler below) give the frontend that signal.
      broadcast({ type: "agent:busy" });
      const msg: SDKUserMsg = {
        type: "user",
        message: { role: "user", content: text },
        parent_tool_use_id: null,
      };
      if (waiting) {
        const resolve = waiting;
        waiting = null;
        resolve({ value: msg, done: false });
      } else {
        pending.push(msg);
      }
    };
    return {
      next(): Promise<IteratorResult<SDKUserMsg>> {
        if (pending.length > 0) {
          return Promise.resolve({ value: pending.shift()!, done: false });
        }
        return new Promise((resolve) => {
          waiting = resolve;
        });
      },
    };
  },
};

// D11: AskUserQuestion's `canUseTool` call blocks until this resolves — the
// browser-mediated answer flow. Only one can be genuinely pending at a time
// (the SDK's conversation loop can't reach a second AskUserQuestion call
// while the first's callback hasn't resolved), but keyed by toolUseID anyway
// since canUseTool exposes it for free and it makes the WS contract
// (question:ask/question:answer) explicit rather than implicit-singleton.
const pendingQuestions = new Map<
  string,
  (answers: Record<string, string | string[]>) => void
>();
// The one currently-outstanding question:ask payload, if any — replayed on
// socket open the same way currentTree is, so a client connecting *after*
// AskUserQuestion already fired (a real timing case: nothing forces a
// browser to be connected the instant Claude asks) still sees it instead of
// the question silently never appearing.
let pendingQuestionBroadcast: { requestId: string; questions: unknown } | null = null;

// Pin a UUID as this claude session's own id upfront (Options.sessionId, the
// SDK-level mirror of `claude --session-id`) rather than needing to be parsed
// out of anywhere. This lets a user later resume the SAME session from a
// normal terminal (`claude --resume <claudeSessionId>`) after this open-gui
// session is stopped — a deliberate, explicit hand-off, not an automatic one
// (see SKILL.md's "Switch to a normal terminal" section: WS disconnects are
// not a reliable "user is done" signal, so this is never triggered by a
// closed tab on its own).
const claudeSessionId = crypto.randomUUID();

const sdkQuery = query({
  prompt: inputStream,
  options: {
    cwd: targetCwd,
    env: independentSpawnEnv(),
    sessionId: claudeSessionId,
    canUseTool: async (toolName, input, ctx) => {
      if (toolName !== "AskUserQuestion") {
        return { behavior: "allow", updatedInput: input };
      }
      const questions = (input.questions ?? []) as Array<{
        question: string;
        header: string;
        options: Array<{ label: string; description?: string }>;
        multiSelect?: boolean;
      }>;
      pendingQuestionBroadcast = { requestId: ctx.toolUseID, questions };
      broadcast({ type: "question:ask", requestId: ctx.toolUseID, questions });
      // A pending question is a "waiting on you" pause, not "agent is
      // still working" — the tool call blocks the SDK's own turn from ever
      // reaching a `result` message until answered, so without this the
      // busy indicator would stay lit the whole time you're the one being
      // asked to act.
      broadcast({ type: "agent:idle" });
      const answers = await new Promise<Record<string, string | string[]>>((resolve) => {
        pendingQuestions.set(ctx.toolUseID, resolve);
      });
      pendingQuestionBroadcast = null;
      return { behavior: "allow", updatedInput: { questions, answers } };
    },
  },
});

pushMessage!(seedPrompt.replace(/\s*\n\s*/g, " ").trim());

let currentTree: TreeDoc = await readTree(dir);
if (!currentTree.topic) currentTree.topic = topic;

(async () => {
  try {
    for await (const message of sdkQuery) {
      if (message.type === "assistant") {
        for (const block of message.message.content) {
          if (block.type === "text" && block.text.trim()) {
            pushTranscript({ kind: "assistant", text: block.text });
          } else if (block.type === "tool_use" && block.name !== "AskUserQuestion") {
            // AskUserQuestion gets its own interactive question:ask card
            // instead (see canUseTool below) — a generic tool_use summary
            // for it would just duplicate that, unhelpfully.
            pushTranscript({
              kind: "tool_use",
              tool: block.name,
              summary: summarizeToolInput(
                block.name,
                block.input as Record<string, unknown>,
              ),
            });
          }
        }
      } else if (message.type === "result") {
        if (message.subtype !== "success") {
          pushTranscript({ kind: "system", text: `[turn ended: ${message.subtype}]` });
        }
        broadcast({ type: "agent:idle" });
      }
    }
    console.error(`[open-gui] session stream ended`);
  } catch (err) {
    console.error(`[open-gui] session stream error: ${err}`);
    broadcast({ type: "fatal", message: String(err) });
  }
  broadcast({ type: "session:ended" });
  setTimeout(shutdown, 500);
})();

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
    socket.send(JSON.stringify({ type: "transcript:snapshot", entries: transcript }));
    socket.send(JSON.stringify({ type: "tree:update", tree: currentTree }));
    if (pendingQuestionBroadcast) {
      socket.send(JSON.stringify({ type: "question:ask", ...pendingQuestionBroadcast }));
    }
  };
  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data as string);
      switch (msg.type) {
        case "message:send":
          // No "> " prefix: a leading #[id] tag (buildSubmission, lib/
          // submission.js) must stay the literal first characters for the
          // frontend's routing to see it (design.md D12) — the echo relies
          // on .thread-entry-system styling to read as "you sent this",
          // not a textual quote marker.
          pushTranscript({ kind: "system", text: msg.text });
          pushMessage(msg.text);
          break;
        case "question:answer": {
          const resolve = pendingQuestions.get(msg.requestId);
          if (resolve) {
            pendingQuestions.delete(msg.requestId);
            // One echo PER question, not one joined "Answered: ..." summary
            // — the old single-string form put "Answered: " before each
            // question's own leading #[id] tag, breaking the frontend's
            // leading-tag-anchor routing (lib/tagRouting.js) so every
            // answer fell to the root card regardless of which node the
            // question was actually about, and joining multiple questions
            // into one string couldn't route to more than one node anyway.
            // A live-question card is ephemeral once answered (removed from
            // `liveQuestions` — CanvasView.js), so without this echo
            // becoming a chain card, the answer left no visible trace at
            // all (user: "使用者的心智圖要怎麼建立").
            for (const [q, a] of Object.entries(msg.answers as Record<string, unknown>)) {
              const answerText = Array.isArray(a) ? a.join(", ") : String(a);
              pushTranscript({ kind: "system", text: `${q} → ${answerText}` });
            }
            broadcast({ type: "question:resolved", requestId: msg.requestId });
            // Resolving this promise un-blocks canUseTool and lets the SDK's
            // turn continue running — but nothing else on this path signals
            // that (unlike message:send/node:reconsider/session:finalize,
            // which all go through pushMessage's own agent:busy broadcast).
            // Without this, answering a live question leaves the busy pill
            // dark for however long the agent keeps working before its next
            // question:ask/result — observed via a blind usability test as a
            // silent ~60-90s gap after the last branch's answer, right when
            // the agent was actually still finalizing.
            broadcast({ type: "agent:busy" });
            resolve(msg.answers);
          }
          break;
        }
        case "node:reconsider": {
          const nodeId = msg.nodeId as string;
          const title = msg.title as string;
          const previousResolution = msg.previousResolution as string | undefined;
          patchNodeStatus(dir, nodeId, "open")
            .then((found) => {
              if (!found) return;
              // No transcript echo here (unlike buildSubmission's own-reply
              // echoes) — the card's status badge flipping to OPEN is
              // already the visible signal; echoing "Reconsider requested"
              // as thread content just duplicated it and, worse, briefly
              // displaced the card's real resolution text.
              //
              // Carries the previous conclusion as context and frames this
              // as withdrawing it, rather than a bare "reconsider this" with
              // nothing to reconsider from (user: "重新考慮只需要把前一題的
              // 結論帶脈絡重送，並且表示撤回前輪就好").
              const withdrawn = previousResolution
                ? ` I'm withdrawing the previous conclusion: "${previousResolution}".`
                : "";
              pushMessage(
                `Reconsider "${title}" [${nodeId}] — I've reopened it in TREE.json ` +
                  `(status: open).${withdrawn} Please update or remove anything else ` +
                  `that depended on it, then ask me again if you need to.`,
              );
            })
            .catch((err) => console.error(`[open-gui] node:reconsider failed: ${err}`));
          break;
        }
        case "session:finalize": {
          pushTranscript({ kind: "system", text: "Finalize requested" });
          // "Decide yourself, don't ask" is the operative instruction here —
          // 收斂 means the user is done providing input, so any still-open
          // branch getting answered with a NEW AskUserQuestion instead of a
          // judgment call defeats the point (user: "收斂了，那些問題應該全部
          // 設定成 resolve，回答都是「as agent decide」").
          pushMessage(
            "Please finalize now: the user is done providing input, so do not ask " +
              "any further questions. For every branch still open, decide it " +
              "yourself using your own best judgment and resolve it (or explicitly " +
              "drop it) rather than asking — then write the summary doc and set " +
              "TREE.json's top-level status to complete.",
          );
          break;
        }
        case "session:stop": {
          console.error(`[open-gui] session:stop requested from browser`);
          shutdown();
          break;
        }
        case "preview:request": {
          const requestId = msg.requestId;
          Deno.readTextFile(`${targetCwd}/${msg.path}`.replace(/\/+/g, "/"))
            .then((content) => {
              socket.send(JSON.stringify({ type: "preview:response", requestId, content }));
            })
            .catch((err) => {
              socket.send(
                JSON.stringify({
                  type: "preview:response",
                  requestId,
                  error: `could not read ${msg.path}: ${err}`,
                }),
              );
            });
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
  claudeSessionId,
});

scheduleIdleShutdown();

console.log(`[open-gui] session ready: ${sessionUrl}`);
console.log(`[open-gui] state dir: ${dir}`);
console.log(`[open-gui] claude session id: ${claudeSessionId}`);
console.log(
  `[open-gui] to switch to a normal terminal later: stop this session, then run \`claude --resume ${claudeSessionId}\``,
);

function shutdown() {
  sdkQuery.close();
  Deno.exit(0);
}
Deno.addSignalListener("SIGINT", shutdown);
Deno.addSignalListener("SIGTERM", shutdown);

await server.finished;

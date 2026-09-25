import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFileSync } from "node:child_process";
import { chmodSync, existsSync, mkdirSync, readFileSync, renameSync, rmdirSync, unlinkSync, watch, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

type Dispatch = {
  id: string;
  name: string;
  task: string;
  cwd: string;
  sessionFile: string;
  launchScriptFile?: string;
  paneId?: string;
  status: "running" | "done" | "failed" | "transferred";
  delivered?: boolean;
};

const agentDir = process.env.PI_CODING_AGENT_DIR || join(homedir(), ".pi", "agent");
const ledgerDir = join(agentDir, "dispatch-ledger");
const forwardedDir = join(agentDir, "dispatch-forwarded");
const deliveredDir = join(agentDir, "dispatch-delivered");
const dispatchScript = fileURLToPath(new URL("../../scripts/pi-dispatch.py", import.meta.url));
const processSessions = ((globalThis as any).__weihungDispatchSessions ??= new Set<string>());
const watchers = new Map<string, ReturnType<typeof watch>>();
const timers = new Map<string, ReturnType<typeof setInterval>>();
const lockWait = new Int32Array(new SharedArrayBuffer(4));

function withLedgerLock<T>(sessionId: string, action: () => T): T {
  mkdirSync(ledgerDir, { recursive: true });
  const lock = join(ledgerDir, `.${sessionId}.lock`);
  for (let attempt = 0; attempt < 500; attempt++) {
    try {
      mkdirSync(lock);
      break;
    } catch (error: any) {
      if (error.code !== "EEXIST") throw error;
      if (attempt === 499) throw new Error(`Timed out waiting for dispatch ledger ${sessionId}`);
      Atomics.wait(lockWait, 0, 0, 10);
    }
  }
  try { return action(); } finally { rmdirSync(lock); }
}

function ledgerFile(sessionId: string): string {
  return join(ledgerDir, `${sessionId}.json`);
}

function readLedger(sessionId: string): Dispatch[] {
  const path = ledgerFile(sessionId);
  if (!existsSync(path)) return [];
  const parsed = JSON.parse(readFileSync(path, "utf8"));
  return Array.isArray(parsed) ? parsed : [];
}

function writeLedger(sessionId: string, records: Dispatch[]): void {
  mkdirSync(ledgerDir, { recursive: true });
  writeFileSync(ledgerFile(sessionId), JSON.stringify(records, null, 2) + "\n");
  chmodSync(ledgerFile(sessionId), 0o600);
}

function forwardedFile(id: string): string {
  return join(forwardedDir, `${id}.json`);
}

function deliveredFile(id: string): string {
  return join(deliveredDir, id);
}

function writeForwarded(id: string, result: { status: "done" | "failed"; content: string }): void {
  mkdirSync(forwardedDir, { recursive: true });
  const path = forwardedFile(id);
  const temporary = `${path}.${process.pid}.tmp`;
  writeFileSync(temporary, JSON.stringify(result), { mode: 0o600 });
  chmodSync(temporary, 0o600);
  renameSync(temporary, path);
}

function sessionEntries(file: string): any[] {
  if (!existsSync(file)) return [];
  return readFileSync(file, "utf8").split("\n").filter(Boolean).flatMap((line) => {
    try { return [JSON.parse(line)]; } catch { return []; }
  });
}

function deliveredInParent(parentFile: string, childFile: string): any | undefined {
  return sessionEntries(parentFile).find((entry) =>
    entry.type === "custom_message" && entry.customType === "subagent_result" &&
    entry.details?.sessionFile === childFile
  );
}

function reconcileDelivered(sessionId: string, parentFile: string): void {
  const records = readLedger(sessionId);
  let changed = false;
  for (const record of records) {
    if (record.status !== "running") continue;
    const result = deliveredInParent(parentFile, record.sessionFile);
    if (!result) continue;
    record.status = result.details?.exitCode === 0 ? "done" : "failed";
    record.delivered = true;
    changed = true;
  }
  if (changed) writeLedger(sessionId, records);
}

function finalMessage(childFile: string): string {
  const messages = sessionEntries(childFile).filter((entry) => entry.type === "message" && entry.message?.role === "assistant");
  const last = messages.at(-1)?.message;
  const text = last?.content?.filter((part: any) => part.type === "text").map((part: any) => part.text).join("\n");
  return text || "The child session ended without a final text message. Inspect its session file.";
}

function observe(sessionId: string, parentFile: string, record: Dispatch, pi: ExtensionAPI): void {
  if (watchers.has(record.id) || record.status !== "running") return;
  const sidecar = `${record.sessionFile}.exit`;
  const forwarded = forwardedFile(record.id);
  const settle = () => {
    if (!existsSync(sidecar) && !existsSync(forwarded)) return;
    withLedgerLock(sessionId, () => {
      const records = readLedger(sessionId);
      const current = records.find((item) => item.id === record.id);
      if (!current || current.status !== "running") return;
      let result: any;
      try { result = JSON.parse(readFileSync(existsSync(forwarded) ? forwarded : sidecar, "utf8")); }
      catch { return; }
      current.status = result.status === "done" || result.status === "failed"
        ? result.status : (result.type === "done" ? "done" : "failed");
      current.delivered = Boolean(deliveredInParent(parentFile, current.sessionFile));
      writeLedger(sessionId, records);
      watchers.get(record.id)?.close();
      watchers.delete(record.id);
      clearInterval(timers.get(record.id));
      timers.delete(record.id);
      if (!current.delivered) {
        pi.sendMessage({
          customType: "recovered_dispatch_result",
          content: `Recovered dispatch ${current.name} (${current.status}). Session: ${current.sessionFile}\n\n${result.content || finalMessage(current.sessionFile)}`,
          display: true,
          details: { id: current.id, sessionFile: current.sessionFile, status: current.status },
        }, { triggerTurn: true, deliverAs: "steer" });
        current.delivered = true;
        writeLedger(sessionId, records);
      }
      mkdirSync(deliveredDir, { recursive: true });
      writeFileSync(deliveredFile(record.id), "");
      chmodSync(deliveredFile(record.id), 0o600);
      if (existsSync(forwarded)) unlinkSync(forwarded);
    });
  };
  mkdirSync(dirname(sidecar), { recursive: true });
  watchers.set(record.id, watch(dirname(sidecar), (_event, name) => {
    if (name === basename(sidecar)) settle();
  }));
  timers.set(record.id, setInterval(settle, 500));
  settle();
}

export default function dispatchRecovery(pi: ExtensionAPI): void {
  if (!process.env.PI_SUBAGENT_ID) {
    pi.registerTool({
      name: "dispatch_control",
      label: "Dispatch inventory and handoff",
      description: "List unfinished dispatches, resume a stopped worker session, or transfer this main scope to a new Herdr pane.",
      parameters: {
        type: "object",
        properties: {
          action: { type: "string", enum: ["roll-call", "reattach", "handoff"] },
          id: { type: "string" },
          summary: { type: "string" },
        },
        required: ["action"],
      },
      execute: async (_toolId, params, _signal, _update, ctx) => {
        const sessionId = ctx.sessionManager.getSessionId();
        const parentFile = ctx.sessionManager.getSessionFile();
        if (parentFile) reconcileDelivered(sessionId, parentFile);
        const args = [dispatchScript, params.action, "--session-id", sessionId, "--cwd", ctx.cwd];
        if (params.action === "reattach") {
          if (!params.id) throw new Error("reattach requires a dispatch ID");
          args.splice(2, 0, params.id);
        }
        if (params.action === "handoff") {
          if (!params.summary) throw new Error("handoff requires a scope summary");
          args.push("--summary", params.summary);
        }
        try {
          const output = execFileSync("python3", args, { encoding: "utf8" }).trim();
          return { content: [{ type: "text", text: output }] };
        } catch (error: any) {
          throw new Error(error.stderr?.toString().trim() || error.message);
        }
      },
    });
  }

  pi.on("tool_result", (event, ctx) => {
    if (event.toolName !== "subagent" || event.isError) return;
    const details = event.details as any;
    if (details?.status !== "started" || !details.id || !details.sessionFile) return;
    const sessionId = ctx.sessionManager.getSessionId();
    const records = readLedger(sessionId);
    if (records.some((record) => record.id === details.id)) return;
    let paneId = details.worktree?.paneId;
    if (!paneId && details.launchScriptFile && existsSync(details.launchScriptFile)) {
      const script = readFileSync(details.launchScriptFile, "utf8");
      paneId = script.match(/PI_SUBAGENT_SURFACE=([^\s;]+)/)?.[1]?.replaceAll("'", "");
    }
    records.push({
      id: details.id, name: details.name, task: details.task,
      cwd: String(event.input.cwd || ctx.cwd), sessionFile: details.sessionFile,
      launchScriptFile: details.launchScriptFile, paneId, status: "running",
    });
    writeLedger(sessionId, records);
  });

  pi.on("message_end", (event, ctx) => {
    const message = event.message as any;
    if (message.role !== "custom" || message.customType !== "subagent_result") return;
    return withLedgerLock(ctx.sessionManager.getSessionId(), () => {
      const records = readLedger(ctx.sessionManager.getSessionId());
      const record = records.find((item) => item.sessionFile === message.details?.sessionFile);
      if (!record) return;
      if (record.status === "running") {
        record.status = message.details?.exitCode === 0 ? "done" : "failed";
        record.delivered = true;
        writeLedger(ctx.sessionManager.getSessionId(), records);
        return;
      }
      if (record.status === "transferred" && !existsSync(deliveredFile(record.id))) {
        writeForwarded(record.id, {
          status: message.details?.exitCode === 0 ? "done" : "failed",
          content: String(message.details?.resultContent || finalMessage(record.sessionFile)),
        });
      }
      return { message: {
        ...message,
        customType: "transferred_dispatch_notice",
        content: `Dispatch ${record.name} was ${record.status === "transferred" ? "transferred" : "already delivered"}.`,
        display: false,
        details: { id: record.id, sessionFile: record.sessionFile },
      } };
    });
  });

  pi.on("session_start", (event, ctx) => {
    const sessionId = ctx.sessionManager.getSessionId();
    const parentFile = ctx.sessionManager.getSessionFile();
    const sameProcess = processSessions.has(sessionId);
    processSessions.add(sessionId);
    if (sameProcess || !parentFile) return;
    reconcileDelivered(sessionId, parentFile);
    const handoffId = process.env.PI_HANDOFF_ID;
    if (handoffId) {
      const handoffFile = join(agentDir, "handoffs", `${handoffId}.json`);
      if (existsSync(handoffFile)) {
        const handoff = JSON.parse(readFileSync(handoffFile, "utf8"));
        const existing = readLedger(sessionId);
        for (const record of handoff.dispatches || []) {
          if (!existing.some((item) => item.id === record.id)) existing.push(record);
        }
        writeLedger(sessionId, existing);
      }
    }
    for (const record of readLedger(sessionId)) {
      if (record.status === "running") observe(sessionId, parentFile, record, pi);
    }
  });

  pi.on("session_shutdown", () => {
    for (const watcher of watchers.values()) watcher.close();
    watchers.clear();
    for (const timer of timers.values()) clearInterval(timer);
    timers.clear();
  });
}

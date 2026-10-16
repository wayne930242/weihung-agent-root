import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { mkdirSync, statSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

export const MAX_WAIT_MS = 6 * 60 * 60 * 1000;
export const RESUME_MARGIN_MS = 2 * 60 * 1000;
export const POLL_MS = 15_000;
// pi-herdr-agents asks this channel before a child exits on a settled run.
export const EXIT_HOLD_CHANNEL = "pi-herdr-agents:exit-hold";
export const RESUME_SIGNAL = join(homedir(), ".local/state/weihung-agent-root/quota-resume");
export const RESUME_PROMPT =
  "The Claude usage limit that stopped the previous turn has reset. Continue the task from where it stopped.";

const STATUS_KEY = "quota-resume";
const QUOTA_ERROR = /quota exceeded|rate limit|hit your .*limit|out of extra usage/i;
// The text fallback carries a clock time without a date, which only identifies the five-hour window.
const FIVE_HOUR = /five_hour|session limit/i;
const RESET_CLOCK = /resets\s+(\d{1,2})(?::(\d{2}))?(?::\d{2})?\s*([ap]m)?/i;

export type AssistantError = { role?: string; stopReason?: string; errorMessage?: string; timestamp?: number };

export type QuotaWaitDeps = {
  now: () => number;
  signalMtime: () => number | undefined;
  touchSignal: () => void;
  setInterval: (callback: () => void, ms: number) => unknown;
  clearInterval: (handle: unknown) => void;
};

const defaultDeps: QuotaWaitDeps = {
  now: Date.now,
  signalMtime: () => {
    try {
      return statSync(RESUME_SIGNAL).mtimeMs;
    } catch {
      return undefined;
    }
  },
  touchSignal: () => {
    mkdirSync(dirname(RESUME_SIGNAL), { recursive: true });
    writeFileSync(RESUME_SIGNAL, `${new Date().toISOString()}\n`);
  },
  setInterval: (callback, ms) => setInterval(callback, ms),
  clearInterval: (handle) => clearInterval(handle as ReturnType<typeof setInterval>),
};

/** The next time of day at `hour:minute` after `after`, in local time. */
function nextClock(after: number, hour: number, minute: number): number {
  const at = new Date(after);
  at.setHours(hour, minute, 0, 0);
  if (at.getTime() <= after) at.setDate(at.getDate() + 1);
  return at.getTime();
}

function parseResetClock(text: string, after: number): number | undefined {
  if (!FIVE_HOUR.test(text)) return undefined;
  const match = RESET_CLOCK.exec(text);
  if (!match) return undefined;
  let hour = Number(match[1]);
  const minute = match[2] ? Number(match[2]) : 0;
  const meridiem = match[3]?.toLowerCase();
  if (meridiem === "pm" && hour < 12) hour += 12;
  if (meridiem === "am" && hour === 12) hour = 0;
  if (hour > 23 || minute > 59) return undefined;
  return nextClock(after, hour, minute);
}

/**
 * When the settled run ended on a Claude quota error that resets within MAX_WAIT_MS, the time to resume it.
 * `rejectedResetMs` is the exact reset the provider reported for this run, when it reported one.
 */
export function quotaResumeAt(message: AssistantError | undefined, rejectedResetMs: number | undefined, now: number): number | undefined {
  if (message?.role !== "assistant" || message.stopReason !== "error") return undefined;
  const text = message.errorMessage ?? "";
  if (!QUOTA_ERROR.test(text)) return undefined;
  const resetMs = rejectedResetMs ?? parseResetClock(text, message.timestamp ?? now);
  if (resetMs === undefined || resetMs - now > MAX_WAIT_MS) return undefined;
  return Math.max(resetMs, now) + RESUME_MARGIN_MS;
}

function lastAssistant(messages: readonly unknown[] | undefined): AssistantError | undefined {
  for (let i = (messages?.length ?? 0) - 1; i >= 0; i--) {
    const message = messages?.[i] as AssistantError | undefined;
    if (message?.role === "assistant") return message;
  }
  return undefined;
}

function branchMessages(ctx: ExtensionContext): unknown[] {
  return ctx.sessionManager.getBranch().flatMap((entry) => (entry.type === "message" ? [entry.message] : []));
}

function clock(ms: number): string {
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function quotaResume(pi: ExtensionAPI, deps: QuotaWaitDeps = defaultDeps): void {
  let rejectedResetMs: number | undefined;
  let wait: { ctx: ExtensionContext; resumeAt: number; since: number; poll: unknown } | undefined;

  const stopWait = (): void => {
    if (!wait) return;
    deps.clearInterval(wait.poll);
    wait.ctx.ui.setStatus(STATUS_KEY, undefined);
    wait = undefined;
  };

  const resume = (): void => {
    const ctx = wait?.ctx;
    stopWait();
    if (ctx?.isIdle()) pi.sendUserMessage(RESUME_PROMPT);
  };

  const check = (): void => {
    if (!wait) return;
    const signalled = deps.signalMtime();
    if (deps.now() >= wait.resumeAt || (signalled !== undefined && signalled > wait.since)) resume();
  };

  const startWait = (ctx: ExtensionContext, resumeAt: number): void => {
    stopWait();
    wait = { ctx, resumeAt, since: deps.now(), poll: deps.setInterval(check, POLL_MS) };
    const text = `Claude quota exhausted; resuming at ${clock(resumeAt)} (/quota-resume resumes now)`;
    ctx.ui.setStatus(STATUS_KEY, text);
    ctx.ui.notify(text, "warning");
  };

  // Answered synchronously, so the hold does not depend on which agent_settled handler runs first.
  pi.events.on(EXIT_HOLD_CHANNEL, (data) => {
    const probe = data as { messages?: unknown[]; hold?: boolean } | undefined;
    if (!probe || !Array.isArray(probe.messages)) return;
    if (quotaResumeAt(lastAssistant(probe.messages), rejectedResetMs, deps.now()) !== undefined) probe.hold = true;
  });

  pi.on("after_provider_response", (event) => {
    const status = event.headers["anthropic-ratelimit-unified-status"];
    const reset = Number(event.headers["anthropic-ratelimit-unified-reset"]);
    if (status === "rejected" && Number.isFinite(reset) && reset > 0) rejectedResetMs = reset * 1000;
    else if (status === "allowed" || status === "allowed_warning") rejectedResetMs = undefined;
  });

  pi.on("agent_start", () => {
    rejectedResetMs = undefined;
    stopWait();
  });

  pi.on("agent_settled", (event, ctx) => {
    if (event.aborted) return;
    const resumeAt = quotaResumeAt(lastAssistant(branchMessages(ctx)), rejectedResetMs, deps.now());
    if (resumeAt !== undefined) startWait(ctx, resumeAt);
  });

  pi.on("session_shutdown", () => stopWait());

  pi.registerCommand("quota-resume", {
    description: "Resume every session waiting on a Claude quota reset now, e.g. after switching accounts",
    handler: async (_args, ctx) => {
      deps.touchSignal();
      if (wait) resume();
      else ctx.ui.notify("Signalled every session waiting on a Claude quota reset to resume.", "info");
    },
  });
}

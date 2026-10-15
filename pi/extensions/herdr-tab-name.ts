import { execFile } from "node:child_process";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

export const MAX_LABEL_CHARS = 16;

export type HerdrRun = (args: string[]) => Promise<string>;

const defaultRun: HerdrRun = (args) =>
  new Promise((resolve, reject) => {
    execFile(process.env.HERDR_BIN_PATH || "herdr", args, { timeout: 5000 }, (error, stdout) => {
      if (error) reject(error);
      else resolve(stdout);
    });
  });

type UserContent = string | { type: string; text?: string }[];

function contentText(content: UserContent): string {
  if (!Array.isArray(content)) return content;
  return content.flatMap((part) => (part.type === "text" && part.text ? [part.text] : [])).join(" ");
}

export function shortLabel(text: string): string {
  const chars = Array.from(text.replace(/\s+/g, " ").trim());
  return chars.length > MAX_LABEL_CHARS ? `${chars.slice(0, MAX_LABEL_CHARS).join("").trimEnd()}…` : chars.join("");
}

function firstUserText(ctx: ExtensionContext): string {
  for (const entry of ctx.sessionManager.getBranch()) {
    if (entry?.type === "message" && entry.message.role === "user") return contentText(entry.message.content as UserContent);
  }
  return "";
}

export default function herdrTabName(pi: ExtensionAPI, run: HerdrRun = defaultRun): void {
  const paneId = process.env.HERDR_PANE_ID;
  // Outside Herdr there is no tab; a subagent shares or owns a tab its parent names.
  if (!paneId || process.env.PI_SUBAGENT_ID) return;

  // The label this session last set; a tab showing anything else besides a bare number was named by someone else.
  let owned: string | undefined;
  let queue: Promise<void> = Promise.resolve();

  const sync = (label: string): void => {
    if (!label) return;
    queue = queue.then(async () => {
      try {
        const pane = JSON.parse(await run(["pane", "get", paneId])).result.pane;
        const tab = JSON.parse(await run(["tab", "get", pane.tab_id])).result.tab;
        const current = String(tab.label);
        if (current === label || (!/^\d+$/.test(current) && current !== owned)) return;
        await run(["tab", "rename", pane.tab_id, label]);
        owned = label;
      } catch {
        // A tab label is cosmetic; a missing pane or a herdr failure must not disturb the session.
      }
    });
  };

  // A session name wins; otherwise the first user message names the tab, falling back to the prompt about to run.
  const labelFor = (ctx: ExtensionContext, name: string | undefined, prompt = ""): string =>
    shortLabel(name || firstUserText(ctx) || prompt);

  pi.on("session_start", (_event, ctx) => sync(labelFor(ctx, pi.getSessionName())));
  pi.on("before_agent_start", (event, ctx) => sync(labelFor(ctx, pi.getSessionName(), "prompt" in event ? event.prompt : "")));
  pi.on("session_info_changed", (event, ctx) => sync(labelFor(ctx, event.name)));
}

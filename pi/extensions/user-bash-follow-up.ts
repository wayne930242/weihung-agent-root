import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

export const POLL_MS = 200;
export const FOLLOW_UP_TYPE = "user-bash-follow-up";
export const FOLLOW_UP_PROMPT = "The user just ran the shell command above with `!`. Read its output and respond to it.";

// pi records a `!` command's output but starts no turn. This extension leaves execution
// to pi (keeping live output and every other user_bash handler) and watches the session
// until the command's bashExecution entry lands, then starts one turn. `!!` commands and
// commands typed while the agent is busy keep pi's behavior.
export default function userBashFollowUp(pi: ExtensionAPI): void {
  let timer: ReturnType<typeof setInterval> | undefined;

  const stop = (): void => {
    if (timer) clearInterval(timer);
    timer = undefined;
  };

  const recorded = (ctx: ExtensionContext, since: string | null, command: string) => {
    let id = ctx.sessionManager.getLeafId();
    while (id && id !== since) {
      const entry = ctx.sessionManager.getEntry(id);
      if (!entry) return undefined;
      if (entry.type === "message" && entry.message.role === "bashExecution" && entry.message.command === command) {
        return entry.message;
      }
      id = entry.parentId;
    }
    return undefined;
  };

  pi.on("user_bash", (event, ctx) => {
    stop();
    if (event.excludeFromContext || !ctx.isIdle()) return;
    const since = ctx.sessionManager.getLeafId();
    timer = setInterval(() => {
      const message = recorded(ctx, since, event.command);
      if (!message) return;
      stop();
      if (message.cancelled || !ctx.isIdle() || ctx.hasPendingMessages()) return;
      pi.sendMessage({ customType: FOLLOW_UP_TYPE, content: FOLLOW_UP_PROMPT, display: false }, { triggerTurn: true });
    }, POLL_MS);
  });
  pi.on("agent_start", () => stop());
  pi.on("session_start", () => stop());
  pi.on("session_shutdown", () => stop());
}

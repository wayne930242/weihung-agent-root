import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

export const COMPACTION_THRESHOLD = 300_000;

export default function idleCompaction(pi: ExtensionAPI): void {
  let compacting = false;
  let pending: ReturnType<typeof setTimeout> | undefined;

  const check = (ctx: ExtensionContext): void => {
    pending = undefined;
    if (compacting || !ctx.isIdle() || ctx.hasPendingMessages()) return;
    const tokens = ctx.getContextUsage()?.tokens;
    if (tokens === null || tokens === undefined || tokens <= COMPACTION_THRESHOLD) return;
    compacting = true;
    ctx.compact({
      onComplete: () => { compacting = false; },
      onError: () => { compacting = false; },
    });
  };

  const schedule = (ctx: ExtensionContext): void => {
    if (pending) clearTimeout(pending);
    pending = setTimeout(() => check(ctx), 100);
  };

  pi.on("session_start", (_event, ctx) => schedule(ctx));
  pi.on("agent_settled", (_event, ctx) => schedule(ctx));
  pi.on("session_shutdown", () => {
    if (pending) clearTimeout(pending);
    pending = undefined;
  });
}

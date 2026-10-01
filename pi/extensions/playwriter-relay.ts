import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn } from "node:child_process";

export const RELAY_URL = "http://127.0.0.1:19988";

export type RelayDeps = {
  fetch: typeof fetch;
  start: () => void;
  sleep: (ms: number) => Promise<void>;
};

const defaultDeps: RelayDeps = {
  fetch,
  // `serve` runs the relay inside the CLI at the CLI's own version, so later commands reuse it instead of restarting it.
  start: () => {
    const child = spawn("playwriter", ["serve", "--host", "127.0.0.1"], { detached: true, stdio: "ignore" });
    child.on("error", () => {});
    child.unref();
  },
  sleep: (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
};

async function relayUp(deps: RelayDeps): Promise<boolean> {
  try {
    return (await deps.fetch(`${RELAY_URL}/version`, { signal: AbortSignal.timeout(2000) })).ok;
  } catch {
    return false;
  }
}

async function extensionConnected(deps: RelayDeps): Promise<boolean> {
  try {
    const response = await deps.fetch(`${RELAY_URL}/extensions/status`, { signal: AbortSignal.timeout(2000) });
    if (!response.ok) return false;
    const { extensions } = (await response.json()) as { extensions: { stableKey?: string }[] };
    return extensions.some((extension) => !extension.stableKey?.startsWith("remote:"));
  } catch {
    return false;
  }
}

/** Returns a warning when the relay or the Chrome extension is unavailable, otherwise undefined. */
export async function ensureRelay(deps: RelayDeps = defaultDeps, attempts = 20, intervalMs = 500): Promise<string | undefined> {
  if (!(await relayUp(deps))) {
    deps.start();
    let up = false;
    for (let i = 0; i < attempts && !up; i++) {
      await deps.sleep(intervalMs);
      up = await relayUp(deps);
    }
    if (!up) return `Playwriter relay did not start on ${RELAY_URL}; run \`playwriter serve --host 127.0.0.1\` to see why.`;
  }
  for (let i = 0; i < attempts; i++) {
    if (await extensionConnected(deps)) return undefined;
    await deps.sleep(intervalMs);
  }
  return "Playwriter relay is running but the Chrome extension is not connected; open Chrome, or reload the Playwriter extension at chrome://extensions.";
}

export default function playwriterRelay(pi: ExtensionAPI, deps: RelayDeps = defaultDeps): void {
  // A session that ends before the check settles leaves ctx stale, and pi throws on any access; nobody is left to warn.
  let ended = false;
  pi.on("session_shutdown", () => { ended = true; });
  pi.on("session_start", (_event, ctx) => {
    ended = false;
    // Session start must not wait on Chrome; the warning arrives when the check settles.
    void ensureRelay(deps).then((warning) => {
      if (warning && !ended && ctx.hasUI) ctx.ui.notify(warning, "warning");
    });
  });
}

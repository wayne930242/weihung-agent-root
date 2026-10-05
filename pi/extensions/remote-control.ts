import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFile } from "node:child_process";
import { readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

// herdr web ui (the devswha.herdr-web-ui herdr plugin) is the remote control: herdr starts it with
// itself on 127.0.0.1, and Tailscale publishes it to the tailnet on 8443 because 443 belongs to the
// user's notes.
export const PLUGIN_ID = "devswha.herdr-web-ui";
export const APP_URL = "http://127.0.0.1:7317";
export const HTTPS_PORT = 8443;

export type RemoteDeps = {
  fetch: typeof fetch;
  run: (command: string, args: string[]) => Promise<string>;
  pluginScript: () => string | undefined;
  sleep: (ms: number) => Promise<void>;
};

const defaultDeps: RemoteDeps = {
  fetch,
  run: (command, args) =>
    new Promise((resolve, reject) => {
      execFile(command, args, { timeout: 30_000, maxBuffer: 1 << 20 }, (error, stdout, stderr) => {
        if (error) reject(new Error(`${command} ${args.join(" ")}: ${stderr.trim() || error.message}`));
        else resolve(stdout);
      });
    }),
  pluginScript: () => {
    const root = join(homedir(), ".config", "herdr", "plugins", "github");
    try {
      const dir = readdirSync(root).find((name) => name.startsWith(`${PLUGIN_ID}-`));
      return dir === undefined ? undefined : join(root, dir, "scripts", "plugin.ts");
    } catch {
      return undefined;
    }
  },
  sleep: (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
};

async function appUp(deps: RemoteDeps): Promise<boolean> {
  try {
    const response = await deps.fetch(`${APP_URL}/api/health`, { signal: AbortSignal.timeout(1500) });
    // the port may hold another program's 200: only the app's own answer counts
    return response.ok && ((await response.json()) as { ok?: unknown }).ok === true;
  } catch {
    return false;
  }
}

async function served(deps: RemoteDeps): Promise<boolean> {
  const status = JSON.parse(await deps.run("tailscale", ["serve", "status", "--json"])) as {
    Web?: Record<string, { Handlers?: Record<string, { Proxy?: string }> }>;
  };
  return Object.entries(status.Web ?? {}).some(
    ([host, web]) => host.endsWith(`:${HTTPS_PORT}`) && web.Handlers?.["/"]?.Proxy === APP_URL,
  );
}

/** Brings the app up and publishes it on the tailnet; returns a problem, or undefined when both hold. */
export async function ensureRemote(deps: RemoteDeps = defaultDeps, attempts = 20, intervalMs = 500): Promise<string | undefined> {
  if (!(await appUp(deps))) {
    try {
      await deps.run("herdr", ["plugin", "action", "invoke", `${PLUGIN_ID}.start`]);
    } catch (error) {
      return `herdr web ui did not start: ${(error as Error).message}`;
    }
    let up = false;
    for (let i = 0; i < attempts && !up; i++) {
      await deps.sleep(intervalMs);
      up = await appUp(deps);
    }
    if (!up) return `herdr web ui is not answering on ${APP_URL}; check \`herdr plugin log list\`.`;
  }
  try {
    if (!(await served(deps))) await deps.run("tailscale", ["serve", "--bg", `--https=${HTTPS_PORT}`, APP_URL]);
  } catch (error) {
    return `Tailscale does not serve herdr web ui on ${HTTPS_PORT}: ${(error as Error).message}`;
  }
  return undefined;
}

/** The plugin's own `phone` (address and QR) or `pair` (pairing code and QR) output. */
export async function remoteReport(mode: "phone" | "pair", deps: RemoteDeps = defaultDeps): Promise<string> {
  const problem = await ensureRemote(deps);
  if (problem !== undefined) throw new Error(problem);
  const script = deps.pluginScript();
  if (script === undefined) throw new Error(`the ${PLUGIN_ID} herdr plugin is not installed; run \`herdr plugin install devswha/herdr-web-ui --yes\`.`);
  return deps.run("bun", [script, mode]);
}

export default function remoteControl(pi: ExtensionAPI, deps: RemoteDeps = defaultDeps): void {
  let ended = false;
  pi.on("session_shutdown", () => { ended = true; });
  pi.on("session_start", (_event, ctx) => {
    ended = false;
    void ensureRemote(deps).then((problem) => {
      if (problem && !ended && ctx.hasUI) ctx.ui.notify(problem, "warning");
    });
  });

  pi.registerCommand("rc", {
    description: "Show the herdr web ui remote-control address as a QR code (`/rc pair` for a pairing code)",
    getArgumentCompletions: (prefix) => ("pair".startsWith(prefix) ? [{ value: "pair", label: "pair" }] : null),
    handler: async (args, ctx) => {
      const mode = args.trim() === "pair" ? "pair" : "phone";
      let report: string;
      try {
        report = await remoteReport(mode, deps);
      } catch (error) {
        ctx.ui.notify((error as Error).message, "error");
        return;
      }
      if (!ctx.hasUI) return;
      // An overlay keeps the QR, and a pairing code, out of the conversation the model reads.
      const lines = [...report.trimEnd().split("\n"), "", "Esc or Enter to close"];
      await ctx.ui.custom<void>((_tui, _theme, _keys, done) => ({
        // plain text without escapes, so a slice is a safe cut to the overlay's width
        render: (width) => lines.map((line) => [...line].slice(0, width).join("")),
        invalidate: () => {},
        handleInput: (data) => {
          if (data === "\x1b" || data === "\r" || data === "\n") done();
        },
      }));
    },
  });
}

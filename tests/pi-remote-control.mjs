import assert from "node:assert/strict";
import { APP_URL, ensureRemote, remoteReport } from "../pi/extensions/remote-control.ts";

const servedOn = (port, proxy = APP_URL) =>
  JSON.stringify({ Web: { [`host.ts.net:${port}`]: { Handlers: { "/": { Proxy: proxy } } } } });

function fake({ up = true, startWorks = true, serve = servedOn(8443), script = "/plugin/scripts/plugin.ts" } = {}) {
  let running = up;
  const calls = [];
  const deps = {
    fetch: async (url) => {
      assert.equal(url, `${APP_URL}/api/health`);
      if (!running) throw new Error("ECONNREFUSED");
      return { ok: true, json: async () => ({ ok: true }) };
    },
    run: async (command, args) => {
      calls.push([command, ...args].join(" "));
      if (command === "herdr") {
        if (!startWorks) throw new Error("herdr: no server");
        running = true;
        return "";
      }
      if (command === "tailscale" && args[1] === "status") return serve;
      if (command === "bun") return `report ${args[1]}\n`;
      return "";
    },
    pluginScript: () => script ?? undefined,
    sleep: async () => {},
  };
  return { deps, calls };
}

let run = fake();
assert.equal(await ensureRemote(run.deps, 3, 0), undefined, "a running, served app is healthy");
assert.deepEqual(run.calls, ["tailscale serve status --json"], "a running, served app is left alone");

run = fake({ up: false });
assert.equal(await ensureRemote(run.deps, 3, 0), undefined, "a stopped app is started");
assert.equal(run.calls[0], "herdr plugin action invoke devswha.herdr-web-ui.start");

run = fake({ up: false, startWorks: false });
assert.match(await ensureRemote(run.deps, 3, 0), /did not start: herdr: no server/, "a failed start is reported");

run = fake({ serve: servedOn(443, "http://localhost:60132") });
assert.equal(await ensureRemote(run.deps, 3, 0), undefined);
assert.equal(run.calls.at(-1), "tailscale serve --bg --https=8443 http://127.0.0.1:7317", "a missing serve is added on 8443, leaving 443 alone");

run = fake({ serve: "{}" });
await ensureRemote(run.deps, 3, 0);
assert.equal(run.calls.at(-1), "tailscale serve --bg --https=8443 http://127.0.0.1:7317", "an empty serve config gets 8443");

run = fake();
assert.equal(await remoteReport("phone", run.deps), "report phone\n", "/rc shows the plugin's phone report");
assert.equal(await remoteReport("pair", run.deps), "report pair\n", "/rc pair shows the plugin's pairing report");
assert.equal(run.calls.at(-1), "bun /plugin/scripts/plugin.ts pair");

run = fake({ script: null });
await assert.rejects(remoteReport("phone", run.deps), /not installed/, "a missing plugin is reported");

run = fake({ up: false, startWorks: false });
await assert.rejects(remoteReport("phone", run.deps), /did not start/, "a report needs a running app");

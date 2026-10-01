import assert from "node:assert/strict";
import playwriterRelay, { ensureRelay, RELAY_URL } from "../pi/extensions/playwriter-relay.ts";

const json = (body) => ({ ok: true, json: async () => body });
const local = { extensions: [{ stableKey: "install:Chrome:abc" }] };
const remoteOnly = { extensions: [{ stableKey: "remote:xyz" }] };

function fake({ upAfterStart = true, initiallyUp = false, status = local } = {}) {
  let up = initiallyUp;
  const calls = { start: 0 };
  const deps = {
    fetch: async (url) => {
      if (!up) throw new Error("ECONNREFUSED");
      if (url === `${RELAY_URL}/version`) return json({ version: "0.7.0" });
      if (url === `${RELAY_URL}/extensions/status`) return json(status);
      throw new Error(`unexpected ${url}`);
    },
    start: () => { calls.start++; up = upAfterStart; },
    sleep: async () => {},
  };
  return { deps, calls };
}

let run = fake({ initiallyUp: true });
assert.equal(await ensureRelay(run.deps, 3, 0), undefined, "running relay with a connected extension is healthy");
assert.equal(run.calls.start, 0, "a running relay is not restarted");

run = fake();
assert.equal(await ensureRelay(run.deps, 3, 0), undefined, "a stopped relay is started");
assert.equal(run.calls.start, 1);

run = fake({ upAfterStart: false });
assert.match(await ensureRelay(run.deps, 3, 0), /did not start/, "a relay that never answers is reported");

run = fake({ initiallyUp: true, status: { extensions: [] } });
assert.match(await ensureRelay(run.deps, 3, 0), /extension is not connected/, "a missing extension is reported");

run = fake({ initiallyUp: true, status: remoteOnly });
assert.match(await ensureRelay(run.deps, 3, 0), /extension is not connected/, "a remote-control tunnel is not the local extension");

const handlers = new Map();
let release;
const gate = new Promise((resolve) => { release = resolve; });
run = fake({ initiallyUp: true, status: { extensions: [] } });
const notices = [];
playwriterRelay({ on(event, handler) { handlers.set(event, handler); } }, { ...run.deps, sleep: () => gate });
const returned = handlers.get("session_start")({}, { hasUI: true, ui: { notify: (message, level) => notices.push([message, level]) } });
assert.equal(returned, undefined, "session start does not wait for the relay check");
assert.equal(notices.length, 0);
release();
await new Promise((resolve) => setTimeout(resolve, 20));
assert.equal(notices.length, 1, "the warning arrives after the check settles");
assert.equal(notices[0][1], "warning");

// The check settles after the session shut down: pi's stale ctx throws on every access.
const staleHandlers = new Map();
let releaseStale;
const staleGate = new Promise((resolve) => { releaseStale = resolve; });
run = fake({ initiallyUp: true, status: { extensions: [] } });
playwriterRelay({ on(event, handler) { staleHandlers.set(event, handler); } }, { ...run.deps, sleep: () => staleGate });
let shutDown = false;
const staleError = () => new Error("This extension ctx is stale after session replacement or reload.");
staleHandlers.get("session_start")({}, {
  get hasUI() { if (shutDown) throw staleError(); return true; },
  get ui() { if (shutDown) throw staleError(); return { notify: () => {} }; },
});
shutDown = true;
const unhandled = [];
const onUnhandled = (error) => unhandled.push(error);
process.on("unhandledRejection", onUnhandled);
releaseStale();
await new Promise((resolve) => setTimeout(resolve, 20));
process.off("unhandledRejection", onUnhandled);
assert.deepEqual(unhandled, [], "a stale ctx after shutdown does not throw");

console.log("pi playwriter relay: pass");

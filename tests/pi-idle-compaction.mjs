import assert from "node:assert/strict";
import idleCompaction, { COMPACTION_THRESHOLD } from "../pi/extensions/idle-compaction.ts";

const handlers = new Map();
idleCompaction({ on(event, handler) { handlers.set(event, handler); } });

let idle = false;
let pending = false;
let tokens = COMPACTION_THRESHOLD + 1;
const calls = [];
const ctx = {
  isIdle: () => idle,
  hasPendingMessages: () => pending,
  getContextUsage: () => ({ tokens, contextWindow: 1_000_000 }),
  compact: (options) => calls.push(options),
};
const wait = () => new Promise((resolve) => setTimeout(resolve, 130));

handlers.get("agent_end")?.({}, ctx);
await wait();
assert.equal(calls.length, 0, "active turn must not compact");

idle = true;
handlers.get("agent_settled")({}, ctx);
await wait();
assert.equal(calls.length, 1, "settled turn compacts after agent_end has passed");
calls[0].onComplete({});

tokens = COMPACTION_THRESHOLD;
handlers.get("agent_settled")({}, ctx);
await wait();
assert.equal(calls.length, 1, "threshold is exclusive");

tokens++;
pending = true;
handlers.get("agent_settled")({}, ctx);
await wait();
assert.equal(calls.length, 1, "queued user message must finish first");

pending = false;
handlers.get("agent_settled")({}, ctx);
await wait();
assert.equal(calls.length, 2, "idle session above threshold compacts");
handlers.get("agent_settled")({}, ctx);
await wait();
assert.equal(calls.length, 2, "one compaction at a time");

calls[1].onComplete({});
tokens = null;
handlers.get("session_start")({}, ctx);
await wait();
assert.equal(calls.length, 2, "unknown usage after compaction does not retrigger");

tokens = COMPACTION_THRESHOLD + 1;
handlers.get("session_start")({}, ctx);
await wait();
assert.equal(calls.length, 3, "resumed idle session above threshold compacts");
calls[2].onError(new Error("test failure"));

handlers.get("session_shutdown")({}, ctx);
console.log("pi idle compaction: pass");

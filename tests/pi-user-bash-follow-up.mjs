import assert from "node:assert/strict";
import userBashFollowUp, { FOLLOW_UP_TYPE, POLL_MS } from "../pi/extensions/user-bash-follow-up.ts";

const handlers = new Map();
const sent = [];
userBashFollowUp({
  on(event, handler) { handlers.set(event, handler); },
  sendMessage(message, options) { sent.push({ message, options }); },
});

const entries = new Map();
let leaf = "root";
entries.set("root", { id: "root", parentId: null, type: "message", message: { role: "user" } });
let idle = true;
let pending = false;
let next = 0;
const ctx = {
  isIdle: () => idle,
  hasPendingMessages: () => pending,
  sessionManager: { getLeafId: () => leaf, getEntry: (id) => entries.get(id) },
};
const append = (entry) => {
  const id = `e${next++}`;
  entries.set(id, { id, parentId: leaf, ...entry });
  leaf = id;
};
const recordBash = (command, extra = {}) =>
  append({ type: "message", message: { role: "bashExecution", command, output: "ok", exitCode: 0, cancelled: false, ...extra } });
const wait = () => new Promise((resolve) => setTimeout(resolve, POLL_MS * 2 + 30));
const bash = (command, excludeFromContext = false) =>
  handlers.get("user_bash")({ type: "user_bash", command, excludeFromContext, cwd: "/" }, ctx);

bash("git status");
await wait();
assert.equal(sent.length, 0, "no turn before the output is recorded");
append({ type: "custom", customType: "other" });
recordBash("git status");
await wait();
assert.equal(sent.length, 1, "recorded `!` output starts one turn");
assert.equal(sent[0].message.customType, FOLLOW_UP_TYPE);
assert.equal(sent[0].message.display, false);
assert.deepEqual(sent[0].options, { triggerTurn: true });
await wait();
assert.equal(sent.length, 1, "one turn per command");

bash("ls", true);
recordBash("ls", { excludeFromContext: true });
await wait();
assert.equal(sent.length, 1, "`!!` starts no turn");

idle = false;
bash("pwd");
recordBash("pwd");
await wait();
assert.equal(sent.length, 1, "a command typed during a turn keeps pi's deferred behavior");
idle = true;

bash("sleep 9");
recordBash("sleep 9", { cancelled: true });
await wait();
assert.equal(sent.length, 1, "a cancelled command starts no turn");

bash("make");
handlers.get("agent_start")({}, ctx);
recordBash("make");
await wait();
assert.equal(sent.length, 1, "a prompt that started a turn meanwhile wins");

bash("make");
pending = true;
recordBash("make");
await wait();
assert.equal(sent.length, 1, "queued messages go first");
pending = false;

bash("npm test");
handlers.get("session_shutdown")({}, ctx);
recordBash("npm test");
await wait();
assert.equal(sent.length, 1, "shutdown stops watching");

console.log("pi user bash follow-up: pass");

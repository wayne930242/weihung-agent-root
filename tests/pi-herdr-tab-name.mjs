import assert from "node:assert/strict";
import herdrTabName, { MAX_LABEL_CHARS, shortLabel } from "../pi/extensions/herdr-tab-name.ts";

function harness({ label = "1", sessionName, branch = [], env = { HERDR_PANE_ID: "w1:p1" } } = {}) {
  const saved = { HERDR_PANE_ID: process.env.HERDR_PANE_ID, PI_SUBAGENT_ID: process.env.PI_SUBAGENT_ID };
  delete process.env.HERDR_PANE_ID;
  delete process.env.PI_SUBAGENT_ID;
  Object.assign(process.env, env);
  const state = { label, renames: [] };
  const run = async (args) => {
    const [kind, verb, id, ...rest] = args;
    if (kind === "pane" && verb === "get") return JSON.stringify({ result: { pane: { pane_id: id, tab_id: "w1:t1" } } });
    if (kind === "tab" && verb === "get") return JSON.stringify({ result: { tab: { tab_id: id, label: state.label } } });
    if (kind === "tab" && verb === "rename") {
      state.label = rest.join(" ");
      state.renames.push(state.label);
      return "";
    }
    throw new Error(`unexpected ${args.join(" ")}`);
  };
  const handlers = new Map();
  const pi = { on: (event, handler) => handlers.set(event, handler), getSessionName: () => sessionName };
  herdrTabName(pi, run);
  for (const [key, value] of Object.entries(saved)) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  const ctx = { sessionManager: { getBranch: () => branch } };
  const fire = async (event, payload = {}) => {
    handlers.get(event)?.(payload, ctx);
    await new Promise((resolve) => setTimeout(resolve, 10));
  };
  return { state, handlers, fire, setName: (name) => { sessionName = name; } };
}

const user = (content) => ({ type: "message", message: { role: "user", content } });

assert.equal(shortLabel("  fix   the\nparser "), "fix the parser");
assert.equal(shortLabel("pi 有辦法 herdr 加上 auto tab name 嗎"), `${Array.from("pi 有辦法 herdr 加上 auto tab name 嗎").slice(0, MAX_LABEL_CHARS).join("").trimEnd()}…`);

let h = harness();
await h.fire("session_start");
assert.deepEqual(h.state.renames, [], "a fresh session with no name or message leaves the tab alone");
await h.fire("before_agent_start", { prompt: "權限遷移" });
assert.deepEqual(h.state.renames, ["權限遷移"], "the first prompt names a numbered tab");

h = harness({ branch: [user([{ type: "text", text: "修 PDF 縮圖" }])] });
await h.fire("before_agent_start", { prompt: "later prompt" });
assert.deepEqual(h.state.renames, ["修 PDF 縮圖"], "the first user message wins over later prompts");

h = harness({ sessionName: "mp-3464", branch: [user("ignored")] });
await h.fire("session_start");
assert.deepEqual(h.state.renames, ["mp-3464"], "a session name wins over the first message");

h = harness({ branch: [user("first task")] });
await h.fire("session_start");
await h.fire("session_info_changed", { name: "renamed" });
assert.deepEqual(h.state.renames, ["first task", "renamed"], "a label this session set follows session renames");
await h.fire("session_info_changed", { name: undefined });
assert.equal(h.state.label, "first task", "clearing the name falls back to the first message");

h = harness({ label: "Agents", branch: [user("task")] });
await h.fire("session_start");
assert.deepEqual(h.state.renames, [], "a tab named by someone else is left alone");

h = harness({ branch: [user("task")] });
await h.fire("session_start");
h.state.label = "dispatch-slug";
await h.fire("session_info_changed", { name: "new name" });
assert.equal(h.state.label, "dispatch-slug", "a manual or straw-boss rename after ours is respected");

h = harness({ env: { HERDR_PANE_ID: "w1:p1", PI_SUBAGENT_ID: "abc" }, branch: [user("task")] });
assert.equal(h.handlers.size, 0, "a subagent registers nothing");

h = harness({ env: {}, branch: [user("task")] });
assert.equal(h.handlers.size, 0, "outside Herdr nothing registers");

let calls = 0;
const failing = { on: (event, handler) => failing.handlers.set(event, handler), handlers: new Map(), getSessionName: () => "x" };
process.env.HERDR_PANE_ID = "w1:p1";
herdrTabName(failing, async () => { calls++; throw new Error("herdr down"); });
delete process.env.HERDR_PANE_ID;
failing.handlers.get("session_start")({}, { sessionManager: { getBranch: () => [] } });
await new Promise((resolve) => setTimeout(resolve, 10));
assert.equal(calls, 1, "a herdr failure is swallowed after one attempt");

console.log("herdr-tab-name ok");

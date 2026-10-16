import assert from "node:assert/strict";
import { test } from "node:test";
import { createAutoThinking, preprocessPrompt } from "../pi/extensions/auto-thinking.ts";

function harness(classify, { isSubagent = false, solutionSpace } = {}) {
  const handlers = new Map();
  const commands = new Map();
  const state = { level: "medium", statuses: [], notices: [], prompts: [] };
  createAutoThinking(classify, { isSubagent, solutionSpace })({
    on: (event, fn) => handlers.set(event, fn),
    registerCommand: (name, options) => commands.set(name, options),
    setThinkingLevel: (level) => { state.level = level === "max" ? "xhigh" : level; },
    getThinkingLevel: () => state.level,
  });
  const ctx = {
    ui: {
      setStatus: (_key, text) => state.statuses.push(text),
      notify: (message, level) => state.notices.push({ message, level }),
    },
  };
  const prompt = (text) => handlers.get("before_agent_start")({ type: "before_agent_start", messageType: "user", prompt: text }, ctx);
  const custom = () => handlers.get("before_agent_start")({ type: "before_agent_start", messageType: "custom", message: { role: "custom" } }, ctx);
  const select = (level) => handlers.get("thinking_level_select")({ level, previousLevel: state.level }, ctx);
  const command = (args) => commands.get("auto-thinking").handler(args, ctx);
  return { handlers, state, prompt, custom, select, command };
}

test("classified level becomes the thinking level", async () => {
  const seen = [];
  const h = harness(async (input) => { seen.push(input); return "xhigh"; });
  await h.prompt("diagnose an intermittent deadlock");
  assert.equal(h.state.level, "xhigh");
  assert.deepEqual(seen, [{ request: "diagnose an intermittent deadlock" }]);
  assert.equal(h.state.statuses.at(-1), "auto:xhigh");
});

test("ultrathink skips the classifier and asks for max", async () => {
  const h = harness(async () => { throw new Error("must not classify"); });
  await h.prompt("ultrathink about this migration");
  assert.equal(h.state.level, "xhigh");
});

test("failure keeps the last classified level and warns", async () => {
  let fail = false;
  const h = harness(async () => { if (fail) throw new Error("timeout"); return "high"; });
  await h.prompt("pick an API shape");
  fail = true;
  h.state.level = "low";
  await h.prompt("rename a constant");
  assert.equal(h.state.level, "high");
  assert.match(h.state.notices.at(-1).message, /kept high: timeout/);
});

test("failure before any classification leaves the level unchanged", async () => {
  const h = harness(async () => { throw new Error("no key"); });
  await h.prompt("anything");
  assert.equal(h.state.level, "medium");
  assert.match(h.state.notices.at(-1).message, /level unchanged: no key/);
});

test("a run started by a custom message keeps the level without classifying", async () => {
  let calls = 0;
  const h = harness(async () => { calls++; return "high"; });
  await h.prompt("pick an API shape");
  h.state.level = "low";
  await h.custom();
  assert.equal(calls, 1);
  assert.equal(h.state.level, "low");
  assert.equal(h.state.notices.length, 0);
});

test("manual level change turns auto off until /auto-thinking on", async () => {
  let calls = 0;
  const h = harness(async () => { calls++; return "low"; });
  await h.prompt("rename");
  await h.select("low");
  assert.equal(h.state.notices.length, 0, "its own level change is not manual");
  await h.select("high");
  assert.match(h.state.notices.at(-1).message, /auto-thinking off/);
  await h.prompt("rename again");
  assert.equal(calls, 1);
  await h.command("on");
  await h.prompt("rename once more");
  assert.equal(calls, 2);
});

test("subagents without a solution space register nothing", () => {
  const h = harness(async () => "low", { isSubagent: true });
  assert.equal(h.handlers.size, 0);
});

test("a subagent classifies its solution space once, not its task", async () => {
  const seen = [];
  const h = harness(async (input) => { seen.push(input); return "high"; },
    { isSubagent: true, solutionSpace: "Cause known; the fix needs one API choice." });
  await h.prompt("a long task text that must not be classified");
  await h.prompt("a follow-up task");
  assert.equal(h.state.level, "high");
  assert.deepEqual(seen, [{ solutionSpace: "Cause known; the fix needs one API choice." }]);
  assert.deepEqual([...h.handlers.keys()], ["before_agent_start"]);
});

test("a failed solution space classification keeps the dispatcher's level", async () => {
  const h = harness(async () => { throw new Error("no key"); }, { isSubagent: true, solutionSpace: "Open cause." });
  await h.prompt("task");
  assert.equal(h.state.level, "medium");
  assert.match(h.state.notices.at(-1).message, /level unchanged: no key/);
});

test("prompt cleanup strips code, tags, hashes and bounds length", () => {
  const cleaned = preprocessPrompt("fix bug in 0123456789abcdef0123 <ctx>noise</ctx>\n```\ncode\n```\nplease");
  assert.equal(cleaned, "fix bug in 0123456 \n \nplease");
  assert.ok(preprocessPrompt("x".repeat(10_000)).length <= 2000);
});

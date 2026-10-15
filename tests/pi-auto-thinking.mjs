import assert from "node:assert/strict";
import { test } from "node:test";
import { createAutoThinking, preprocessPrompt } from "../pi/extensions/auto-thinking.ts";

function harness(classify, { isSubagent = false } = {}) {
  const handlers = new Map();
  const commands = new Map();
  const state = { level: "medium", statuses: [], notices: [], prompts: [] };
  createAutoThinking(classify, isSubagent)({
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
  const prompt = (text) => handlers.get("before_agent_start")({ prompt: text }, ctx);
  const select = (level) => handlers.get("thinking_level_select")({ level, previousLevel: state.level }, ctx);
  const command = (args) => commands.get("auto-thinking").handler(args, ctx);
  return { handlers, state, prompt, select, command };
}

test("classified level becomes the thinking level", async () => {
  const seen = [];
  const h = harness(async (request) => { seen.push(request); return "xhigh"; });
  await h.prompt("diagnose an intermittent deadlock");
  assert.equal(h.state.level, "xhigh");
  assert.deepEqual(seen, ["diagnose an intermittent deadlock"]);
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

test("subagents register nothing", () => {
  const h = harness(async () => "low", { isSubagent: true });
  assert.equal(h.handlers.size, 0);
});

test("prompt cleanup strips code, tags, hashes and bounds length", () => {
  const cleaned = preprocessPrompt("fix bug in 0123456789abcdef0123 <ctx>noise</ctx>\n```\ncode\n```\nplease");
  assert.equal(cleaned, "fix bug in 0123456 \n \nplease");
  assert.ok(preprocessPrompt("x".repeat(10_000)).length <= 2000);
});

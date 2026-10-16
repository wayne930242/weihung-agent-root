import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import quotaResume, {
  EXIT_HOLD_CHANNEL,
  MAX_WAIT_MS,
  RESUME_MARGIN_MS,
  RESUME_PROMPT,
  quotaResumeAt,
} from "../pi/extensions/quota-resume.ts";

const HOUR = 60 * 60 * 1000;
const now = new Date(2026, 9, 16, 15, 0, 0).getTime();
const error = (errorMessage, extra = {}) => ({ role: "assistant", stopReason: "error", errorMessage, timestamp: now, ...extra });
const fiveHour = (clock) => error(`Claude quota exceeded — rate limit (five_hour) — resets ${clock}: You've hit your session limit · resets 8pm (Asia/Taipei)`);

// Decision
assert.equal(quotaResumeAt(fiveHour("8:00:00 PM"), undefined, now), now + 5 * HOUR + RESUME_MARGIN_MS, "parses the bridge's clock time");
assert.equal(quotaResumeAt(error("You've hit your session limit · resets 3:30am"), undefined, now), undefined, "12.5h away is beyond the wait limit");
assert.equal(quotaResumeAt(fiveHour("3:30:00 PM"), undefined, now), now + 30 * 60 * 1000 + RESUME_MARGIN_MS, "same-day reset");
assert.equal(quotaResumeAt(fiveHour("2:00:00 PM"), undefined, now), undefined, "a passed clock time means tomorrow, beyond the limit");
assert.equal(quotaResumeAt(error("Claude quota exceeded — rate limit (seven_day) — resets 4:00:00 PM: weekly"), undefined, now), undefined, "a clock time without a date never identifies a seven-day reset");
assert.equal(quotaResumeAt(error("Claude quota exceeded — rate limit (seven_day)"), now + 2 * HOUR, now), now + 2 * HOUR + RESUME_MARGIN_MS, "an exact provider reset is trusted for any window");
assert.equal(quotaResumeAt(error("Claude quota exceeded — rate limit (seven_day)"), now + MAX_WAIT_MS + 1, now), undefined, "exact reset beyond the limit");
assert.equal(quotaResumeAt(error("provider failed"), now + HOUR, now), undefined, "only quota errors wait");
assert.equal(quotaResumeAt({ role: "assistant", stopReason: "stop" }, now + HOUR, now), undefined, "completed turns never wait");
assert.equal(quotaResumeAt(error("Claude rate limit (five_hour)"), undefined, now), undefined, "no reset time, no wait");

// Lifecycle
function harness() {
  const handlers = new Map();
  const commands = new Map();
  const bus = new EventEmitter();
  const sent = [];
  const status = new Map();
  const notices = [];
  let polls = [];
  const state = { now, idle: true, signal: undefined, touched: 0, branch: [] };
  const pi = {
    on: (event, handler) => handlers.set(event, handler),
    events: { emit: (channel, data) => bus.emit(channel, data), on: (channel, handler) => bus.on(channel, handler) },
    registerCommand: (name, command) => commands.set(name, command),
    sendUserMessage: (message) => sent.push(message),
  };
  const deps = {
    now: () => state.now,
    signalMtime: () => state.signal,
    touchSignal: () => { state.touched++; state.signal = state.now; },
    setInterval: (callback) => { const handle = { callback }; polls.push(handle); return handle; },
    clearInterval: (handle) => { polls = polls.filter((poll) => poll !== handle); },
  };
  const ctx = {
    isIdle: () => state.idle,
    sessionManager: { getBranch: () => state.branch.map((message) => ({ type: "message", message })) },
    ui: { setStatus: (key, text) => status.set(key, text), notify: (text) => notices.push(text) },
  };
  quotaResume(pi, deps);
  const tick = () => polls.forEach((poll) => poll.callback());
  const hold = (messages) => { const probe = { messages, hold: false }; pi.events.emit(EXIT_HOLD_CHANNEL, probe); return probe.hold; };
  return { handlers, commands, sent, status, notices, state, ctx, tick, hold, polls: () => polls };
}

{
  const h = harness();
  const quota = fiveHour("4:00:00 PM");
  assert.equal(h.hold([quota]), true, "holds a child's exit on a quota error that resets soon");
  assert.equal(h.hold([fiveHour("2:00:00 PM")]), false, "does not hold beyond the wait limit");
  assert.equal(h.hold([error("provider failed")]), false, "does not hold other errors");

  h.state.branch = [quota];
  h.handlers.get("agent_settled")({ aborted: false }, h.ctx);
  assert.equal(h.polls().length, 1, "waiting starts");
  assert.match(h.status.get("quota-resume"), /resuming at/);
  h.tick();
  assert.deepEqual(h.sent, [], "nothing before the reset");
  h.state.now = now + HOUR + RESUME_MARGIN_MS;
  h.tick();
  assert.deepEqual(h.sent, [RESUME_PROMPT], "resumes after the reset plus margin");
  assert.equal(h.status.get("quota-resume"), undefined, "status cleared");
  assert.equal(h.polls().length, 0, "polling stopped");
}

{
  const h = harness();
  h.state.branch = [fiveHour("4:00:00 PM")];
  h.handlers.get("agent_settled")({ aborted: false }, h.ctx);
  h.state.now += 1000;
  h.state.signal = h.state.now;
  h.tick();
  assert.deepEqual(h.sent, [RESUME_PROMPT], "another session's /quota-resume wakes this one");
}

{
  const h = harness();
  h.state.signal = now - 1000;
  h.state.branch = [fiveHour("4:00:00 PM")];
  h.handlers.get("agent_settled")({ aborted: false }, h.ctx);
  h.tick();
  assert.deepEqual(h.sent, [], "a signal older than the wait is ignored");
  h.state.now += 1000;
  await h.commands.get("quota-resume").handler("", h.ctx);
  assert.equal(h.state.touched, 1, "the command broadcasts");
  assert.deepEqual(h.sent, [RESUME_PROMPT], "the command resumes its own session at once");
}

{
  const h = harness();
  h.state.branch = [fiveHour("4:00:00 PM")];
  h.handlers.get("agent_settled")({ aborted: false }, h.ctx);
  h.handlers.get("agent_start")({}, h.ctx);
  h.state.now = now + 2 * HOUR;
  h.tick();
  assert.deepEqual(h.sent, [], "a run started meanwhile cancels the wait");

  h.handlers.get("agent_settled")({ aborted: true }, h.ctx);
  assert.equal(h.polls().length, 0, "an aborted run never waits");

  h.handlers.get("after_provider_response")({ status: 200, headers: { "anthropic-ratelimit-unified-status": "rejected", "anthropic-ratelimit-unified-reset": String((h.state.now + HOUR) / 1000) } }, h.ctx);
  h.state.branch = [error("Claude quota exceeded — rate limit (seven_day)")];
  h.handlers.get("agent_settled")({ aborted: false }, h.ctx);
  assert.equal(h.polls().length, 1, "the provider's exact reset lets any window wait");
  h.state.idle = false;
  h.state.now += HOUR + RESUME_MARGIN_MS;
  h.tick();
  assert.deepEqual(h.sent, [], "a busy session is not interrupted");
  assert.equal(h.polls().length, 0);

  await h.commands.get("quota-resume").handler("", h.ctx);
  assert.match(h.notices.at(-1), /Signalled every session/);
}

console.log("pi quota resume: pass");

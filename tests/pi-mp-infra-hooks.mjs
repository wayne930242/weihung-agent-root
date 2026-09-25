import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { rmSync } from "node:fs";

const home = mkdtempSync(join(tmpdir(), "pi-mp-hooks-"));
try {
  const agent = join(home, ".pi", "agent");
  mkdirSync(agent, { recursive: true });
  const root = resolve("../moldplan-center/plugins/waydosoft-marketplace/plugins/mp-infra");
  writeFileSync(join(agent, "mp-infra.json"), JSON.stringify({ root }));
  process.env.PI_CODING_AGENT_DIR = agent;
  const { default: extension } = await import("../pi/extensions/mp-infra-hooks.ts");
  const absent = new Map();
  const { renameSync } = await import("node:fs");
  renameSync(join(agent, "mp-infra.json"), join(agent, "mp-infra.json.hold"));
  extension({ on(name, handler) { absent.set(name, handler); }, sendMessage() {} });
  assert.equal(absent.size, 0, "without mp-infra.json the extension registers no hooks");
  renameSync(join(agent, "mp-infra.json.hold"), join(agent, "mp-infra.json"));
  const handlers = new Map();
  const messages = [];
  extension({ on(name, handler) { handlers.set(name, handler); }, sendMessage(message) { messages.push(message); } });
  const ctx = { cwd: home, hasUI: false, ui: { notify() {} } };
  const blocked = await handlers.get("tool_call")({ toolName: "bash", input: { command: "DROP DATABASE example" } }, ctx);
  assert.equal(blocked.block, true);
  assert.match(blocked.reason, /DROP DATABASE/);
  const harmless = await handlers.get("tool_call")({ toolName: "bash", input: { command: "echo hello" } }, ctx);
  assert.equal(harmless, undefined);
  const review = await handlers.get("tool_call")({ toolName: "bash", input: { command: "git reset --hard" } }, ctx);
  assert.equal(review.block, true);

  const fake = join(home, "fake-mp-infra");
  mkdirSync(join(fake, "hooks"), { recursive: true });
  writeFileSync(join(fake, "hooks", "production-safety-hook"), "import os, sys\nsys.stdout.write(os.environ.get('FAKE_GATE_STDOUT', ''))\n");
  writeFileSync(join(agent, "mp-infra.json"), JSON.stringify({ root: fake }));
  process.env.FAKE_GATE_STDOUT = "";
  assert.equal(await handlers.get("tool_call")({ toolName: "bash", input: { command: "echo empty" } }, ctx), undefined);
  process.env.FAKE_GATE_STDOUT = "Traceback: not json";
  const malformed = await handlers.get("tool_call")({ toolName: "bash", input: { command: "echo malformed" } }, ctx);
  assert.equal(malformed.block, true);
  assert.match(malformed.reason, /malformed output: Traceback: not json/);
  delete process.env.FAKE_GATE_STDOUT;
  writeFileSync(join(agent, "mp-infra.json"), JSON.stringify({ root }));

  const path = join(home, "role", "tasks.yml");
  mkdirSync(join(home, "role"));
  writeFileSync(path, "- name: Example\n  debug:\n    msg: okay\n");
  const result = await handlers.get("tool_result")({ toolName: "edit", input: { path }, content: [{ type: "text", text: "Edited" }], isError: false }, ctx);
  assert.match(result.content.at(-1).text, /Validating Ansible file/);
  assert.match(result.content.at(-1).text, /Validation complete/);

  const vault = join(home, "vault.yml");
  writeFileSync(vault, "secret: cleartext\n");
  const vaultResult = await handlers.get("tool_result")({ toolName: "write", input: { path: vault }, content: [], isError: false }, ctx);
  assert.equal(vaultResult.isError, true);
  assert.match(vaultResult.content.at(-1).text, /Decrypted vault file detected/);
  const nomad = join(home, "example.nomad");
  writeFileSync(nomad, "job \"example\" {}\n");
  const nomadResult = await handlers.get("tool_result")({ toolName: "write", input: { path: nomad }, content: [], isError: false }, ctx);
  assert.match(nomadResult.content.at(-1).text, /Validating Nomad job file/);
  await handlers.get("session_start")({}, ctx);
  assert.match(messages[0].content, /Checking deploy-ansible environment/);
  console.log("pi mp-infra hooks: pass");
} finally {
  rmSync(home, { recursive: true, force: true });
}

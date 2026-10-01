import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import tierRoles, { ROLE_PACK_EVENT, rolesDir } from "../pi/extensions/tier-roles.ts";

const agentDir = mkdtempSync(join(tmpdir(), "tier-roles-"));
process.env.PI_CODING_AGENT_DIR = agentDir;
const roles = join(agentDir, "herdr-agents/roles");
assert.equal(rolesDir(), roles);

let listener;
let unsubscribed = false;
const handlers = new Map();
tierRoles({
  events: { on(event, handler) { assert.equal(event, ROLE_PACK_EVENT); listener = handler; return () => { unsubscribed = true; }; } },
  on(event, handler) { handlers.set(event, handler); },
});

const discover = (apiVersion) => {
  const registered = [];
  listener({ apiVersion, register: (path) => registered.push(path) });
  return registered;
};

assert.deepEqual(discover(1), [], "a missing roles directory registers nothing");
mkdirSync(roles, { recursive: true });
assert.deepEqual(discover(1), [roles], "the generated roles directory registers as a role pack");
assert.deepEqual(discover(2), [], "an unknown discovery API version registers nothing");

handlers.get("session_shutdown")();
assert.ok(unsubscribed, "shutdown removes the discovery listener");
rmSync(agentDir, { recursive: true });

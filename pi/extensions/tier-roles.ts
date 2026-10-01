import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export const ROLE_PACK_EVENT = "pi-herdr-subagents:roles:discover:v1";

interface RolePackDiscovery {
  apiVersion: number;
  register(path: string): void;
}

// scripts/pi-target.py writes one role per model tier here from the active strategy.
export function rolesDir(env: NodeJS.ProcessEnv = process.env): string {
  return join(env.PI_CODING_AGENT_DIR ?? join(homedir(), ".pi/agent"), "herdr-agents/roles");
}

export default function tierRoles(pi: ExtensionAPI): void {
  const unsubscribe = pi.events.on(ROLE_PACK_EVENT, (request) => {
    const discovery = request as RolePackDiscovery;
    const path = rolesDir();
    if (discovery.apiVersion === 1 && existsSync(path)) discovery.register(path);
  });
  pi.on("session_shutdown", unsubscribe);
}

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const agentDir = process.env.PI_CODING_AGENT_DIR || join(homedir(), ".pi", "agent");

function hookPath(name: string): string {
  const config = JSON.parse(readFileSync(join(agentDir, "mp-infra.json"), "utf8"));
  const path = join(config.root, "hooks", name);
  if (!existsSync(path)) throw new Error(`mp-infra hook is missing: ${path}`);
  return path;
}

function runHook(name: string, input: object, cwd: string, timeout = 5000) {
  const path = hookPath(name);
  const result = spawnSync(name === "production-safety-hook" || name === "vault-check-hook" ? "python3" : "bash",
    [path, ...(name.startsWith("tool-after-edit-") ? [(input as { tool_input: { file_path: string } }).tool_input.file_path] : [])],
    { input: JSON.stringify(input), cwd, encoding: "utf8", timeout });
  return { code: result.status ?? 2, text: [result.stdout, result.stderr, result.error?.message].filter(Boolean).join("\n").trim() };
}

export default function mpInfraHooks(pi: ExtensionAPI): void {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return;
    const command = String(event.input.command ?? "");
    let result;
    try {
      result = runHook("production-safety-hook", { tool_name: "Bash", tool_input: { command } }, ctx.cwd);
    } catch (error) {
      return { block: true, reason: `mp-infra safety gate unavailable: ${String(error)}` };
    }
    if (result.code !== 0) return { block: true, reason: result.text || "mp-infra safety gate failed" };
    let output: any;
    try { output = JSON.parse(result.text); } catch { return; }
    const decision = output?.hookSpecificOutput?.permissionDecision;
    if (decision === "deny") return { block: true, reason: output?.hookSpecificOutput?.permissionDecisionReason || "mp-infra denied command" };
    if (decision !== "ask") return;
    const reason = output?.hookSpecificOutput?.permissionDecisionReason || "Production-sensitive command";
    if (!ctx.hasUI) return { block: true, reason: `${reason} Approval requires an interactive Pi session.` };
    const approved = await ctx.ui.confirm("mp-infra command review", `${reason}\n\n${command}`);
    if (!approved) return { block: true, reason };
  });

  pi.on("tool_result", async (event, ctx) => {
    if ((event.toolName !== "edit" && event.toolName !== "write") || event.isError) return;
    const path = String(event.input.path ?? event.input.file_path ?? "");
    if (!path) return;
    const input = { tool_name: event.toolName === "edit" ? "Edit" : "Write", tool_input: { file_path: path } };
    const results: string[] = [];
    let failed = false;
    for (const name of ["vault-check-hook", "tool-after-edit-playbook-hook", "tool-after-edit-nomad-hook"]) {
      if (name === "vault-check-hook" && !/vault.*\.ya?ml$/i.test(path)) continue;
      if (name === "tool-after-edit-playbook-hook" && !/\.ya?ml$/i.test(path)) continue;
      if (name === "tool-after-edit-nomad-hook" && !/\.(nomad|hcl|nomad\.j2)$/i.test(path)) continue;
      try {
        const result = runHook(name, input, ctx.cwd);
        if (result.text) results.push(result.text);
        if (result.code !== 0) failed = true;
      } catch (error) {
        results.push(`mp-infra ${name} failed: ${String(error)}`);
        failed = true;
      }
    }
    if (!results.length) return;
    return { content: [...event.content, { type: "text" as const, text: results.join("\n") }], isError: event.isError || failed };
  });

  pi.on("session_start", async (_event, ctx) => {
    try {
      const result = runHook("session-start-hook", {}, ctx.cwd, 10000);
      if (result.text) pi.sendMessage({ customType: "mp-infra-environment", content: result.text, display: false });
    } catch (error) {
      ctx.ui.notify(`mp-infra environment check failed: ${String(error)}`, "warning");
    }
  });
}

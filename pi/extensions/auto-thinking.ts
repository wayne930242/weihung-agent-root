/**
 * Per-prompt thinking level, ported from oh-my-pi's `auto` thinking classifier.
 *
 * Before each user prompt in a main session, TypeSafe Jev answers one choice question about
 * how open-ended the request is, and the answer becomes the session's thinking level for that
 * turn. The question, ladder, and xhigh ceiling follow oh-my-pi; `ultrathink` in the prompt
 * skips the classifier and asks for max. A failed classification keeps the last classified
 * level. Subagents keep the level their dispatcher chose. Choosing a level by hand turns auto
 * off for the session; `/auto-thinking on` turns it back on.
 */

import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

type Level = "low" | "medium" | "high" | "xhigh";

export const CLASSIFY_TIMEOUT_MS = 4000;
const STATUS_KEY = "auto-thinking";

// Question copied from oh-my-pi prompts/judge/auto-thinking.json (`level`, without `max`).
export const LEVEL_QUESTION = {
	type: "choice" as const,
	instructions:
		"The state is a user's request to a coding agent. Judge how open-ended its problem is: whether the fix or design is given, or which causes or designs remain open. Choose the reasoning effort that needs, judging inherent difficulty rather than phrasing politeness or verbosity. Volume of work never raises it. If torn between levels, choose the lower one.",
	criteria: {
		low: "One obvious solution, mechanically applied: target, mapping, or fix given.",
		medium: "A few candidates in a localized area, or one small trap: which line breaks a test, one boundary case.",
		high: "Several viable designs or candidate causes: API shape, policy choice, a known cause whose fix needs a design choice.",
		xhigh: "Open cause of flaky, concurrent, or stale behavior; solutions that are easy to get subtly wrong (races, invariants, cross-version compatibility).",
	},
};

// Prompt cleanup ported from oh-my-pi tiny/message-preproc.ts.
const MAX_CHARS = 2000;
const MIN_STRIPPED_CHARS = 12;
const RAW_SCAN_EDGE_CHARS = 262_144;
const CLEAN_WINDOW_EDGE_CHARS = 16_384;

function windowEdges(message: string, edgeChars: number): string {
	if (message.length <= edgeChars * 2) return message;
	return `${message.slice(0, edgeChars)}\n…\n${message.slice(-edgeChars)}`;
}

function collapseWhitespace(message: string): string {
	return message.replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}

function stripCodeBlocks(message: string): string {
	const cleaned = collapseWhitespace(message.replace(/```+[\s\S]*?(?:```+|$)/g, " "));
	return cleaned.length >= MIN_STRIPPED_CHARS ? cleaned : message;
}

function truncate(message: string): string {
	if (message.length <= MAX_CHARS) return message;
	let omitted = message.length - MAX_CHARS;
	let headChars = 0;
	let tailChars = 0;
	for (let pass = 0; pass < 2; pass++) {
		const keptChars = Math.max(0, MAX_CHARS - `\n[… ${omitted} chars omitted …]\n`.length);
		headChars = Math.ceil((keptChars * 2) / 3);
		tailChars = keptChars - headChars;
		omitted = message.length - headChars - tailChars;
	}
	return `${message.slice(0, headChars)}\n[… ${omitted} chars omitted …]\n${message.slice(-tailChars)}`;
}

export function preprocessPrompt(message: string): string {
	const fenceStripped = stripCodeBlocks(windowEdges(message, RAW_SCAN_EDGE_CHARS).replace(/\u001b\[[0-9;]*m/g, ""));
	const cleaned = windowEdges(fenceStripped, CLEAN_WINDOW_EDGE_CHARS)
		.replace(/<([a-zA-Z][\w-]*)(?:\s[^>]*)?>[\s\S]*?<\/\1>/g, " ")
		.replace(/\b[0-9a-fA-F]{12,}\b/g, (match) => match.slice(0, 7));
	return truncate(collapseWhitespace(cleaned));
}

export type Classifier = (request: string, signal: AbortSignal) => Promise<Level>;

/**
 * One TypeSafe System One request, the call `@typesafe-ai/sdk` makes for `client.systemOne`.
 * Called through fetch because pi does not install dependencies for local packages.
 */
export function jevClassifier(): Classifier {
	return async (request, signal) => {
		const apiKey = process.env.TYPESAFE_API_KEY;
		if (!apiKey) throw new Error("TYPESAFE_API_KEY is not set");
		const baseUrl = (process.env.TYPESAFE_BASE_URL ?? "https://api.typesafe.ai").replace(/\/+$/, "");
		const response = await fetch(`${baseUrl}/v1/systemone`, {
			method: "POST",
			headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json", Accept: "application/json" },
			body: JSON.stringify({
				state: { request },
				questions: { level: LEVEL_QUESTION },
				model: process.env.TYPESAFE_DEFAULT_MODEL ?? "jev-latest",
			}),
			signal,
		});
		if (!response.ok) throw new Error(`TypeSafe ${response.status}: ${(await response.text()).slice(0, 200)}`);
		const choice = ((await response.json()) as { answers?: { level?: { choice?: string } } }).answers?.level?.choice;
		if (!choice || !(choice in LEVEL_QUESTION.criteria)) throw new Error(`unexpected TypeSafe answer: ${choice}`);
		return choice as Level;
	};
}

export function createAutoThinking(classify: Classifier, isSubagent: boolean) {
	return function autoThinking(pi: ExtensionAPI): void {
		if (isSubagent) return;
		let enabled = true;
		let lastResolved: string | undefined;
		let ownLevel: string | undefined;

		const show = (ctx: ExtensionContext, text: string | undefined) => ctx.ui.setStatus(STATUS_KEY, text);

		const apply = (ctx: ExtensionContext, level: string, label: string) => {
			pi.setThinkingLevel(level as never);
			ownLevel = pi.getThinkingLevel();
			lastResolved = level;
			show(ctx, `auto:${ownLevel}${label}`);
		};

		pi.on("session_start", (_event, ctx) => show(ctx, enabled ? "auto" : undefined));

		pi.on("before_agent_start", async (event, ctx) => {
			if (!enabled) return;
			if (/\bultrathink\b/i.test(event.prompt)) {
				apply(ctx, "max", "");
				return;
			}
			const controller = new AbortController();
			const timer = setTimeout(() => controller.abort(), CLASSIFY_TIMEOUT_MS);
			try {
				apply(ctx, await classify(preprocessPrompt(event.prompt), controller.signal), "");
			} catch (error) {
				const reason = error instanceof Error ? error.message : String(error);
				if (lastResolved) apply(ctx, lastResolved, " (kept)");
				ctx.ui.notify(`auto-thinking: classification failed, ${lastResolved ? `kept ${lastResolved}` : "level unchanged"}: ${reason}`, "warning");
			} finally {
				clearTimeout(timer);
			}
		});

		pi.on("thinking_level_select", (event, ctx) => {
			if (!enabled || event.level === ownLevel) return;
			enabled = false;
			show(ctx, undefined);
			ctx.ui.notify(`auto-thinking off: level set to ${event.level} by hand. /auto-thinking on resumes it.`, "info");
		});

		pi.registerCommand("auto-thinking", {
			description: "Turn per-prompt thinking level on or off: /auto-thinking [on|off]",
			handler: async (args, ctx) => {
				const choice = args.trim().toLowerCase();
				if (choice === "on" || choice === "off") enabled = choice === "on";
				else if (choice !== "") {
					ctx.ui.notify("Usage: /auto-thinking [on|off]", "warning");
					return;
				}
				show(ctx, enabled ? `auto${ownLevel ? `:${ownLevel}` : ""}` : undefined);
				ctx.ui.notify(`auto-thinking ${enabled ? "on" : "off"}${lastResolved ? ` (last: ${lastResolved})` : ""}`, "info");
			},
		});
	};
}

export default createAutoThinking(jevClassifier(), Boolean(process.env.PI_SUBAGENT_SESSION));

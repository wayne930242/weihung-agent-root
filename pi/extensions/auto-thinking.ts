/**
 * Per-prompt thinking level, ported from oh-my-pi's `auto` thinking classifier.
 *
 * Before each user prompt in a main session, TypeSafe Jev answers one choice question about
 * how open-ended the request is, and the answer becomes the session's thinking level for that
 * turn. The question, ladder, and xhigh ceiling follow oh-my-pi; `ultrathink` in the prompt
 * skips the classifier and asks for max. A failed classification keeps the last classified
 * level. Choosing a level by hand turns auto off for the session; `/auto-thinking on` turns it
 * back on.
 *
 * A subagent launched with a `solutionSpace` (PI_SUBAGENT_SOLUTION_SPACE) classifies that
 * description instead of its task, once, with oh-my-pi's solution-space question; without one
 * it keeps the level its dispatcher chose.
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

// oh-my-pi's `solutionSpace` question: same ladder, instructions for a delegator's description.
export const SOLUTION_SPACE_QUESTION = {
	...LEVEL_QUESTION,
	instructions:
		"The state describes how open-ended a coding subagent's problem is; the work itself is not shown. Choose the reasoning effort it needs. Volume of work and coordination with other agents never raise it. If torn between levels, choose the lower one.",
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

/** The turn to classify: the user's request, or a delegator's solution-space description. */
export type DifficultyInput = { request: string } | { solutionSpace: string };

export type Classifier = (input: DifficultyInput, signal: AbortSignal) => Promise<Level>;

/**
 * One TypeSafe System One request, the call `@typesafe-ai/sdk` makes for `client.systemOne`.
 * Called through fetch because pi does not install dependencies for local packages.
 */
export function jevClassifier(): Classifier {
	return async (input, signal) => {
		const [state, question] =
			"solutionSpace" in input
				? [{ solution_space: input.solutionSpace }, SOLUTION_SPACE_QUESTION]
				: [{ request: input.request }, LEVEL_QUESTION];
		const apiKey = process.env.TYPESAFE_API_KEY;
		if (!apiKey) throw new Error("TYPESAFE_API_KEY is not set");
		const baseUrl = (process.env.TYPESAFE_BASE_URL ?? "https://api.typesafe.ai").replace(/\/+$/, "");
		const response = await fetch(`${baseUrl}/v1/systemone`, {
			method: "POST",
			headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json", Accept: "application/json" },
			body: JSON.stringify({
				state,
				questions: { level: question },
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

export interface ChildContext {
	isSubagent: boolean;
	solutionSpace?: string;
}

/** Classify a subagent's solution space once, on its first prompt; failures keep the dispatcher's level. */
function registerChild(pi: ExtensionAPI, classify: Classifier, solutionSpace: string): void {
	let classified = false;
	pi.on("before_agent_start", async (_event, ctx) => {
		if (classified) return;
		classified = true;
		const signal = AbortSignal.timeout(CLASSIFY_TIMEOUT_MS);
		try {
			const level = await classify({ solutionSpace: preprocessPrompt(solutionSpace) }, signal);
			pi.setThinkingLevel(level);
			ctx.ui.setStatus(STATUS_KEY, `auto:${pi.getThinkingLevel()}`);
		} catch (error) {
			const reason = error instanceof Error ? error.message : String(error);
			ctx.ui.notify(`auto-thinking: solution space classification failed, level unchanged: ${reason}`, "warning");
		}
	});
}

export function createAutoThinking(classify: Classifier, child: ChildContext) {
	return function autoThinking(pi: ExtensionAPI): void {
		if (child.isSubagent) {
			const solutionSpace = child.solutionSpace?.trim();
			if (solutionSpace) registerChild(pi, classify, solutionSpace);
			return;
		}
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
				apply(ctx, await classify({ request: preprocessPrompt(event.prompt) }, controller.signal), "");
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

export default createAutoThinking(jevClassifier(), {
	isSubagent: Boolean(process.env.PI_SUBAGENT_SESSION),
	solutionSpace: process.env.PI_SUBAGENT_SOLUTION_SPACE,
});

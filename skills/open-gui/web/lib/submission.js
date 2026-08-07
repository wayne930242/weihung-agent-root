// Builds the text sent as a `message:send` payload for node-driven input
// (design.md D11 — a plain streamed message, not PTY stdin).

export function sanitizeText(text) {
  return text.replace(/\r?\n/g, " ").trim();
}

// Every submission carries a reference to the originating node's id and
// title (spec: "Every submission carries node context"), so the session can
// identify which node is being answered even when multiple nodes are open.
export function buildSubmission(node, rawText) {
  const clean = sanitizeText(rawText);
  return `Re "${node.title}" [${node.id}]: ${clean}`;
}

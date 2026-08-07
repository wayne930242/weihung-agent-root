// Builds the exact string sent as a `pty:write` payload for node-driven input.
// Every node interaction funnels into the same PTY stdin (design.md D5) — this
// is the one place that composes the text before it's written.

export function sanitizeForPty(text) {
  return text.replace(/\r?\n/g, " ").trim();
}

// Every submission carries a reference to the originating node's id and
// title (spec: "Every submission carries node context"), so the receiving
// `claude` process can identify which node is being answered even when
// multiple nodes are open at once.
export function buildSubmission(node, rawText) {
  const clean = sanitizeForPty(rawText);
  const text = `Re "${node.title}" [${node.id}]: ${clean}`;
  return `${text}\r`;
}

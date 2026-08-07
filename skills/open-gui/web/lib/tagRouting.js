// Routes a transcript entry (or a live question) to the canvas card it
// belongs on, per a leading `#[id]` tag the session's Claude is instructed
// to prefix onto text that discusses a specific TREE.json node
// (grill-with-web/SKILL.md's interview discipline).
//
// Anchored at the very start of the text only — a `#[...]`-shaped string
// appearing mid-sentence is content, not a routing tag (user-specified:
// "只有開頭的明確要帶的，才是要接"). And a leading tag whose id doesn't match
// any node currently in the tree is treated the same as no tag at all,
// left untouched in the displayed text — it might be genuine content that
// happens to look like the tag syntax, not a routing mistake to silently
// swallow (user-specified: "不要過度敏感 #slug 如果對不到的，代表那可能是真的
// #slug 要送給使用者").
const TAG_PATTERN = /^#\[([a-zA-Z0-9_-]+)\]\s*/;

// Returns { targetNodeId, text } — targetNodeId is null (route to the
// synthesized root thread) when there's no tag, or the tag doesn't resolve
// to a real node id. `text` has the tag prefix stripped only when it does.
export function routeTaggedText(rawText, nodesById) {
  const match = rawText.match(TAG_PATTERN);
  if (!match) return { targetNodeId: null, text: rawText };
  const id = match[1];
  if (!nodesById.has(id)) return { targetNodeId: null, text: rawText };
  return { targetNodeId: id, text: rawText.slice(match[0].length) };
}

// Same routing rule applied to a live AskUserQuestion call — a call carries
// 1-4 questions, but routing is decided once per call from the first
// question's tag only (not split across nodes). Every question's own text
// still gets its leading tag stripped for display, independent of routing,
// so a later question that Claude also tagged (common when a call spans
// more than one node's topic) doesn't show raw `#[id]` syntax to the user.
export function routeQuestion(questions, nodesById) {
  const { targetNodeId } = routeTaggedText(questions[0]?.question ?? "", nodesById);
  const stripped = questions.map((q) => ({
    ...q,
    question: routeTaggedText(q.question, nodesById).text,
  }));
  return { targetNodeId, questions: stripped };
}

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

// Same routing rule applied to each question in a live AskUserQuestion call
// independently — a call carries 1-4 questions, and each becomes its own
// ephemeral canvas card (design.md D12 revision, user: "三個問題三張卡片，
// 然後都接到上層的 root" — a multi-question call spanning several nodes'
// topics was rendering as one bundled UI, not one card per question).
export function routeQuestions(questions, nodesById) {
  return questions.map((q) => {
    const { targetNodeId, text } = routeTaggedText(q.question, nodesById);
    return { ...q, question: text, targetNodeId };
  });
}

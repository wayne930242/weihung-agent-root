"use client";

import { useState } from "react";

// Plain free-text follow-up box for node types other than `question`
// (design.md D5: "all other node types get a plain free-text box").
// Submits go through `enqueue` (item 3's pending queue, CanvasView.js) —
// SidekickPanel dispatches them one at a time once the agent is idle,
// rather than firing straight to the agent regardless of what it's
// already working on.

export default function FreeTextBox({ node, enqueue, placeholder = "Reply…", onSubmit }) {
  const [text, setText] = useState("");
  // The "/" shortcut hint lives in the placeholder itself, not just the
  // bottom shortcut-hints bar (user: "/ 和 : 放到相應的 input 的 placeholder
  // （當還沒 focus 的時候）") — only while unfocused, since it's redundant
  // once you're already typing here.
  const [focused, setFocused] = useState(false);

  function submit() {
    if (!text.trim()) return;
    enqueue(node, text);
    onSubmit?.();
    setText("");
  }

  return (
    <div className="node-freetext">
      <textarea
        className="nodrag nopan"
        value={text}
        placeholder={focused ? placeholder : `${placeholder} (/)`}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          // Guard against IME composition (e.g. Chinese input): a composing
          // Enter confirms the composed text instead of submitting.
          if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            submit();
          }
        }}
      />
      <button className="nodrag nopan" onClick={submit} disabled={!text.trim()}>
        Send
      </button>
    </div>
  );
}

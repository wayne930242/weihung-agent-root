"use client";

import { useState } from "react";
import { useSocket } from "./SocketProvider";
import { buildSubmission } from "../lib/submission";

// Plain free-text follow-up box for node types other than `question`
// (design.md D5: "all other node types get a plain free-text box").

export default function FreeTextBox({ node, placeholder = "Reply…", onSubmit }) {
  const { send } = useSocket();
  const [text, setText] = useState("");

  function submit() {
    if (!text.trim()) return;
    send({ type: "message:send", text: buildSubmission(node, text) });
    onSubmit?.();
    setText("");
  }

  return (
    <div className="node-freetext">
      <textarea
        value={text}
        placeholder={placeholder}
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
      <button onClick={submit} disabled={!text.trim()}>
        Send
      </button>
    </div>
  );
}

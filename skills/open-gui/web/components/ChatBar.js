"use client";

import { useState } from "react";
import { useSocket } from "./SocketProvider";

// The general-purpose message input, fixed chrome outside the pannable
// canvas (user: "message 應該放到最外層的 chat") — a message sent from here
// carries no node tag, so it routes to the root card's thread like any
// other untagged content (lib/tagRouting.js).
export default function ChatBar() {
  const { send } = useSocket();
  const [draft, setDraft] = useState("");
  // The ":" shortcut hint lives in the placeholder itself, not just the
  // bottom shortcut-hints bar (user: "/ 和 : 放到相應的 input 的 placeholder
  // （當還沒 focus 的時候）") — only while unfocused.
  const [focused, setFocused] = useState(false);

  function submit() {
    if (!draft.trim()) return;
    send({ type: "message:send", text: draft });
    setDraft("");
  }

  return (
    <div className="chat-bar">
      <textarea
        value={draft}
        placeholder={focused ? "Message…" : "Message… (:)"}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            submit();
          }
        }}
      />
      <button onClick={submit} disabled={!draft.trim()}>
        Send
      </button>
    </div>
  );
}

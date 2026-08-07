"use client";

import { useEffect, useRef } from "react";
import Thread from "./Thread";

// Shown for whichever card is currently focused (design.md D12, user:
// "focus 的時候，可以用邊欄 layout 顯示那一段的完整過程"). Cards themselves
// only show their latest entry; this is the full history. Live
// AskUserQuestion answering happens directly on its own ephemeral canvas
// card now (LiveQuestionCanvasCard), not here — this sidebar has nothing to
// add for a card with no history (user: "沒內容的就不用硬要顯示 sidebar
// 了"), so it renders nothing rather than an empty panel. A blind usability
// test found this panel, once open, had no way to close it (Esc/clicking
// the canvas did nothing) and sat there permanently — `onClose` gives it an
// explicit X; CanvasView.js resets the dismissal whenever focus moves to a
// genuinely different card, so switching focus always shows the new card's
// history fresh.
export default function DetailSidebar({ title, thread, onClose }) {
  const bodyRef = useRef(null);

  useEffect(() => {
    const el = bodyRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [thread]);

  if (!title || thread.length === 0) return null;

  return (
    <div className="detail-sidebar">
      <div className="detail-sidebar-header">
        <span className="detail-sidebar-title">{title}</span>
        <button className="detail-sidebar-close nodrag nopan" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>
      <div className="detail-sidebar-body" ref={bodyRef}>
        <Thread entries={thread} />
      </div>
    </div>
  );
}

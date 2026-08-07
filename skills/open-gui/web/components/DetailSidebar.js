"use client";

import { useEffect, useRef } from "react";
import Thread from "./Thread";
import LiveQuestionCard from "./LiveQuestionCard";
import { useSocket } from "./SocketProvider";

// Shown for whichever card is currently focused (design.md D12, user:
// "focus 的時候，可以用邊欄 layout 顯示那一段的完整過程"). Cards themselves
// only show their latest entry; this is the full history, plus the actual
// interactive answering UI for a live AskUserQuestion routed here (moved
// out of the cramped fixed-size card body — user: "問題選項沒有出來，是不是
// focus 的時候可以顯示再卡片旁邊").
export default function DetailSidebar({ title, thread, pendingQuestion }) {
  const { send } = useSocket();
  const bodyRef = useRef(null);

  useEffect(() => {
    const el = bodyRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [thread, pendingQuestion]);

  function answerQuestion(requestId, answers) {
    send({ type: "question:answer", requestId, answers });
  }

  // Digit-key quick-answer only applies to a single-question call — a
  // multi-question call has no unambiguous "the" option list for a bare
  // digit to mean, so it's mouse-only there (documented simplification).
  useEffect(() => {
    if (!pendingQuestion || pendingQuestion.questions.length !== 1) return;
    function handleKeyDown(e) {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      const q = pendingQuestion.questions[0];
      if (e.key >= "1" && e.key <= "4") {
        const idx = Number(e.key);
        if (idx <= q.options.length) {
          e.preventDefault();
          answerQuestion(pendingQuestion.requestId, { [q.question]: q.options[idx - 1].label });
        }
      } else if (e.key === "/") {
        e.preventDefault();
        document.querySelector(".detail-sidebar .node-other input")?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingQuestion]);

  if (!title) return null;

  return (
    <div className="detail-sidebar">
      <div className="detail-sidebar-header">{title}</div>
      <div className="detail-sidebar-body" ref={bodyRef}>
        <Thread entries={thread} />
        {pendingQuestion && (
          <LiveQuestionCard
            requestId={pendingQuestion.requestId}
            questions={pendingQuestion.questions}
            onAnswer={answerQuestion}
          />
        )}
      </div>
    </div>
  );
}

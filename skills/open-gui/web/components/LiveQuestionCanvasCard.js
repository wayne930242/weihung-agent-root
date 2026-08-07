"use client";

import { useEffect, useState } from "react";
import { Handle, Position } from "@xyflow/react";
import { cn } from "../lib/cn";

// design.md D12 revision: each question in an AskUserQuestion call is its
// own ephemeral canvas card, parented to whatever it's routed to (or root)
// — not bundled into one shared answering UI (user: "三個問題三張卡片，然後
// 都接到上層的 root"). Picking an option/Other only stages the answer
// (`picked`) — it's not sent to the agent until Submit (user: "選完先不送，
// 跳確認卡" — a card vanishing straight to the agent on the first click gave
// no chance to change your mind or confirm what was actually picked).
export default function LiveQuestionCanvasCard({ id, data }) {
  const { question: q, onAnswer, focused, onFocus } = data;
  const [picked, setPicked] = useState(q.multiSelect ? [] : null);
  const [otherText, setOtherText] = useState("");
  // "/" shortcut hint lives in the placeholder itself (user: "/ 和 : 放到
  // 相應的 input 的 placeholder（當還沒 focus 的時候）") — only while
  // unfocused.
  const [otherFocused, setOtherFocused] = useState(false);

  function toggle(label) {
    if (q.multiSelect) {
      setPicked((prev) => (prev.includes(label) ? prev.filter((l) => l !== label) : [...prev, label]));
    } else {
      setPicked((prev) => (prev === label ? null : label));
    }
  }

  function setOther() {
    const text = otherText.trim();
    if (!text) return;
    if (q.multiSelect) {
      setPicked((prev) => (prev.includes(text) ? prev : [...prev, text]));
    } else {
      setPicked(text);
    }
    setOtherText("");
  }

  function reselect() {
    setPicked(q.multiSelect ? [] : null);
  }

  const hasSelection = q.multiSelect ? picked.length > 0 : picked != null;

  function submit() {
    if (!hasSelection) return;
    onAnswer(picked);
  }

  useEffect(() => {
    if (!focused) return;
    function handleKeyDown(e) {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (hasSelection && e.key === "Enter") {
        e.preventDefault();
        submit();
        return;
      }
      if (!q.multiSelect && e.key >= "1" && e.key <= "4") {
        const idx = Number(e.key);
        if (idx <= q.options.length) {
          e.preventDefault();
          setPicked(q.options[idx - 1].label);
        }
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focused, q, hasSelection, picked]);

  return (
    <div
      className={cn("canvas-card", "canvas-card-question", "nodrag", "nopan", focused && "canvas-card-focused")}
      data-card-id={id}
      onClick={onFocus}
    >
      <Handle type="target" position={Position.Top} />
      <div className="canvas-card-header">
        <span className="canvas-card-title">{q.header}</span>
      </div>
      {/* `nowheel` (not CardBody — its scroll-to-bottom-on-render effect is
          wrong here, this is a question to read top-down, not a growing
          thread) is what actually lets the mouse wheel scroll this body
          instead of React Flow's canvas stealing the event to pan/zoom
          (user: "滾輪效果會直接被 canvas 攔截，無法下滑" — missed when this
          card was first split out from CardBody's shared pattern). */}
      <div className="canvas-card-body nowheel">
        <p className="question-text">{q.question}</p>
        <div className="option-cards">
          {q.options.map((opt) => {
            const selected = q.multiSelect ? picked.includes(opt.label) : picked === opt.label;
            return (
              <button
                key={opt.label}
                className={cn("option-card", "nodrag", "nopan", selected && "option-card-selected")}
                onClick={() => toggle(opt.label)}
              >
                <span className="option-label">{opt.label}</span>
                {opt.description && <span className="option-desc">{opt.description}</span>}
              </button>
            );
          })}
        </div>
        <div className="node-other">
          <input
            type="text"
            className="nodrag nopan"
            placeholder={otherFocused ? "Other…" : "Other… (/)"}
            value={otherText}
            onFocus={() => setOtherFocused(true)}
            onBlur={() => setOtherFocused(false)}
            onChange={(e) => setOtherText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.nativeEvent.isComposing) setOther();
            }}
          />
          <button className="nodrag nopan" onClick={setOther} disabled={!otherText.trim()}>
            Set
          </button>
        </div>
      </div>
      {/* Sticky footer, not scrolled-past content — a long question/option
          list previously buried Submit below the fold, and the wheel-trap
          bug above made it unreachable entirely (user: "把 submit 拉到卡片
          層，stick 卡片底端"). Always visible; disabled (not hidden) until
          there's something to submit. */}
      <div className="canvas-card-footer question-confirm">
        <span className="question-confirm-value">
          {hasSelection ? `已選：${Array.isArray(picked) ? picked.join("、") : picked}` : "尚未選擇"}
        </span>
        <div className="question-confirm-actions">
          <button className="nodrag nopan" onClick={reselect} disabled={!hasSelection}>
            重選
          </button>
          <button className="question-submit nodrag nopan" onClick={submit} disabled={!hasSelection}>
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}

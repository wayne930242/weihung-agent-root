"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSocket } from "./SocketProvider";
import { buildSubmission } from "../lib/submission";
import StatusBadge from "./StatusBadge";

// Mirrors the AskUserQuestion tool's own interface: option cards, plus an
// always-present "Other" free-text field and notes field, even when options
// is non-empty (NODE-FORMAT.md, design.md D5/D9).
//
// design.md D11: this is for `question`-type TREE NODES from non-
// `grill-with-web` consumers (Claude wrote the node into TREE.json directly,
// the old design's mechanism) — distinct from the live AskUserQuestion
// cards in the transcript pane, which answer through `question:ask`/
// `question:answer` instead. Both ultimately just send a plain message; no
// PTY, no keystroke protocol.

export default function QuestionNode({ node, onSubmit }) {
  const { send } = useSocket();
  const [notes, setNotes] = useState("");
  const [customText, setCustomText] = useState("");
  const notesRef = useRef(null);
  const optionCount = node.options?.length ?? 0;

  const submitOption = useCallback(
    (index) => {
      const label = node.options[index - 1].label;
      const notesTrimmed = notes.trim();
      const combined = notesTrimmed ? `${label} — note: ${notesTrimmed}` : label;
      send({ type: "message:send", text: buildSubmission(node, combined) });
      onSubmit?.();
    },
    [node, notes, send, onSubmit],
  );

  const submitOther = useCallback(
    (text) => {
      if (!text.trim()) return;
      const notesTrimmed = notes.trim();
      const combined = notesTrimmed ? `${text} — note: ${notesTrimmed}` : text;
      send({ type: "message:send", text: buildSubmission(node, combined) });
      onSubmit?.();
    },
    [node, notes, send, onSubmit],
  );

  // Keyboard quick-answer: this listener is naturally scoped to "only while
  // this question node is selected" because NodeDetail remounts QuestionNode
  // fresh (keyed on node.id) whenever the selection changes. Ignored while
  // focus is inside a text input/textarea so typing digits or "n" into the
  // "Other"/notes fields isn't hijacked.
  useEffect(() => {
    function handleKeyDown(e) {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (e.key >= "1" && e.key <= "4") {
        const idx = Number(e.key);
        if (idx <= optionCount) {
          e.preventDefault();
          submitOption(idx);
        }
      } else if (e.key === "n" || e.key === "N") {
        e.preventDefault();
        notesRef.current?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [optionCount, submitOption]);

  return (
    <div className="node-body node-question">
      <StatusBadge status={node.status} />
      <p className="node-prompt">{node.prompt}</p>
      {node.status === "resolved" && node.answer && (
        <div className="answer-card">
          <span className="answer-card-label">Your answer</span>
          <span className="answer-card-value">
            {node.answer.selectedLabel ?? node.answer.customText}
          </span>
          {node.answer.notes && (
            <span className="answer-card-notes">note: {node.answer.notes}</span>
          )}
        </div>
      )}
      {optionCount > 0 && (
        <div className="option-cards">
          {node.options.map((opt, i) => (
            <button
              key={opt.label}
              className="option-card"
              onClick={() => submitOption(i + 1)}
            >
              <span className="option-label">{opt.label}</span>
              {opt.description && (
                <span className="option-desc">{opt.description}</span>
              )}
            </button>
          ))}
        </div>
      )}
      <div className="node-other">
        <input
          type="text"
          placeholder="Other…"
          value={customText}
          onChange={(e) => setCustomText(e.target.value)}
          onKeyDown={(e) => {
            // Guard against IME composition (e.g. Chinese input): a composing
            // Enter confirms the composed text instead of submitting.
            if (e.key === "Enter" && !e.nativeEvent.isComposing) {
              submitOther(customText);
              setCustomText("");
            }
          }}
        />
        <button
          onClick={() => {
            submitOther(customText);
            setCustomText("");
          }}
          disabled={!customText.trim()}
        >
          Send
        </button>
      </div>
      <textarea
        ref={notesRef}
        className="node-notes"
        placeholder="Notes (sent as a follow-up after your selection)…"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />
    </div>
  );
}

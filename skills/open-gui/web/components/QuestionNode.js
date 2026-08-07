"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSocket } from "./SocketProvider";
import { buildSubmission } from "../lib/submission";
import StatusBadge from "./StatusBadge";

// Mirrors the AskUserQuestion tool's own interface: option cards, plus an
// always-present "Other" free-text field and notes field, even when options
// is non-empty (NODE-FORMAT.md, design.md D5/D9).

// Empirically verified against a real claude session (2026-08-07): Claude
// Code's AskUserQuestion widget is a raw-mode menu, not a text prompt.
// - A bare digit keystroke (no \r) for one of the *real* options (1..N)
//   selects AND confirms it in one step. Sending the option's label text
//   instead does nothing useful — worse, a long single-write burst trips
//   the same paste-detection that ate the seed prompt (main.ts) and gets
//   silently dropped.
// - The widget also appends two extra entries after the real options:
//   N+1 "Type something" and N+2 "Chat about this". A digit keystroke there
//   only moves the highlight; a *separate* \r is needed to confirm it — and
//   confirming doesn't open a text field inside the widget, it cancels the
//   tool call outright and returns to the normal chat prompt, where a
//   plain-text message works exactly like any other chat input.
// Consequence: notes can no longer be attached in the same action as an
// option pick (the digit press already confirms and moves on) — they go out
// as a separate follow-up message afterward instead. Known open gap: all of
// this assumes the terminal is still showing *this* node's menu at the
// moment of submission — a stale node's digit keystrokes land on whatever
// the terminal actually shows right now, not necessarily this question.
const MENU_STEP_DELAY_MS = 300;

export default function QuestionNode({ node, onSubmit }) {
  const { send } = useSocket();
  const [notes, setNotes] = useState("");
  const [customText, setCustomText] = useState("");
  const notesRef = useRef(null);
  const optionCount = node.options?.length ?? 0;

  const submitOption = useCallback(
    (index) => {
      send({ type: "pty:write", data: String(index) });
      onSubmit?.();
      const notesTrimmed = notes.trim();
      if (notesTrimmed) {
        setTimeout(() => {
          send({ type: "pty:write", data: buildSubmission(node, `note: ${notesTrimmed}`) });
        }, MENU_STEP_DELAY_MS);
      }
    },
    [node, notes, send, onSubmit],
  );

  const submitOther = useCallback(
    (text) => {
      if (!text.trim()) return;
      const otherIndex = optionCount + 1;
      send({ type: "pty:write", data: String(otherIndex) });
      onSubmit?.();
      setTimeout(() => {
        send({ type: "pty:write", data: "\r" });
        setTimeout(() => {
          const notesTrimmed = notes.trim();
          const combined = notesTrimmed ? `${text} — note: ${notesTrimmed}` : text;
          send({ type: "pty:write", data: buildSubmission(node, combined) });
        }, MENU_STEP_DELAY_MS);
      }, MENU_STEP_DELAY_MS);
    },
    [node, notes, optionCount, send, onSubmit],
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

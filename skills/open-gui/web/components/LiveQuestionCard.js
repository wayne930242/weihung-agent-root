"use client";

import { useState } from "react";
import { cn } from "../lib/cn";

// Interactive AskUserQuestion answering UI (design.md D11) — renders every
// question in a single call (1-4 questions, each 2-4 options, optionally
// multiSelect) and submits one combined `answers` map once every question
// has a pick, matching the Agent SDK's expected response shape. Embedded
// inline in whichever card's Thread it was routed to (root, or a specific
// node — see lib/tagRouting.js).
export default function LiveQuestionCard({ requestId, questions, onAnswer }) {
  const [answers, setAnswers] = useState({});
  const [otherText, setOtherText] = useState({});

  function pick(q, label) {
    setAnswers((prev) => {
      if (q.multiSelect) {
        const cur = Array.isArray(prev[q.question]) ? prev[q.question] : [];
        const next = cur.includes(label)
          ? cur.filter((l) => l !== label)
          : [...cur, label];
        return { ...prev, [q.question]: next };
      }
      return { ...prev, [q.question]: label };
    });
  }

  function setOther(q, text) {
    setAnswers((prev) => ({ ...prev, [q.question]: text }));
  }

  const allAnswered = questions.every((q) => {
    const a = answers[q.question];
    return q.multiSelect ? Array.isArray(a) && a.length > 0 : typeof a === "string" && a.trim();
  });

  return (
    <div className="live-question-card">
      {questions.map((q) => (
        <div key={q.question} className="question-block">
          <div className="question-header">{q.header}</div>
          <p className="question-text">{q.question}</p>
          <div className="option-cards">
            {q.options.map((opt) => {
              const current = answers[q.question];
              const selected = q.multiSelect
                ? Array.isArray(current) && current.includes(opt.label)
                : current === opt.label;
              return (
                <button
                  key={opt.label}
                  className={cn("option-card", "nodrag", "nopan", selected && "option-card-selected")}
                  onClick={() => pick(q, opt.label)}
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
              placeholder="Other…"
              value={otherText[q.question] || ""}
              onChange={(e) => {
                const text = e.target.value;
                setOtherText((prev) => ({ ...prev, [q.question]: text }));
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                  setOther(q, otherText[q.question] || "");
                }
              }}
            />
            <button
              className="nodrag nopan"
              onClick={() => setOther(q, otherText[q.question] || "")}
              disabled={!(otherText[q.question] || "").trim()}
            >
              Set
            </button>
          </div>
        </div>
      ))}
      <button
        className="question-submit nodrag nopan"
        disabled={!allAnswered}
        onClick={() => onAnswer(requestId, answers)}
      >
        Submit answers
      </button>
    </div>
  );
}

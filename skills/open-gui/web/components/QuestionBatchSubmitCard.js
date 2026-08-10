"use client";

import { useState } from "react";
import { Handle, Position } from "@xyflow/react";
import { cn } from "../lib/cn";

// Shared child of every question in an AskUserQuestion batch (design.md-
// style ephemeral card, never written to TREE.json, same as
// LiveQuestionCanvasCard) — appears only once every question has a staged
// answer (CanvasView.js's `batchSubmit`), and its own Submit button is what
// actually sends `question:answer` to the agent. The individual per-
// question cards disappear as each is staged (CanvasView.js's
// `liveQuestions` filter); this is the review-and-confirm step before the
// batch actually reaches the agent, not an auto-fire the instant the last
// pick lands (user: "跳到 submit card（這張卡片是問題的共同 child，只有所有
// 問題都回答的時候他才會出現）").
export default function QuestionBatchSubmitCard({ id, data }) {
  const { questions, answers, onSubmit, focused, onFocus } = data;
  const [submitted, setSubmitted] = useState(false);

  function submit() {
    if (submitted) return;
    setSubmitted(true);
    onSubmit();
  }

  return (
    <div
      className={cn("canvas-card", "canvas-card-batch-submit", "nodrag", "nopan", focused && "canvas-card-focused")}
      data-card-id={id}
      onClick={onFocus}
    >
      <Handle type="target" position={Position.Top} />
      <div className="canvas-card-header">
        <span className="canvas-card-title">確認送出</span>
      </div>
      <div className="canvas-card-body nowheel">
        {questions.map((q) => (
          <div key={q.question} className="batch-submit-entry">
            <span className="batch-submit-question">{q.question}</span>
            <span className="batch-submit-answer">
              {Array.isArray(answers[q.question]) ? answers[q.question].join("、") : answers[q.question]}
            </span>
          </div>
        ))}
      </div>
      <div className="canvas-card-footer">
        <button className="question-submit nodrag nopan" onClick={submit} disabled={submitted}>
          {submitted ? "已送出…" : "Submit"}
        </button>
      </div>
    </div>
  );
}

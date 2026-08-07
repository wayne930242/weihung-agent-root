"use client";

import { useCallback, useState } from "react";
import { Handle, Position } from "@xyflow/react";
import CardBody from "./CardBody";
import StatusBadge from "./StatusBadge";
import NodeTypeIcon from "./NodeTypeIcon";
import { useSocket } from "./SocketProvider";
import { buildSubmission } from "../lib/submission";
import { cn } from "../lib/cn";

// A `question`-type TREE.json node — persisted by a non-`grill-with-web`
// consumer (NODE-FORMAT.md's D11 note: grill-with-web answers live instead,
// via LiveQuestionCard). Same option-cards + "Other" + notes interface,
// submitted as a plain message like any other node interaction.
export default function QuestionTreeCard({ id, data }) {
  const { send } = useSocket();
  const { node, pendingQuestion, focused, onFocus } = data;
  const [notes, setNotes] = useState("");
  const [customText, setCustomText] = useState("");
  // "/" and "e" shortcut hints live in the placeholder itself (user: "/ 和 :
  // 放到相應的 input 的 placeholder（當還沒 focus 的時候）") — only while
  // unfocused.
  const [otherFocused, setOtherFocused] = useState(false);
  const [notesFocused, setNotesFocused] = useState(false);
  const optionCount = node.options?.length ?? 0;
  const resolved = node.status === "resolved";

  const submitOption = useCallback(
    (index) => {
      const label = node.options[index - 1].label;
      const notesTrimmed = notes.trim();
      const combined = notesTrimmed ? `${label} — note: ${notesTrimmed}` : label;
      send({ type: "message:send", text: buildSubmission(node, combined) });
    },
    [node, notes, send],
  );

  const submitOther = useCallback(
    (text) => {
      if (!text.trim()) return;
      const notesTrimmed = notes.trim();
      const combined = notesTrimmed ? `${text} — note: ${notesTrimmed}` : text;
      send({ type: "message:send", text: buildSubmission(node, combined) });
    },
    [node, notes, send],
  );

  function reconsider() {
    // Carries the previous answer along so the agent's next message can
    // withdraw that specific conclusion with context (user: "重新考慮只需要
    // 把前一題的結論帶脈絡重送，並且表示撤回前輪就好").
    const previousResolution = node.answer?.selectedLabel ?? node.answer?.customText;
    send({ type: "node:reconsider", nodeId: node.id, title: node.title, previousResolution });
  }

  return (
    <div
      className={cn("canvas-card", "canvas-card-question", "nodrag", "nopan", focused && "canvas-card-focused")}
      data-card-id={id}
      onClick={onFocus}
    >
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <div className="canvas-card-header">
        <NodeTypeIcon type="question" />
        <span className="canvas-card-title">{node.title}</span>
        <StatusBadge status={node.status} />
        {pendingQuestion && <span className="pending-badge">?</span>}
        {resolved && (
          <button className="reconsider-btn nodrag nopan" onClick={reconsider}>
            重新考慮
          </button>
        )}
      </div>
      <CardBody>
        <p className="node-prompt">{node.prompt}</p>
        {resolved && node.answer && (
          <div className="answer-card">
            <span className="answer-card-label">Answer</span>
            <span className="answer-card-value">
              {node.answer.selectedLabel ?? node.answer.customText}
            </span>
            {node.answer.notes && <span className="answer-card-notes">note: {node.answer.notes}</span>}
          </div>
        )}
        {optionCount > 0 && (
          <div className="option-cards">
            {node.options.map((opt, i) => (
              <button
                key={opt.label}
                className="option-card nodrag nopan"
                onClick={() => submitOption(i + 1)}
              >
                <span className="option-label">{opt.label}</span>
                {opt.description && <span className="option-desc">{opt.description}</span>}
              </button>
            ))}
          </div>
        )}
        <div className="node-other">
          <input
            type="text"
            className="nodrag nopan"
            placeholder={otherFocused ? "Other…" : "Other… (/)"}
            value={customText}
            onFocus={() => setOtherFocused(true)}
            onBlur={() => setOtherFocused(false)}
            onChange={(e) => setCustomText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                submitOther(customText);
                setCustomText("");
              }
            }}
          />
          <button
            className="nodrag nopan"
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
          className="node-notes nodrag nopan"
          placeholder={notesFocused ? "Notes…" : "Notes… (e)"}
          value={notes}
          onFocus={() => setNotesFocused(true)}
          onBlur={() => setNotesFocused(false)}
          onChange={(e) => setNotes(e.target.value)}
        />
      </CardBody>
    </div>
  );
}

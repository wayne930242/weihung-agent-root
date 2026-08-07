"use client";

import { useEffect, useRef, useState } from "react";
import { useSocket } from "./SocketProvider";
import Markdown from "./Markdown";

// design.md D11: replaces the xterm terminal. Renders the SDK message stream
// as a card list, not raw text — the user asked for a card-based
// conversation where a card can be promoted into a tree node ("加進 tree").
// AskUserQuestion answers happen here too (question:ask/question:answer),
// not through PTY keystrokes.

// The frontend never writes TREE.json itself (design.md D4 — Claude is the
// sole author); "加進 tree" sends a message asking Claude to add a node,
// using its own judgment for type/fields, same mechanism as any other
// free-text submission.
function buildPromoteMessage(entry) {
  if (entry.kind === "assistant") {
    return `Add a node to TREE.json for this (your judgment on type/fields): "${entry.text}"`;
  }
  if (entry.kind === "tool_use") {
    return `Add a node to TREE.json for this tool call (your judgment on type/fields): ${entry.tool}(${entry.summary})`;
  }
  return null;
}

function Card({ entry, onPromote }) {
  if (entry.kind === "system") {
    return <div className="chat-card chat-card-system">{entry.text}</div>;
  }
  const promoteMsg = buildPromoteMessage(entry);
  return (
    <div className={`chat-card chat-card-${entry.kind}`}>
      {entry.kind === "assistant" ? (
        <Markdown text={entry.text} />
      ) : (
        <div className="tool-use-summary">
          <span className="tool-use-name">{entry.tool}</span>
          <span className="tool-use-detail">{entry.summary}</span>
        </div>
      )}
      {promoteMsg && (
        <button className="add-to-tree-btn" onClick={() => onPromote(promoteMsg)}>
          + 加進 tree
        </button>
      )}
    </div>
  );
}

// Renders every question in a single AskUserQuestion call (1-4 questions,
// each 2-4 options, optionally multiSelect) and submits one combined
// `answers` map once every question has a pick — matching the Agent SDK's
// expected response shape (design.md D11).
function QuestionCard({ requestId, questions, onAnswer }) {
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
    <div className="chat-card question-card">
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
                  className={`option-card${selected ? " option-card-selected" : ""}`}
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
              onClick={() => setOther(q, otherText[q.question] || "")}
              disabled={!(otherText[q.question] || "").trim()}
            >
              Set
            </button>
          </div>
        </div>
      ))}
      <button
        className="question-submit"
        disabled={!allAnswered}
        onClick={() => onAnswer(requestId, answers)}
      >
        Submit answers
      </button>
    </div>
  );
}

export default function TranscriptPane() {
  const { send, addListener } = useSocket();
  const [entries, setEntries] = useState([]);
  const [pending, setPending] = useState(null);
  const [draft, setDraft] = useState("");
  const scrollRef = useRef(null);
  const keyCounter = useRef(0);

  useEffect(() => {
    const offSnapshot = addListener("transcript:snapshot", (msg) => {
      keyCounter.current = msg.entries.length;
      setEntries(msg.entries.map((e, i) => ({ ...e, _key: i })));
    });
    const offEvent = addListener("transcript:event", (msg) => {
      const key = keyCounter.current++;
      setEntries((prev) => [...prev, { ...msg.entry, _key: key }]);
    });
    const offQuestion = addListener("question:ask", (msg) => {
      setPending({ requestId: msg.requestId, questions: msg.questions });
    });
    return () => {
      offSnapshot();
      offEvent();
      offQuestion();
    };
  }, [addListener]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [entries, pending]);

  function promote(text) {
    send({ type: "message:send", text });
  }

  function answerQuestion(requestId, answers) {
    send({ type: "question:answer", requestId, answers });
    setPending(null);
  }

  function sendDraft() {
    if (!draft.trim()) return;
    send({ type: "message:send", text: draft });
    setDraft("");
  }

  return (
    <div className="chat-pane">
      <div className="chat-scroll" ref={scrollRef}>
        {entries.map((entry) => (
          <Card key={entry._key} entry={entry} onPromote={promote} />
        ))}
        {pending && (
          <QuestionCard
            requestId={pending.requestId}
            questions={pending.questions}
            onAnswer={answerQuestion}
          />
        )}
      </div>
      <div className="chat-input">
        <textarea
          value={draft}
          placeholder="Message…"
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              sendDraft();
            }
          }}
        />
        <button onClick={sendDraft} disabled={!draft.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

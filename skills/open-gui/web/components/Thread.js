"use client";

import Markdown from "./Markdown";
import LiveQuestionCard from "./LiveQuestionCard";

// Shared thread renderer, embedded inside every canvas card AND
// DetailSidebar (design.md D12). A card's ask/answer content and its
// thread are visually one card (user: "把 ask 和 answer 放恣同一張卡片上就
// 好"). `limit` renders only the last N entries — the compact card view
// shows just the latest response (user: "card 顯示最後的回應"); the sidebar
// passes no limit for the full history ("focus card 的時候，可以用邊欄
// layout 顯示那一段的完整過程"). No promote-to-tree control — dropped as
// unneeded once #[id]-tagged routing already places discussion on the
// right card.

function ThreadEntry({ entry }) {
  if (entry.kind === "system") {
    return <div className="thread-entry thread-entry-system">{entry.text}</div>;
  }
  return (
    <div className={`thread-entry thread-entry-${entry.kind}`}>
      {entry.kind === "assistant" ? (
        <Markdown text={entry.text} />
      ) : (
        <div className="tool-use-summary">
          <span className="tool-use-name">{entry.tool}</span>
          <span className="tool-use-detail">{entry.summary}</span>
        </div>
      )}
    </div>
  );
}

export default function Thread({ entries, limit, pendingQuestion, onAnswerQuestion }) {
  const shown = limit ? entries.slice(-limit) : entries;
  return (
    <div className="thread">
      {shown.map((entry) => (
        <ThreadEntry key={entry._key} entry={entry} />
      ))}
      {pendingQuestion && (
        <LiveQuestionCard
          requestId={pendingQuestion.requestId}
          questions={pendingQuestion.questions}
          onAnswer={onAnswerQuestion}
        />
      )}
    </div>
  );
}

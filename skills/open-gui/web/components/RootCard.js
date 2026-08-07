"use client";

import { Handle, Position } from "@xyflow/react";
import CardBody from "./CardBody";
import Thread from "./Thread";

// The canvas's always-present root card — the graph's anchor and the home
// for every untagged transcript entry (general chat, unlabeled tool-use/
// exploration) and any AskUserQuestion call that didn't resolve to a
// specific node (lib/tagRouting.js). Session-level controls (message input,
// 定案/Stop) live in fixed chrome outside the canvas instead (Navbar.js,
// ChatBar.js). Shows only its latest entry (design.md D12, user: "card 顯示
// 最後的回應") — the full history is DetailSidebar's job once this card is
// focused.
export default function RootCard({ id, data }) {
  const { thread, pendingQuestion, focused, onFocus } = data;

  return (
    <div
      className={`canvas-card canvas-card-root${focused ? " canvas-card-focused" : ""}`}
      data-card-id={id}
      onClick={onFocus}
    >
      <Handle type="source" position={Position.Bottom} />
      <div className="canvas-card-header">
        <span className="canvas-card-title">General</span>
        {pendingQuestion && <span className="pending-badge">?</span>}
      </div>
      <CardBody>
        <Thread entries={thread} limit={1} />
      </CardBody>
    </div>
  );
}

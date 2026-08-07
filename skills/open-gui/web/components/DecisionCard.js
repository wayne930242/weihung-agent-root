"use client";

import { Handle, Position } from "@xyflow/react";
import CardBody from "./CardBody";
import FreeTextBox from "./FreeTextBox";
import StatusBadge from "./StatusBadge";
import NodeTypeIcon from "./NodeTypeIcon";
import { usePreview } from "./PreviewProvider";
import { useSocket } from "./SocketProvider";
import { cn } from "../lib/cn";

// Ask (recommendation) and answer (resolution) on one card (user: "把 ask
// 和 answer 放恣同一張卡片上就好") plus a "重新考慮" control once resolved (see
// NODE-FORMAT.md, design.md D12). #[id]-routed follow-up replies no longer
// render inline here — each is its own chained ThreadEntryCard beneath this
// one instead (design.md D12's later revision).
export default function DecisionCard({ id, data }) {
  const { send } = useSocket();
  const { openPreview } = usePreview();
  const { node, pendingQuestion, focused, onFocus } = data;
  const resolved = node.status === "resolved";

  function reconsider() {
    // Carries the previous resolution along so the agent's next message can
    // withdraw that specific conclusion with context, not just "reconsider
    // this" with nothing to reconsider FROM (user: "重新考慮只需要把前一題的
    // 結論帶脈絡重送，並且表示撤回前輪就好").
    send({ type: "node:reconsider", nodeId: node.id, title: node.title, previousResolution: node.resolution });
  }

  return (
    <div
      className={cn("canvas-card", "canvas-card-decision", "nodrag", "nopan", focused && "canvas-card-focused")}
      data-card-id={id}
      onClick={onFocus}
    >
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <div className="canvas-card-header">
        <NodeTypeIcon type="decision" />
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
        <p className="node-recommendation">{node.recommendation}</p>
        {resolved && <p className="node-resolution">{node.resolution}</p>}
        {node.doc && (
          <button className="node-doc-link nodrag nopan" onClick={() => openPreview(node.doc)}>
            View doc →
          </button>
        )}
      </CardBody>
      <div className="canvas-card-footer">
        <FreeTextBox node={node} />
      </div>
    </div>
  );
}

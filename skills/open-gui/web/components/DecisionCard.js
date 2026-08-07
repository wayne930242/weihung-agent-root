"use client";

import { Handle, Position } from "@xyflow/react";
import CardBody from "./CardBody";
import Thread from "./Thread";
import FreeTextBox from "./FreeTextBox";
import StatusBadge from "./StatusBadge";
import NodeTypeIcon from "./NodeTypeIcon";
import { usePreview } from "./PreviewProvider";
import { useSocket } from "./SocketProvider";

// Ask (recommendation) and answer (resolution) on one card (user: "把 ask
// 和 answer 放恣同一張卡片上就好"), a "重新考慮" control once resolved (see
// NODE-FORMAT.md, design.md D12), and only its latest #[id]-routed thread
// entry (user: "card 顯示最後的回應") — the full history and any live
// pending question render in DetailSidebar once this card is focused.
export default function DecisionCard({ id, data }) {
  const { send } = useSocket();
  const { openPreview } = usePreview();
  const { node, thread, pendingQuestion, focused, onFocus } = data;
  const resolved = node.status === "resolved";

  function reconsider() {
    send({ type: "node:reconsider", nodeId: node.id, title: node.title });
  }

  return (
    <div
      className={`canvas-card canvas-card-decision${focused ? " canvas-card-focused" : ""}`}
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
        <Thread entries={thread} limit={1} />
      </CardBody>
      <div className="canvas-card-footer">
        <FreeTextBox node={node} />
      </div>
    </div>
  );
}

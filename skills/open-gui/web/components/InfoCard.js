"use client";

import { Handle, Position } from "@xyflow/react";
import CardBody from "./CardBody";
import Thread from "./Thread";
import FreeTextBox from "./FreeTextBox";
import Markdown from "./Markdown";
import NodeTypeIcon from "./NodeTypeIcon";

export default function InfoCard({ id, data }) {
  const { node, thread, pendingQuestion, focused, onFocus } = data;

  return (
    <div
      className={`canvas-card canvas-card-info${focused ? " canvas-card-focused" : ""}`}
      data-card-id={id}
      onClick={onFocus}
    >
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <div className="canvas-card-header">
        <NodeTypeIcon type="info" />
        <span className="canvas-card-title">{node.title}</span>
        {pendingQuestion && <span className="pending-badge">?</span>}
      </div>
      <CardBody>
        <Markdown text={node.text} />
        <Thread entries={thread} limit={1} />
      </CardBody>
      <div className="canvas-card-footer">
        <FreeTextBox node={node} placeholder="Add a note…" />
      </div>
    </div>
  );
}

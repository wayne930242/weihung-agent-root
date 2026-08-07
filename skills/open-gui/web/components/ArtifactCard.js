"use client";

import { Handle, Position } from "@xyflow/react";
import CardBody from "./CardBody";
import Thread from "./Thread";
import FreeTextBox from "./FreeTextBox";
import NodeTypeIcon from "./NodeTypeIcon";
import { usePreview } from "./PreviewProvider";

// NODE-FORMAT.md: `kind` defaults to "file" (local path, previewed via the
// existing preview:request/preview:response flow). "url" iframes a
// claude.ai artifact link directly. Shows only its latest thread entry
// (design.md D12) — full history/live pending questions are DetailSidebar's
// job once focused.
export default function ArtifactCard({ id, data }) {
  const { openPreview } = usePreview();
  const { node, thread, pendingQuestion, focused, onFocus } = data;
  const kind = node.kind ?? "file";

  return (
    <div
      className={`canvas-card canvas-card-artifact${focused ? " canvas-card-focused" : ""}`}
      data-card-id={id}
      onClick={onFocus}
    >
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <div className="canvas-card-header">
        <NodeTypeIcon type="artifact" />
        <span className="canvas-card-title">{node.title}</span>
        {pendingQuestion && <span className="pending-badge">?</span>}
      </div>
      <CardBody>
        {node.caption && <p className="node-caption">{node.caption}</p>}
        {kind === "url" ? (
          <div className="artifact-embed">
            <div className="artifact-embed-header">
              <span className="preview-path">{node.url}</span>
              <button
                className="nodrag nopan"
                onClick={() => window.open(node.url, "_blank", "noopener,noreferrer")}
              >
                Open in new tab ↗
              </button>
            </div>
            <iframe className="artifact-iframe nodrag nopan nowheel" src={node.url} title={node.title} />
          </div>
        ) : (
          <button className="node-doc-link nodrag nopan" onClick={() => openPreview(node.path)}>
            Preview {node.path}
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

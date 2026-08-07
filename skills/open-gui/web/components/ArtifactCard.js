"use client";

import { Handle, Position } from "@xyflow/react";
import CardBody from "./CardBody";
import FreeTextBox from "./FreeTextBox";
import NodeTypeIcon from "./NodeTypeIcon";
import { usePreview } from "./PreviewProvider";
import { cn } from "../lib/cn";

// NODE-FORMAT.md: `kind` defaults to "file" (local path, previewed via the
// existing preview:request/preview:response flow). "url" iframes a
// claude.ai artifact link directly. #[id]-routed follow-up replies render as
// their own chained ThreadEntryCard beneath this one (design.md D12's later
// revision), not inline here.
export default function ArtifactCard({ id, data }) {
  const { openPreview } = usePreview();
  const { node, pendingQuestion, focused, onFocus } = data;
  const kind = node.kind ?? "file";

  return (
    <div
      className={cn("canvas-card", "canvas-card-artifact", "nodrag", "nopan", focused && "canvas-card-focused")}
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
      </CardBody>
      <div className="canvas-card-footer">
        <FreeTextBox node={node} />
      </div>
    </div>
  );
}

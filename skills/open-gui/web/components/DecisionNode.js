"use client";

import StatusBadge from "./StatusBadge";
import FreeTextBox from "./FreeTextBox";
import { usePreview } from "./PreviewProvider";

export default function DecisionNode({ node, onSubmit }) {
  const { openPreview } = usePreview();
  return (
    <div className="node-body node-decision">
      <StatusBadge status={node.status} />
      {node.status !== "resolved" && (
        <p className="node-recommendation">{node.recommendation}</p>
      )}
      {node.status === "resolved" && (
        <p className="node-resolution">{node.resolution}</p>
      )}
      {node.doc && (
        <button className="node-doc-link" onClick={() => openPreview(node.doc)}>
          View doc →
        </button>
      )}
      <FreeTextBox node={node} onSubmit={onSubmit} />
    </div>
  );
}

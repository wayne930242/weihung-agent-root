"use client";

import FreeTextBox from "./FreeTextBox";
import { usePreview } from "./PreviewProvider";

// NODE-FORMAT.md: `kind` defaults to "file" (local path, previewed via the
// existing preview:request/preview:response flow). "url" iframes a
// claude.ai artifact link directly — no preview-panel round trip, since the
// browser can load a cross-origin URL in an iframe on its own. A private
// (non-shared) artifact will show claude.ai's own login wall inside the
// iframe rather than the artifact content; that's an accepted trade-off,
// not a bug — expand-in-new-tab still gets the user to a real sign-in flow.
export default function ArtifactNode({ node, onSubmit }) {
  const { openPreview } = usePreview();
  const kind = node.kind ?? "file";

  return (
    <div className="node-body node-artifact">
      {node.caption && <p className="node-caption">{node.caption}</p>}
      {kind === "url" ? (
        <div className="artifact-embed">
          <div className="artifact-embed-header">
            <span className="preview-path">{node.url}</span>
            <button
              onClick={() => window.open(node.url, "_blank", "noopener,noreferrer")}
            >
              Open in new tab ↗
            </button>
          </div>
          <iframe className="artifact-iframe" src={node.url} title={node.title} />
        </div>
      ) : (
        <button className="node-doc-link" onClick={() => openPreview(node.path)}>
          Preview {node.path}
        </button>
      )}
      <FreeTextBox node={node} onSubmit={onSubmit} />
    </div>
  );
}

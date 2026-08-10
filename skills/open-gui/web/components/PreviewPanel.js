"use client";

import { useEffect } from "react";
import { usePreview } from "./PreviewProvider";
import Markdown from "./Markdown";

export default function PreviewPanel() {
  const { open, path, loading, content, error, closePreview } = usePreview();

  // The shortcut-hints bar and CanvasView's own keydown handler both
  // advertise "Esc back", but CanvasView's Escape case only blurs a
  // focused input — nothing there ever closed this overlay.
  useEffect(() => {
    if (!open) return;
    function handleKeyDown(e) {
      if (e.key === "Escape") closePreview();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, closePreview]);

  if (!open) return null;

  const isMarkdown = path?.toLowerCase().endsWith(".md");

  return (
    <div className="preview-overlay" onClick={closePreview}>
      <div className="preview-panel" onClick={(e) => e.stopPropagation()}>
        <div className="preview-header">
          <span className="preview-path">{path}</span>
          <button
            className="preview-close"
            onClick={closePreview}
            aria-label="Close preview"
          >
            ×
          </button>
        </div>
        <div className="preview-body">
          {loading && <p className="dim">Loading…</p>}
          {error && <p className="preview-error">{error}</p>}
          {!loading && !error && content != null && (
            isMarkdown ? (
              <Markdown text={content} />
            ) : (
              <pre className="preview-pre">{content}</pre>
            )
          )}
        </div>
      </div>
    </div>
  );
}

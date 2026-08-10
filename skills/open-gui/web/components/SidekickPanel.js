"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "../lib/cn";

// Visible pending-message queue, docked LEFT — the mirror of DetailSidebar
// (docked right), but a resizable splitter rather than a fixed-width panel
// (user: "left pane 不要做成 dialog 類型的，要做成 spliter") since watching
// and managing a queue is an ongoing task, not a glance-and-close lookup.
// Renders nothing when the queue is empty, same principle DetailSidebar
// already applies ("沒內容的就不用硬要顯示 sidebar 了") — an empty queue has
// nothing to show or manage.
const MIN_WIDTH = 200;
const MAX_WIDTH = 480;
const DEFAULT_WIDTH = 280;

export default function SidekickPanel({ queue, onCancel }) {
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const draggingRef = useRef(false);

  const onHandlePointerDown = useCallback((e) => {
    e.preventDefault();
    draggingRef.current = true;
  }, []);

  useEffect(() => {
    function onMove(e) {
      if (!draggingRef.current) return;
      setWidth(Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, e.clientX)));
    }
    function onUp() {
      draggingRef.current = false;
    }
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, []);

  if (queue.length === 0) return null;

  return (
    <div className="sidekick-panel nodrag nopan" style={{ width }}>
      <div className="sidekick-panel-header">
        <span className="sidekick-panel-title">思考佇列 ({queue.length})</span>
      </div>
      <div className="sidekick-panel-body">
        {queue.map((item, i) => (
          <div key={item.id} className="sidekick-panel-entry">
            <span className="sidekick-panel-entry-index">{i === 0 ? "…" : i + 1}</span>
            <div className="sidekick-panel-entry-body">
              <span className="sidekick-panel-entry-label">{item.label}</span>
              <span className="sidekick-panel-entry-text">{item.preview}</span>
            </div>
            <button
              className="sidekick-panel-entry-cancel nodrag nopan"
              onClick={() => onCancel(item.id)}
              aria-label="Cancel"
              title="Cancel — remove before it's sent"
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <div
        className={cn("sidekick-panel-resize-handle", "nodrag", "nopan")}
        onPointerDown={onHandlePointerDown}
      />
    </div>
  );
}

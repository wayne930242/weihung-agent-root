"use client";

import { useCallback, useRef, useState } from "react";
import TranscriptPane from "./TranscriptPane";
import TreePanel from "./TreePanel";

const MIN_PCT = 30;
const MAX_PCT = 80;
// The tree panel is the point of this tool (op-sec decision-tree navigation);
// the terminal only needs to stay usable for reading/typing. Default the
// split so the tree (100 - INITIAL_LEFT_PCT) gets the majority of the width;
// the divider still lets the user drag it further either way.
const INITIAL_LEFT_PCT = 35;

export default function SplitView() {
  const containerRef = useRef(null);
  const [leftPct, setLeftPct] = useState(INITIAL_LEFT_PCT);
  const draggingRef = useRef(false);

  const onPointerMove = useCallback((e) => {
    if (!draggingRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const pct = ((e.clientX - rect.left) / rect.width) * 100;
    setLeftPct(Math.min(MAX_PCT, Math.max(MIN_PCT, pct)));
  }, []);

  const stopDrag = useCallback(() => {
    draggingRef.current = false;
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", stopDrag);
  }, [onPointerMove]);

  const startDrag = useCallback(
    (e) => {
      e.preventDefault();
      draggingRef.current = true;
      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", stopDrag);
    },
    [onPointerMove, stopDrag],
  );

  return (
    <div className="split-view" ref={containerRef}>
      <div className="pane pane-chat" style={{ flexBasis: `${leftPct}%` }}>
        <TranscriptPane />
      </div>
      <div
        className="split-divider"
        onPointerDown={startDrag}
        role="separator"
        aria-orientation="vertical"
      />
      <div
        className="pane pane-tree"
        style={{ flexBasis: `${100 - leftPct}%` }}
      >
        <TreePanel />
      </div>
    </div>
  );
}

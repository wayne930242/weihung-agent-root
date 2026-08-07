"use client";

import { useEffect, useRef } from "react";

// The scrollable body every canvas card uses. Two things React Flow's own
// canvas would otherwise steal: `nowheel` (a React Flow convention class)
// stops the canvas's pan/zoom handler from capturing wheel events meant for
// this card's own scroll, and the effect below keeps new content in view
// (a card has no linear "bottom" the way the old transcript pane's window
// did, but each card's own body still does — AutoPan in CanvasView.js only
// handles panning the viewport TO the card, not scrolling within it).
export default function CardBody({ children }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (el) el.scrollTop = el.scrollHeight;
  });
  return (
    <div className="canvas-card-body nowheel" ref={ref}>
      {children}
    </div>
  );
}

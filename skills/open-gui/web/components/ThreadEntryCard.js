"use client";

import { Handle, Position } from "@xyflow/react";
import CardBody from "./CardBody";
import Thread from "./Thread";
import FreeTextBox from "./FreeTextBox";
import { cn } from "../lib/cn";

// A single follow-up reply, chained downward under whichever card in its
// branch most recently received one — never written to `TREE.json` (design.md
// D12 revision, user: "所有回應都應該往下疊加... 像是討論從此往下"). Purely a
// render-time chain over already `#[id]`-tag-routed thread entries
// (CanvasView.js's `threadsByTarget`); D4's "Claude alone authors TREE.json"
// is unaffected — this only decides which entry renders under which card.
// Has its own header (user: "又不能往下問，看不懂" — an unlabeled, dead-end
// card read as confusing/broken) and its own reply box, routed via
// `originNode` — the real TREE.json node this chain hangs off, since a
// chain card has no id of its own for Claude to tag a reply back onto.
export default function ThreadEntryCard({ id, data }) {
  const { entry, originNode, focused, onFocus } = data;
  return (
    <div
      className={cn("canvas-card", "canvas-card-reply", "nodrag", "nopan", focused && "canvas-card-focused")}
      data-card-id={id}
      onClick={onFocus}
    >
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <div className="canvas-card-header">
        <span className="canvas-card-title">Reply</span>
      </div>
      <CardBody>
        <Thread entries={[entry]} />
      </CardBody>
      <div className="canvas-card-footer">
        <FreeTextBox node={originNode} />
      </div>
    </div>
  );
}

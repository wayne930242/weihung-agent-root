"use client";

import NodeTypeIcon from "./NodeTypeIcon";

// One compact row per node — the tree's structural "spine". No node body,
// no reply boxes here; this exists purely so the whole tree's shape is
// visible and navigable at a glance. Nesting depth is conveyed the same way
// a file explorer or `tree` command does it: indentation plus a
// `border-left` per level (`.tree-children` in globals.css), not a
// node-graph canvas. Clicking a row selects it; the full content renders in
// the detail pane (see NodeDetail.js / TreePanel.js).

export default function TreeSpine({
  node,
  childrenByParent,
  selectedId,
  onSelect,
  pendingIds,
}) {
  const children = childrenByParent.get(node.id) ?? [];
  const hasStatus = node.type === "decision" || node.type === "question";
  const isSelected = node.id === selectedId;
  // Client-side-only pending flag (never in TREE.json) — see TreePanel's
  // pendingSnapshots. Takes visual priority over the node's own status dot
  // since it reflects the more recent event (the user's own submission).
  const isPending = pendingIds?.has(node.id) ?? false;

  return (
    <li className="spine-node">
      <button
        type="button"
        className={`spine-row${isSelected ? " spine-row-selected" : ""}`}
        onClick={() => onSelect(node.id)}
      >
        <NodeTypeIcon type={node.type} />
        <span className={`node-type-tag node-type-${node.type}`}>
          {node.type}
        </span>
        <span className="spine-title">{node.title}</span>
        {isPending ? (
          <span className="spine-status-dot spine-status-pending" title="pending" />
        ) : (
          hasStatus &&
          node.status && (
            <span
              className={`spine-status-dot spine-status-${node.status}`}
              title={node.status}
            />
          )
        )}
      </button>
      {children.length > 0 && (
        <ul className="tree-children">
          {children.map((child) => (
            <TreeSpine
              key={child.id}
              node={child}
              childrenByParent={childrenByParent}
              selectedId={selectedId}
              onSelect={onSelect}
              pendingIds={pendingIds}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

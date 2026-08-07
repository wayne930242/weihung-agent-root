"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSocket } from "./SocketProvider";
import TreeSpine from "./TreeSpine";
import NodeDetail from "./NodeDetail";
import ThemeToggle from "./ThemeToggle";

export default function TreePanel() {
  const { addListener } = useSocket();
  const [tree, setTree] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  // nodeId -> JSON.stringify(node) snapshot taken at submission time. Purely
  // client-side "pending" tracking (spec: "Optimistic pending indicator for
  // in-flight submissions") — never written to TREE.json. Cleared once a
  // tree:update shows that node's own data differs from this snapshot.
  const [pendingSnapshots, setPendingSnapshots] = useState(() => new Map());

  useEffect(
    () =>
      addListener("tree:update", (msg) => {
        setTree(msg.tree);
        setPendingSnapshots((prev) => {
          if (prev.size === 0) return prev;
          const byId = new Map((msg.tree?.nodes ?? []).map((n) => [n.id, n]));
          let changed = false;
          const next = new Map(prev);
          for (const [id, snapshot] of prev) {
            const current = byId.get(id);
            const currentJson = current ? JSON.stringify(current) : null;
            if (currentJson !== snapshot) {
              next.delete(id);
              changed = true;
            }
          }
          return changed ? next : prev;
        });
      }),
    [addListener],
  );

  const { roots, childrenByParent, nodesById } = useMemo(() => {
    const nodes = tree?.nodes ?? [];
    const ids = new Set(nodes.map((n) => n.id));
    const childrenByParent = new Map();
    const nodesById = new Map();
    const roots = [];
    for (const node of nodes) {
      nodesById.set(node.id, node);
      const hasKnownParent = node.parent !== null && ids.has(node.parent);
      if (hasKnownParent) {
        if (!childrenByParent.has(node.parent)) {
          childrenByParent.set(node.parent, []);
        }
        childrenByParent.get(node.parent).push(node);
      } else {
        roots.push(node);
      }
    }
    return { roots, childrenByParent, nodesById };
  }, [tree]);

  // Flattened depth-first order of every visible spine row, for j/k/arrow
  // stepping. The spine has no collapse/expand state — everything renders
  // expanded — so this is just a full depth-first walk of roots/children.
  const flatIds = useMemo(() => {
    const order = [];
    const visit = (nodes) => {
      for (const node of nodes) {
        order.push(node.id);
        const children = childrenByParent.get(node.id) ?? [];
        if (children.length > 0) visit(children);
      }
    };
    visit(roots);
    return order;
  }, [roots, childrenByParent]);

  // Auto-select the newest node the first time any node exists, so the
  // detail pane opens on something rather than an empty placeholder. Once
  // the user (or this effect) has made a selection, this never re-fires —
  // design.md D11: there's no "live/urgent" node to chase anymore (questions
  // live in the transcript pane, not the tree), so unlike the old frontier
  // logic this never re-selects on later tree:update events.
  useEffect(() => {
    if (selectedId === null && flatIds.length > 0) {
      setSelectedId(flatIds[flatIds.length - 1]);
    }
  }, [flatIds, selectedId]);

  // Spec: "SHALL NOT intercept these keys while focus is inside a text input
  // or textarea" — a document-level listener is simpler and more robust here
  // than manual focus/tabindex management on every spine row.
  useEffect(() => {
    function handleKeyDown(e) {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      let delta = 0;
      if (e.key === "j" || e.key === "ArrowDown") delta = 1;
      else if (e.key === "k" || e.key === "ArrowUp") delta = -1;
      else return;
      if (flatIds.length === 0) return;
      e.preventDefault();
      setSelectedId((current) => {
        const idx = flatIds.indexOf(current);
        const nextIdx =
          idx === -1 ? 0 : Math.min(Math.max(idx + delta, 0), flatIds.length - 1);
        return flatIds[nextIdx];
      });
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [flatIds]);

  // Called by a node's detail-pane submit action with that node's id. Snapshots
  // the node's current (pre-submission) data so a later tree:update can detect
  // whether that specific node changed.
  const markPending = useCallback(
    (nodeId) => {
      const node = nodesById.get(nodeId);
      if (!node) return;
      setPendingSnapshots((prev) => {
        const next = new Map(prev);
        next.set(nodeId, JSON.stringify(node));
        return next;
      });
    },
    [nodesById],
  );

  const pendingIds = useMemo(
    () => new Set(pendingSnapshots.keys()),
    [pendingSnapshots],
  );

  const selectedNode = selectedId ? (nodesById.get(selectedId) ?? null) : null;

  return (
    <div className="tree-pane">
      <div className="tree-header">
        <span className="tree-topic">{tree?.topic || "open-gui"}</span>
        <div className="tree-header-right">
          {tree?.status && (
            <span className={`tree-status tree-status-${tree.status}`}>
              {tree.status}
            </span>
          )}
          <ThemeToggle />
        </div>
      </div>
      {roots.length === 0 ? (
        <p className="tree-empty">No nodes yet.</p>
      ) : (
        <div className="tree-master-detail">
          <div className="tree-spine">
            <ul className="tree-root-list">
              {roots.map((node) => (
                <TreeSpine
                  key={node.id}
                  node={node}
                  childrenByParent={childrenByParent}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                  pendingIds={pendingIds}
                />
              ))}
            </ul>
          </div>
          <div className="tree-detail">
            <NodeDetail
              node={selectedNode}
              isPending={selectedId ? pendingIds.has(selectedId) : false}
              markPending={markPending}
            />
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSocket } from "./SocketProvider";
import TreeSpine from "./TreeSpine";
import NodeDetail from "./NodeDetail";
import ThemeToggle from "./ThemeToggle";

// Depth-first spine order computed directly from a TreeDoc, standalone from
// the memoized `flatIds` below — needed inside the tree:update handler,
// where the new tree hasn't gone through a render/memo cycle yet.
function computeFlatIds(treeDoc) {
  const nodes = treeDoc?.nodes ?? [];
  const ids = new Set(nodes.map((n) => n.id));
  const childrenByParent = new Map();
  const roots = [];
  for (const node of nodes) {
    const hasKnownParent = node.parent !== null && ids.has(node.parent);
    if (hasKnownParent) {
      if (!childrenByParent.has(node.parent)) childrenByParent.set(node.parent, []);
      childrenByParent.get(node.parent).push(node);
    } else {
      roots.push(node);
    }
  }
  const order = [];
  const visit = (list) => {
    for (const node of list) {
      order.push(node.id);
      const children = childrenByParent.get(node.id) ?? [];
      if (children.length > 0) visit(children);
    }
  };
  visit(roots);
  return order;
}

// "The thing to look at right now": the first still-open decision/question
// in spine order, since a grilling interview isn't strictly append-then-
// resolve-in-array-order — branches can resolve out of sequence (observed
// live: the last-added node resolved before an earlier one did). Array
// position alone is not a reliable proxy for "currently active." Falls back
// to the newest node (last in spine order) once nothing is open.
function findFrontierId(treeDoc, flatIds) {
  const nodesById = new Map((treeDoc?.nodes ?? []).map((n) => [n.id, n]));
  for (const id of flatIds) {
    if (nodesById.get(id)?.status === "open") return id;
  }
  return flatIds.length > 0 ? flatIds[flatIds.length - 1] : null;
}

export default function TreePanel() {
  const { addListener } = useSocket();
  const [tree, setTree] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  // Refs mirroring selectedId/the current frontier for the tree:update
  // listener below, which is registered once (addListener runs in an effect
  // keyed only on `addListener`) and would otherwise close over stale values.
  const selectedIdRef = useRef(null);
  const frontierIdRef = useRef(null);
  // nodeId -> JSON.stringify(node) snapshot taken at submission time. Purely
  // client-side "pending" tracking (spec: "Optimistic pending indicator for
  // in-flight submissions") — never written to TREE.json. Cleared once a
  // tree:update shows that node's own data differs from this snapshot.
  const [pendingSnapshots, setPendingSnapshots] = useState(() => new Map());

  useEffect(
    () =>
      addListener("tree:update", (msg) => {
        // Auto-advance: if the user was looking at the frontier (the first
        // open node, or the newest node if nothing's open) when this update
        // arrives, follow the new frontier — that's "the next thing" in a
        // live interview. If they'd navigated away to an earlier node, leave
        // the selection alone; don't yank them off something they're
        // deliberately reviewing.
        const wasAtFrontier =
          selectedIdRef.current !== null && selectedIdRef.current === frontierIdRef.current;
        if (wasAtFrontier) {
          const newFlatIds = computeFlatIds(msg.tree);
          const newFrontier = findFrontierId(msg.tree, newFlatIds);
          if (newFrontier && newFrontier !== selectedIdRef.current) {
            setSelectedId(newFrontier);
          }
        }
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

  // Auto-select the frontier (first open node, else the newest) the first
  // time any node exists — on load/reload this is "whatever the interview
  // is currently doing," not just the first thing chronologically, so the
  // detail pane opens on the live question rather than old history. Once
  // the user (or this effect) has made a selection, this never re-fires;
  // staying on the frontier as further nodes arrive is the tree:update
  // handler's job (the auto-advance logic above), not this one.
  useEffect(() => {
    if (selectedId === null && flatIds.length > 0) {
      setSelectedId(findFrontierId(tree, flatIds));
    }
  }, [tree, flatIds, selectedId]);

  // Keep the refs the tree:update listener reads in sync with actual state —
  // that listener is registered once and would otherwise see stale values.
  useEffect(() => {
    selectedIdRef.current = selectedId;
  }, [selectedId]);
  useEffect(() => {
    frontierIdRef.current = flatIds.length > 0 ? findFrontierId(tree, flatIds) : null;
  }, [tree, flatIds]);

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

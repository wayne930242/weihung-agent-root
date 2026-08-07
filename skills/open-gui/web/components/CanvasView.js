"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ReactFlow, ReactFlowProvider, Background, Controls, useReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useSocket } from "./SocketProvider";
import RootCard from "./RootCard";
import DecisionCard from "./DecisionCard";
import ArtifactCard from "./ArtifactCard";
import InfoCard from "./InfoCard";
import QuestionTreeCard from "./QuestionTreeCard";
import Navbar from "./Navbar";
import ChatBar from "./ChatBar";
import DetailSidebar from "./DetailSidebar";
import { routeTaggedText, routeQuestion } from "../lib/tagRouting";
import { layoutTree, CARD_WIDTH, CARD_HEIGHT } from "../lib/layout";

// design.md D12: replaces the split-view (transcript pane + tree spine/
// detail) with a single top-down node-graph canvas — the tree is the
// primary view, not a side panel. Session-level controls (message input,
// 定案/Stop, theme) live in fixed chrome (Navbar/ChatBar) outside the
// pannable canvas, not inside a card. `#[id]`-tagged assistant text routes
// into the discussing node's own card (lib/tagRouting.js); everything else
// hangs off the root card. Each card shows only its latest entry —
// DetailSidebar shows the focused card's full history plus, for a live
// question, the actual interactive answering UI.

const ROOT_ID = "__root__";

// assistant text is Claude's own #[id]-tagged replies; system entries are
// this browser's own echoes of what it just sent (buildSubmission, node:
// reconsider) which use the same tag convention (lib/submission.js) so a
// card's own submission routes back onto that same card. tool_use entries
// have no freeform text a tag could live in, so they're never checked.
function isTaggable(entry) {
  return entry.kind === "assistant" || entry.kind === "system";
}

const NODE_TYPES = {
  root: RootCard,
  decision: DecisionCard,
  artifact: ArtifactCard,
  info: InfoCard,
  question: QuestionTreeCard,
};

// Pans the viewport to whichever card is focused — a canvas has no linear
// "bottom" to auto-scroll to like the old transcript pane did (user: "新訊息
// 來記得要 scroll canvas").
function AutoPan({ activeNodeId, nodes }) {
  const { setCenter } = useReactFlow();
  useEffect(() => {
    if (!activeNodeId) return;
    const node = nodes.find((n) => n.id === activeNodeId);
    if (!node) return;
    const x = node.position.x + CARD_WIDTH / 2;
    const y = node.position.y + CARD_HEIGHT / 2;
    setCenter(x, y, { zoom: 1, duration: 400 });
  }, [activeNodeId, nodes, setCenter]);
  return null;
}

export default function CanvasView() {
  const { addListener, theme } = useSocket();
  const [tree, setTree] = useState(null);
  const [entries, setEntries] = useState([]);
  const [pendingRaw, setPendingRaw] = useState(null); // {requestId, questions} | null
  const [lastEntryTarget, setLastEntryTarget] = useState(null);
  // Explicit click/Tab focus — wins over auto-drift so looking around
  // doesn't fight the user, but a genuinely NEW question still reclaims it
  // (see the requestId-keyed effect below).
  const [manualFocusId, setManualFocusId] = useState(null);
  const keyCounter = useRef(0);
  const prevEntriesLengthRef = useRef(0);

  useEffect(() => {
    const offTree = addListener("tree:update", (msg) => setTree(msg.tree));
    const offSnapshot = addListener("transcript:snapshot", (msg) => {
      keyCounter.current = msg.entries.length;
      setEntries(msg.entries.map((e, i) => ({ ...e, _key: i })));
    });
    const offEvent = addListener("transcript:event", (msg) => {
      const key = keyCounter.current++;
      setEntries((prev) => [...prev, { ...msg.entry, _key: key }]);
    });
    const offQuestion = addListener("question:ask", (msg) => {
      setPendingRaw({ requestId: msg.requestId, questions: msg.questions });
    });
    // The answering browser already clears optimistically (LiveQuestionCard
    // callers below); this is what clears it for every OTHER connected
    // browser, and is the authoritative clear either way — there's no
    // other signal that a pending question stopped being pending.
    const offResolved = addListener("question:resolved", (msg) => {
      setPendingRaw((prev) => (prev?.requestId === msg.requestId ? null : prev));
    });
    return () => {
      offTree();
      offSnapshot();
      offEvent();
      offQuestion();
      offResolved();
    };
  }, [addListener]);

  const nodesById = useMemo(() => {
    const m = new Map();
    for (const n of tree?.nodes ?? []) m.set(n.id, n);
    return m;
  }, [tree]);

  // Tracks which card most recently got new content — the fallback
  // AutoPan target when nothing is pending/manually focused. Guarded on
  // entries actually growing (not just nodesById changing) so this doesn't
  // re-fire on every unrelated tree:update.
  useEffect(() => {
    if (entries.length > prevEntriesLengthRef.current) {
      const last = entries[entries.length - 1];
      if (isTaggable(last)) {
        const { targetNodeId } = routeTaggedText(last.text, nodesById);
        setLastEntryTarget(targetNodeId ?? ROOT_ID);
      } else {
        setLastEntryTarget(ROOT_ID);
      }
    }
    prevEntriesLengthRef.current = entries.length;
  }, [entries, nodesById]);

  const pendingTargetNodeId = useMemo(() => {
    if (!pendingRaw) return null;
    const { targetNodeId } = routeQuestion(pendingRaw.questions, nodesById);
    return targetNodeId ?? ROOT_ID;
  }, [pendingRaw, nodesById]);

  // A genuinely new question reclaims focus even if the user had manually
  // looked elsewhere — only a *new* requestId does this, not every render.
  useEffect(() => {
    if (pendingRaw) setManualFocusId(null);
  }, [pendingRaw?.requestId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Priority: explicit user focus > a live pending question > whatever's
  // newest. (user: "focus 應該 focus「還沒 resolve 的問題」而非 root" — but an
  // explicit click/Tab should still be able to look elsewhere on purpose.)
  const activeNodeId = manualFocusId ?? pendingTargetNodeId ?? lastEntryTarget;

  // Buckets every transcript entry fresh from current `tree` state on every
  // change — no stored routing decision that could go stale if a tag's
  // target node appears after the entry itself did.
  const threadsByTarget = useMemo(() => {
    const buckets = new Map();
    buckets.set(ROOT_ID, []);
    for (const n of tree?.nodes ?? []) buckets.set(n.id, []);
    for (const entry of entries) {
      let targetNodeId = ROOT_ID;
      let displayEntry = entry;
      if (isTaggable(entry)) {
        const routed = routeTaggedText(entry.text, nodesById);
        if (routed.targetNodeId) {
          targetNodeId = routed.targetNodeId;
          displayEntry = { ...entry, text: routed.text };
        }
      }
      const bucket = buckets.get(targetNodeId) ?? buckets.get(ROOT_ID);
      bucket.push(displayEntry);
    }
    return buckets;
  }, [entries, nodesById, tree]);

  const pendingByTarget = useMemo(() => {
    if (!pendingRaw || !pendingTargetNodeId) return new Map();
    return new Map([[pendingTargetNodeId, { requestId: pendingRaw.requestId, questions: pendingRaw.questions }]]);
  }, [pendingRaw, pendingTargetNodeId]);

  // No manual dragging (v1): every card is always dagre-positioned, so
  // recomputing layout on every render is safe — nothing to "snap back
  // from." Positions only actually change when tree structure changes;
  // dagre is deterministic, so a data-only re-render reproduces the same
  // coordinates.
  const { nodes, edges } = useMemo(() => {
    const treeNodes = tree?.nodes ?? [];
    const ids = new Set(treeNodes.map((n) => n.id));
    const rfNodes = [{ id: ROOT_ID }, ...treeNodes.map((n) => ({ id: n.id }))];
    const rfEdges = treeNodes.map((n) => {
      const parent = n.parent && ids.has(n.parent) ? n.parent : ROOT_ID;
      return { id: `${parent}->${n.id}`, source: parent, target: n.id };
    });
    const positioned = layoutTree(rfNodes, rfEdges);
    const withData = positioned.map((n) => {
      const focused = n.id === activeNodeId;
      const onFocus = () => setManualFocusId(n.id);
      if (n.id === ROOT_ID) {
        return {
          ...n,
          type: "root",
          data: {
            thread: threadsByTarget.get(ROOT_ID) ?? [],
            pendingQuestion: pendingByTarget.get(ROOT_ID) ?? null,
            focused,
            onFocus,
          },
        };
      }
      const node = nodesById.get(n.id);
      return {
        ...n,
        type: node.type,
        data: {
          node,
          thread: threadsByTarget.get(n.id) ?? [],
          pendingQuestion: pendingByTarget.get(n.id) ?? null,
          focused,
          onFocus,
        },
      };
    });
    return { nodes: withData, edges: rfEdges };
  }, [tree, nodesById, threadsByTarget, pendingByTarget, activeNodeId]);

  // "Needs action": a live pending question, or a persisted `question`-type
  // node still open — the set Tab/Shift+Tab cycles through.
  const actionableIds = useMemo(
    () =>
      nodes
        .filter((n) => n.data.pendingQuestion || (n.data.node?.type === "question" && n.data.node?.status === "open"))
        .map((n) => n.id),
    [nodes],
  );

  useEffect(() => {
    function handleKeyDown(e) {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (e.key === "Tab") {
        if (actionableIds.length === 0) return;
        e.preventDefault();
        const idx = actionableIds.indexOf(manualFocusId ?? activeNodeId);
        const delta = e.shiftKey ? -1 : 1;
        const nextIdx = idx === -1 ? 0 : (idx + delta + actionableIds.length) % actionableIds.length;
        setManualFocusId(actionableIds[nextIdx]);
      } else if (e.key === ":") {
        e.preventDefault();
        document.querySelector(".chat-bar textarea")?.focus();
      } else if (e.key === "/") {
        e.preventDefault();
        document
          .querySelector(`[data-card-id="${activeNodeId}"] .node-freetext textarea, [data-card-id="${activeNodeId}"] .node-other input`)
          ?.focus();
      } else if (e.key === "n" || e.key === "N") {
        e.preventDefault();
        document.querySelector(`[data-card-id="${activeNodeId}"] .node-notes`)?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [actionableIds, manualFocusId, activeNodeId]);

  const focusedData = nodes.find((n) => n.id === activeNodeId)?.data;

  return (
    <div className="canvas-view">
      <Navbar topic={tree?.topic} status={tree?.status} />
      <div className="canvas-flow">
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={NODE_TYPES}
            colorMode={theme === "light" ? "light" : "dark"}
            fitView
            nodesDraggable={false}
            nodesConnectable={false}
          >
            <Background />
            <Controls showInteractive={false} />
          </ReactFlow>
          <AutoPan activeNodeId={activeNodeId} nodes={nodes} />
        </ReactFlowProvider>
        <DetailSidebar
          title={focusedData?.node?.title ?? (activeNodeId === ROOT_ID ? "General" : null)}
          thread={focusedData?.thread ?? []}
          pendingQuestion={focusedData?.pendingQuestion ?? null}
        />
      </div>
      <ChatBar />
    </div>
  );
}

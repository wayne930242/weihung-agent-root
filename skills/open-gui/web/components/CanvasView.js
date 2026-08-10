"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ReactFlow, ReactFlowProvider, Background, Controls, useReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useSocket } from "./SocketProvider";
import RootCard from "./RootCard";
import DecisionCard from "./DecisionCard";
import ArtifactCard from "./ArtifactCard";
import InfoCard from "./InfoCard";
import QuestionTreeCard from "./QuestionTreeCard";
import LiveQuestionCanvasCard from "./LiveQuestionCanvasCard";
import QuestionBatchSubmitCard from "./QuestionBatchSubmitCard";
import ThreadEntryCard from "./ThreadEntryCard";
import Navbar from "./Navbar";
import ChatBar from "./ChatBar";
import DetailSidebar from "./DetailSidebar";
import SidekickPanel from "./SidekickPanel";
import { routeTaggedText, routeQuestions } from "../lib/tagRouting";
import { layoutTree, CARD_WIDTH, CARD_HEIGHT } from "../lib/layout";
import { buildSubmission } from "../lib/submission";

// design.md D12: replaces the split-view (transcript pane + tree spine/
// detail) with a single top-down node-graph canvas — the tree is the
// primary view, not a side panel. Session-level controls (message input,
// 收斂/Stop, theme) live in fixed chrome (Navbar/ChatBar) outside the
// pannable canvas, not inside a card. `#[id]`-tagged assistant text routes
// into the discussing node's own card (lib/tagRouting.js); a node's own
// follow-up replies each chain downward as their own ephemeral card
// (chainTailId below) rather than folding into that card or DetailSidebar —
// everything untagged hangs off the root card instead, which keeps its
// original latest-entry-on-card + full-history-in-DetailSidebar behavior. A
// live AskUserQuestion call renders as one ephemeral card PER QUESTION, each
// parented to whatever it's routed to (user: "三個問題三張卡片，然後都接到
// 上層的 root") — not bundled into one shared answering UI.

const ROOT_ID = "__root__";

// React Flow only ships Tab-cycling (DOM order) and arrow-keys-move-the-
// selected-node (dragging); it has no notion of "jump focus to the nearest
// node in this direction" (confirmed against its own docs). hjkl/arrows
// need actual spatial navigation matching the dagre-computed canvas
// position (user: "和 react flow 的位置要一致") — for each candidate, keep
// only ones within a 45° cone of the requested direction (perpendicular
// offset no larger than the along-direction offset) and take the closest.
function spatialNeighbor(nodes, fromId, dx0, dy0) {
  const from = nodes.find((n) => n.id === fromId);
  if (!from) return null;
  const fx = from.position.x + CARD_WIDTH / 2;
  const fy = from.position.y + CARD_HEIGHT / 2;
  let best = null;
  let bestDist = Infinity;
  for (const n of nodes) {
    if (n.id === fromId) continue;
    const dx = n.position.x + CARD_WIDTH / 2 - fx;
    const dy = n.position.y + CARD_HEIGHT / 2 - fy;
    const along = dx * dx0 + dy * dy0;
    if (along <= 0) continue;
    const perp = Math.abs(dx * dy0 - dy * dx0);
    if (perp > along) continue;
    const dist = Math.hypot(dx, dy);
    if (dist < bestDist) {
      bestDist = dist;
      best = n.id;
    }
  }
  return best;
}

// assistant text is Claude's own #[id]-tagged replies; system entries are
// this browser's own echoes of what it just sent (buildSubmission, node:
// reconsider) which use the same tag convention (lib/submission.js) so a
// card's own submission routes back onto that same card. tool_use entries
// have no freeform text a tag could live in, so they're never checked.
function isTaggable(entry) {
  return entry.kind === "assistant" || entry.kind === "system";
}

// The id of the tail card in `nodeId`'s reply chain — where a new tagged
// reply to that node attaches (design.md D12 revision, user: "所有回應都應該
// 往下疊加... 像是討論從此往下"). Falls back to the node's own id when it has
// no chained replies yet. A node only ever gets tagged by its own id (Claude
// has no way to address a chain card's synthetic id), so appending to
// whatever is currently last in that bucket already is "attach to the branch's
// most-recently-active point" — no separate fan-out rule needed.
function chainTailId(nodeId, threadsByTarget) {
  const thread = threadsByTarget.get(nodeId);
  if (!thread || thread.length === 0) return nodeId;
  return `${nodeId}::reply:${thread.length - 1}`;
}

const NODE_TYPES = {
  root: RootCard,
  decision: DecisionCard,
  artifact: ArtifactCard,
  info: InfoCard,
  question: QuestionTreeCard,
  "live-question": LiveQuestionCanvasCard,
  "question-batch-submit": QuestionBatchSubmitCard,
  reply: ThreadEntryCard,
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
  const { addListener, theme, send } = useSocket();
  const [tree, setTree] = useState(null);
  const [entries, setEntries] = useState([]);
  const [pendingRaw, setPendingRaw] = useState(null); // {requestId, questions} | null
  // Answers collected so far for the current pendingRaw's requestId, keyed
  // by question text — each ephemeral question-card submits its own answer
  // independently; the real `question:answer` only fires once every
  // question in the call has one (the SDK expects one combined answer set).
  const [partialAnswers, setPartialAnswers] = useState({});
  const [lastEntryTarget, setLastEntryTarget] = useState(null);
  // Explicit click/Tab focus — wins over auto-drift so looking around
  // doesn't fight the user, but a genuinely NEW question still reclaims it
  // (see the requestId-keyed effect below).
  const [manualFocusId, setManualFocusId] = useState(null);
  // 收斂 (converge): all cards visually stack into the root card, then the
  // existing finalize flow runs.
  const [converging, setConverging] = useState(false);
  // DetailSidebar's own explicit close, separate from what content it has
  // (blind usability test: once open, there was no way to close it — Esc/
  // canvas-click did nothing). Reset whenever focus moves to a different
  // card (below) so switching focus always shows that card's history.
  const [sidebarDismissed, setSidebarDismissed] = useState(false);
  // Whether the agent is actively working, as opposed to waiting on you or
  // finished — a blind usability test found zero indication of this
  // anywhere ("no loading spinner... I only knew something happened
  // because I took a screenshot after waiting"). Driven by the server's
  // agent:busy/agent:idle broadcasts (PROTOCOL.md), not inferred from
  // transcript content.
  const [agentBusy, setAgentBusy] = useState(false);
  const keyCounter = useRef(0);
  const prevEntriesLengthRef = useRef(0);

  // Pending-message queue (item 3): every card's reply/submit used to call
  // `send` directly, so multiple cards submitted while the agent was still
  // busy on an earlier turn all landed in the backend's own internal queue
  // (main.ts's input-stream `pending` array) with zero visibility and no way
  // to change your mind. `enqueue` is what every reply box calls instead —
  // it stages the submission here; the dispatch effect below is the only
  // thing that actually calls `send`, one at a time, only once the agent is
  // idle. SidekickPanel renders `queue` so what's waiting (and its origin
  // card) is visible, with a cancel per still-queued entry.
  const [queue, setQueue] = useState([]); // [{id, text, label, preview}]
  const queueCounter = useRef(0);
  const dispatchLockRef = useRef(false);

  const enqueue = useCallback((node, rawText) => {
    const id = `queue:${queueCounter.current++}`;
    const text = node ? buildSubmission(node, rawText) : rawText;
    const label = node ? node.title : "General";
    setQueue((q) => [...q, { id, text, label, preview: rawText.trim() || rawText }]);
  }, []);

  const cancelQueued = useCallback((id) => {
    setQueue((q) => q.filter((item) => item.id !== id));
  }, []);

  // Dispatches the queue's front entry once the agent is actually idle —
  // `dispatchLockRef` covers the round-trip gap between calling `send` and
  // the server's `agent:busy` broadcast landing (agentBusy is still stale
  // `false` for that window), so a second entry can't slip out in the same
  // render pass. Cleared the moment `agentBusy` turns true, since the
  // `!agentBusy` guard below already prevents re-firing until it turns
  // false again on its own.
  useEffect(() => {
    if (agentBusy) {
      dispatchLockRef.current = false;
      return;
    }
    if (dispatchLockRef.current || queue.length === 0) return;
    dispatchLockRef.current = true;
    send({ type: "message:send", text: queue[0].text });
    setQueue((q) => q.slice(1));
  }, [queue, agentBusy, send]);

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
      setPartialAnswers({});
    });
    const offResolved = addListener("question:resolved", (msg) => {
      setPendingRaw((prev) => (prev?.requestId === msg.requestId ? null : prev));
    });
    const offBusy = addListener("agent:busy", () => setAgentBusy(true));
    const offIdle = addListener("agent:idle", () => setAgentBusy(false));
    return () => {
      offTree();
      offSnapshot();
      offEvent();
      offQuestion();
      offResolved();
      offBusy();
      offIdle();
    };
  }, [addListener]);

  const nodesById = useMemo(() => {
    const m = new Map();
    for (const n of tree?.nodes ?? []) m.set(n.id, n);
    return m;
  }, [tree]);

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
    // A multi-question AskUserQuestion call only sends `question:answer`
    // (and only then gets a server-pushed chain entry, PROTOCOL.md) once
    // EVERY question in the call has been individually answered — the SDK
    // resolves the whole tool call as one unit, there's no partial-resolve.
    // Until the rest of the batch catches up, a question you already
    // submitted would otherwise vanish from `liveQuestions` with nothing to
    // show for it (user: "回答之後，更要清楚顯示「做出了什麼決定」" — this
    // gap is exactly where that broke). Synthesize a local stand-in chain
    // entry per partial answer so what you picked is never invisible, even
    // mid-batch; superseded (briefly overlapping, not duplicated long-term)
    // once the real server echo lands and `partialAnswers` clears.
    if (pendingRaw) {
      for (const q of routeQuestions(pendingRaw.questions, nodesById)) {
        if (!(q.question in partialAnswers)) continue;
        const value = partialAnswers[q.question];
        const text = `${q.question} → ${Array.isArray(value) ? value.join(", ") : value}`;
        const targetNodeId = q.targetNodeId && buckets.has(q.targetNodeId) ? q.targetNodeId : ROOT_ID;
        buckets.get(targetNodeId).push({ _key: `partial:${pendingRaw.requestId}:${q.question}`, kind: "system", text });
      }
    }
    return buckets;
  }, [entries, nodesById, tree, pendingRaw, partialAnswers]);

  // Tracks which card most recently got new content — the fallback
  // AutoPan target when nothing is pending/manually focused. Guarded on
  // entries actually growing (not just nodesById changing) so this doesn't
  // re-fire on every unrelated tree:update. Targets the tail of the node's
  // reply chain, not the node itself, so a follow-up reply pans/focuses onto
  // the new chained card rather than back onto the (unchanged) origin card.
  useEffect(() => {
    if (entries.length > prevEntriesLengthRef.current) {
      const last = entries[entries.length - 1];
      if (isTaggable(last)) {
        const { targetNodeId } = routeTaggedText(last.text, nodesById);
        setLastEntryTarget(targetNodeId ? chainTailId(targetNodeId, threadsByTarget) : ROOT_ID);
      } else {
        setLastEntryTarget(ROOT_ID);
      }
    }
    prevEntriesLengthRef.current = entries.length;
  }, [entries, nodesById, threadsByTarget]);

  // Each question routed independently; still-unanswered ones each become
  // their own ephemeral card. `id` is stable across re-renders as long as
  // requestId/index don't change.
  const liveQuestions = useMemo(() => {
    if (!pendingRaw) return [];
    return routeQuestions(pendingRaw.questions, nodesById)
      .map((q, i) => ({ ...q, cardId: `q:${pendingRaw.requestId}:${i}` }))
      .filter((q) => !(q.question in partialAnswers));
  }, [pendingRaw, nodesById, partialAnswers]);

  // Only stages the answer — does NOT send `question:answer` itself even
  // once every question in the batch has one. That used to auto-fire the
  // instant the last pick landed, with no chance to review what the batch
  // as a whole was about to say; `batchSubmit` (below) renders one shared
  // review-and-confirm card once every question is staged, and only ITS
  // Submit button (`submitBatch`) actually sends (user: "問題組合...跳到
  // submit card（這張卡片是問題的共同 child，只有所有問題都回答的時候他才會
  // 出現）").
  function answerOne(question, requestId, value) {
    setPartialAnswers((prev) => ({ ...prev, [question]: value }));
  }

  // The shared child card, gated on every question in the batch having a
  // staged answer — `parents` is the deduped set of nodes the batch's
  // questions actually route to (usually just root, but a batch can span
  // more than one node's branch), so the card reads as "common child of the
  // questions" the way the user described rather than picking one arbitrary
  // parent. `routedQuestions` carries the tag-stripped display text so the
  // review card and `partialAnswers` share the same keys.
  const batchSubmit = useMemo(() => {
    if (!pendingRaw) return null;
    if (Object.keys(partialAnswers).length !== pendingRaw.questions.length) return null;
    const routedQuestions = routeQuestions(pendingRaw.questions, nodesById);
    const parents = [...new Set(routedQuestions.map((q) => (q.targetNodeId && nodesById.has(q.targetNodeId) ? q.targetNodeId : ROOT_ID)))];
    return { cardId: `submit:${pendingRaw.requestId}`, parents, routedQuestions };
  }, [pendingRaw, partialAnswers, nodesById]);

  // Moved out of answerOne above — this is now the only thing that actually
  // sends `question:answer`, triggered by the batch-submit card's own
  // button. Same key-matching logic as before it moved: routeQuestions
  // strips display tags, so the SDK's ORIGINAL question text is the key the
  // outgoing `answers` object needs, looked up via partialAnswers' stripped
  // key.
  function submitBatch() {
    if (!pendingRaw) return;
    const answers = {};
    for (const q of pendingRaw.questions) {
      answers[q.question] = partialAnswers[routeTaggedText(q.question, nodesById).text];
    }
    send({ type: "question:answer", requestId: pendingRaw.requestId, answers });
  }

  // A genuinely new question reclaims focus even if the user had manually
  // looked elsewhere — only a *new* requestId does this, not every render.
  useEffect(() => {
    if (pendingRaw) setManualFocusId(null);
  }, [pendingRaw?.requestId]); // eslint-disable-line react-hooks/exhaustive-deps

  // A multi-question AskUserQuestion batch only reaches `batchSubmit`'s
  // review card once every question has a staged answer (answerOne above)
  // — until then, each already-staged question just leaves its stand-in
  // system entry with nothing to indicate how many more are still needed
  // (blind usability test: answering one of four read as "did this even
  // work?" with no clue the other three were still blocking it).
  const batchProgress =
    pendingRaw && pendingRaw.questions.length > 1
      ? { answered: Object.keys(partialAnswers).length, total: pendingRaw.questions.length }
      : null;

  // "Please finalize now" (converge()'s pushMessage) explicitly asks Claude
  // to resolve or drop every open branch before flipping top-level status —
  // but a plain chat "wrap up" phrasing can also reach `complete` without
  // going through that instruction, and nothing here enforces it either way
  // (D4: Claude alone authors TREE.json). Surface the mismatch rather than
  // silently trusting `complete` to mean "nothing left open."
  const openNodesAfterComplete =
    tree?.status === "complete" ? (tree.nodes ?? []).filter((n) => n.status === "open").length : 0;

  const firstLiveQuestionId = liveQuestions[0]?.cardId ?? null;

  // Priority: explicit user focus > a live pending question > the batch's
  // review-and-confirm card once every question is staged > whatever's
  // newest. (user: "focus 應該 focus「還沒 resolve 的問題」而非 root" — but an
  // explicit click/Tab should still be able to look elsewhere on purpose.)
  const activeNodeId = manualFocusId ?? firstLiveQuestionId ?? batchSubmit?.cardId ?? lastEntryTarget;

  useEffect(() => {
    setSidebarDismissed(false);
  }, [activeNodeId]);

  // No manual dragging (v1): every card is always dagre-positioned, so
  // recomputing layout on every render is safe — nothing to "snap back
  // from." Positions only actually change when tree structure changes;
  // dagre is deterministic, so a data-only re-render reproduces the same
  // coordinates.
  const { nodes, edges } = useMemo(() => {
    const treeNodes = tree?.nodes ?? [];
    const ids = new Set(treeNodes.map((n) => n.id));
    // Each non-root node's thread entries chain downward, one ephemeral card
    // per entry, instead of folding into that node's own card (design.md
    // D12 revision: "所有回應都應該往下疊加... 像是討論從此往下"). Never
    // written to TREE.json — D4 still holds, Claude alone authors that file.
    const chainEntryById = new Map();
    const chainNodeDefs = [];
    const chainEdgeDefs = [];
    for (const n of treeNodes) {
      const thread = threadsByTarget.get(n.id) ?? [];
      let parent = n.id;
      thread.forEach((entry, i) => {
        const chainId = `${n.id}::reply:${i}`;
        // originNode (the real TREE.json node this chain hangs off) rides
        // along so the chain card's own reply box can route back to it —
        // a chain card has no TREE.json id of its own for Claude to tag
        // (user: "又不能往下問" — it was pure display, no way to continue).
        chainEntryById.set(chainId, { entry, originNode: n });
        chainNodeDefs.push({ id: chainId });
        chainEdgeDefs.push({ id: `${parent}->${chainId}`, source: parent, target: chainId });
        parent = chainId;
      });
    }
    const rfNodes = [
      { id: ROOT_ID },
      ...treeNodes.map((n) => ({ id: n.id })),
      ...liveQuestions.map((q) => ({ id: q.cardId })),
      ...chainNodeDefs,
      ...(batchSubmit ? [{ id: batchSubmit.cardId }] : []),
    ];
    const rfEdges = [
      ...treeNodes.map((n) => {
        const parent = n.parent && ids.has(n.parent) ? n.parent : ROOT_ID;
        return { id: `${parent}->${n.id}`, source: parent, target: n.id };
      }),
      ...liveQuestions.map((q) => {
        const parent = q.targetNodeId && ids.has(q.targetNodeId) ? q.targetNodeId : ROOT_ID;
        return { id: `${parent}->${q.cardId}`, source: parent, target: q.cardId };
      }),
      ...chainEdgeDefs,
      // One edge per node the batch's questions actually route to — the
      // "common child" the user described, not a single arbitrary parent.
      ...(batchSubmit
        ? batchSubmit.parents.map((p) => ({ id: `${p}->${batchSubmit.cardId}`, source: p, target: batchSubmit.cardId }))
        : []),
    ];
    const positioned = layoutTree(rfNodes, rfEdges);
    // Converging: collapse every card onto the root's position, each offset
    // a few px more than the last so it reads as a stacked deck rather than
    // cards vanishing into each other. `.react-flow__node`'s own CSS
    // transition (globals.css) animates the position change — no animation
    // library needed for this.
    const rootPos = positioned.find((n) => n.id === ROOT_ID)?.position ?? { x: 0, y: 0 };
    const finalPositioned = converging
      ? positioned.map((n, i) => ({
          ...n,
          position: { x: rootPos.x + i * 6, y: rootPos.y + i * 6 },
        }))
      : positioned;
    const withData = finalPositioned.map((n) => {
      const focused = n.id === activeNodeId;
      const onFocus = () => setManualFocusId(n.id);
      if (n.id === ROOT_ID) {
        return {
          ...n,
          type: "root",
          data: { thread: threadsByTarget.get(ROOT_ID) ?? [], focused, onFocus },
        };
      }
      if (batchSubmit && n.id === batchSubmit.cardId) {
        return {
          ...n,
          type: "question-batch-submit",
          data: { questions: batchSubmit.routedQuestions, answers: partialAnswers, onSubmit: submitBatch, focused, onFocus },
        };
      }
      const liveQuestion = liveQuestions.find((q) => q.cardId === n.id);
      if (liveQuestion) {
        return {
          ...n,
          type: "live-question",
          data: {
            question: liveQuestion,
            onAnswer: (value) => answerOne(liveQuestion.question, pendingRaw.requestId, value),
            focused,
            onFocus,
          },
        };
      }
      const chain = chainEntryById.get(n.id);
      if (chain) {
        return {
          ...n,
          type: "reply",
          data: { entry: chain.entry, originNode: chain.originNode, focused, onFocus, enqueue },
        };
      }
      const node = nodesById.get(n.id);
      // No `thread` here — follow-up replies are their own chained cards
      // now (chainEntryById above), not inline content on the origin card.
      return {
        ...n,
        type: node.type,
        data: { node, focused, onFocus, enqueue },
      };
    });
    return { nodes: withData, edges: rfEdges };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tree, nodesById, threadsByTarget, liveQuestions, activeNodeId, converging, enqueue, batchSubmit, partialAnswers, pendingRaw]);

  // "Needs action": a live question card, or a persisted `question`-type
  // node still open — the set n/p cycles through (user: "n p，是前往下一個、
  // 上一個還沒 resolve 的卡片"). hjkl/arrows instead do spatial navigation
  // across every card (see spatialNeighbor above).
  const actionableIds = useMemo(
    () =>
      nodes
        .filter(
          (n) =>
            n.type === "live-question" ||
            n.type === "question-batch-submit" ||
            (n.data.node?.type === "question" && n.data.node?.status === "open"),
        )
        .map((n) => n.id),
    [nodes],
  );

  useEffect(() => {
    function handleKeyDown(e) {
      const tag = document.activeElement?.tagName;
      const typing = tag === "INPUT" || tag === "TEXTAREA";
      // Esc always works, even while typing (user: "esc 要退出 / or :") — it's
      // the one universal "back out of wherever a shortcut put me" key.
      if (e.key === "Escape" && typing) {
        e.preventDefault();
        document.activeElement.blur();
        return;
      }
      if (typing) return;
      // hjkl/arrows: spatial navigation to the nearest card in that
      // direction (not Tab/Shift+Tab — user: "shift tab 沒用，可能被 browser
      // 攔截了", and React Flow's own Tab-cycling/arrow-drag are disabled
      // below via disableKeyboardA11y/nodesFocusable={false} so they don't
      // compete for the same keys).
      const DIRS = {
        h: [-1, 0], ArrowLeft: [-1, 0],
        l: [1, 0], ArrowRight: [1, 0],
        k: [0, -1], ArrowUp: [0, -1],
        j: [0, 1], ArrowDown: [0, 1],
      };
      if (e.key in DIRS) {
        e.preventDefault();
        const [dx, dy] = DIRS[e.key];
        const next = spatialNeighbor(nodes, manualFocusId ?? activeNodeId, dx, dy);
        if (next) setManualFocusId(next);
      } else if (e.key === "n" || e.key === "p") {
        if (actionableIds.length === 0) return;
        e.preventDefault();
        const idx = actionableIds.indexOf(manualFocusId ?? activeNodeId);
        const delta = e.key === "n" ? 1 : -1;
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
      } else if (e.key === "e") {
        e.preventDefault();
        document.querySelector(`[data-card-id="${activeNodeId}"] .node-notes`)?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [nodes, actionableIds, manualFocusId, activeNodeId]);

  const focusedData = nodes.find((n) => n.id === activeNodeId)?.data;

  function converge() {
    setConverging(true);
    setManualFocusId(ROOT_ID);
    // Matches globals.css's .react-flow__node transition duration — send
    // finalize once the collapse animation has visibly settled, not before.
    // `converging` MUST reset afterward: it's a one-shot lead-in animation,
    // not a mode — left true forever, every card (including whatever the
    // agent asks/resolves next) stays pinned to the same collapsed pile,
    // reads as the whole canvas being permanently stuck (user: "收斂按了變成
    // 這樣，然後按什麼都完全沒有效果").
    setTimeout(() => {
      send({ type: "session:finalize" });
      setConverging(false);
    }, 600);
  }

  return (
    <div className="canvas-view">
      <Navbar
        topic={tree?.topic}
        status={tree?.status}
        busy={agentBusy}
        batchProgress={batchProgress}
        openNodesAfterComplete={openNodesAfterComplete}
        onConverge={converge}
      />
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
            nodesFocusable={false}
            elementsSelectable={false}
            disableKeyboardA11y
          >
            <Background />
            <Controls showInteractive={false} />
          </ReactFlow>
          <AutoPan activeNodeId={activeNodeId} nodes={nodes} />
        </ReactFlowProvider>
        <SidekickPanel queue={queue} onCancel={cancelQueued} />
        <DetailSidebar
          key={activeNodeId}
          title={sidebarDismissed ? null : (focusedData?.node?.title ?? (activeNodeId === ROOT_ID ? "General" : null))}
          thread={focusedData?.thread ?? []}
          onClose={() => setSidebarDismissed(true)}
        />
      </div>
      <div className="shortcut-hints">
        <span><kbd>hjkl</kbd>/<kbd>←↑↓→</kbd> move</span>
        <span><kbd>n</kbd>/<kbd>p</kbd> next/prev unresolved</span>
        <span><kbd>1-4</kbd> answer</span>
        <span><kbd>/</kbd> reply</span>
        <span><kbd>e</kbd> notes</span>
        <span><kbd>:</kbd> chat</span>
        <span><kbd>Esc</kbd> back</span>
      </div>
      <ChatBar enqueue={enqueue} />
    </div>
  );
}

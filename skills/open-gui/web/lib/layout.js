import dagre from "@dagrejs/dagre";

// Cards are CSS min/max-height (auto), not a fixed pixel size (user-raised:
// "卡片的高度不能固定，這樣內容都看不清楚" — a hard-fixed height clipped real
// content). dagre still needs a concrete number per node to space the graph
// without overlap, so CARD_HEIGHT here is a spacing ESTIMATE, not a promise
// the rendered card matches it exactly — a card shorter than this leaves a
// little extra vertical gap; one taller grows into its CSS max-height with
// its own scroll (CardBody.js) rather than colliding with the row below.
export const CARD_WIDTH = 340;
export const CARD_HEIGHT = 260;

// Top-down (root at top) tree layout. `nodes` are plain {id} objects (React
// Flow node shape minus position); `edges` are {source, target}.
export function layoutTree(nodes, edges) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "TB", nodesep: 48, ranksep: 96 });
  g.setDefaultEdgeLabel(() => ({}));

  for (const node of nodes) {
    g.setNode(node.id, { width: CARD_WIDTH, height: CARD_HEIGHT });
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target);
  }

  dagre.layout(g);

  return nodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: { x: pos.x - CARD_WIDTH / 2, y: pos.y - CARD_HEIGHT / 2 },
    };
  });
}

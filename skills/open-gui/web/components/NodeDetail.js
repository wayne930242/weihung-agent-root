import DecisionNode from "./DecisionNode";
import QuestionNode from "./QuestionNode";
import ArtifactNode from "./ArtifactNode";
import InfoNode from "./InfoNode";
import NodeTypeIcon from "./NodeTypeIcon";
import StatusBadge from "./StatusBadge";

const RENDERERS = {
  decision: DecisionNode,
  question: QuestionNode,
  artifact: ArtifactNode,
  info: InfoNode,
};

// The full-detail view for whichever node is currently selected in the tree
// spine. All interaction affordances (reply boxes, option cards, doc/artifact
// preview buttons) live only here, never in the spine.
export default function NodeDetail({ node, isPending, markPending }) {
  if (!node) {
    return (
      <div className="detail-placeholder">
        <p className="dim">Select a node.</p>
      </div>
    );
  }

  const Renderer = RENDERERS[node.type];
  const onSubmit = () => markPending?.(node.id);

  return (
    <div className="detail-node">
      <div className="detail-node-header">
        <NodeTypeIcon type={node.type} className="node-type-icon-lg" />
        <span className={`node-type-tag node-type-${node.type}`}>
          {node.type}
        </span>
        <span className="node-title">{node.title}</span>
        {isPending && <StatusBadge status="pending" />}
      </div>
      {Renderer ? (
        // Keyed on node.id so switching the selected node mounts a fresh
        // instance instead of reusing one across nodes — otherwise
        // in-progress state in QuestionNode (notes/"Other" text) or
        // FreeTextBox would leak from the previously selected node onto the
        // newly selected one.
        <Renderer key={node.id} node={node} onSubmit={onSubmit} />
      ) : (
        <p className="node-unknown">Unknown node type: {node.type}</p>
      )}
    </div>
  );
}

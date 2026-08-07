import Markdown from "./Markdown";
import FreeTextBox from "./FreeTextBox";

export default function InfoNode({ node, onSubmit }) {
  return (
    <div className="node-body node-info">
      <Markdown text={node.text} />
      <FreeTextBox node={node} placeholder="Add a note…" onSubmit={onSubmit} />
    </div>
  );
}

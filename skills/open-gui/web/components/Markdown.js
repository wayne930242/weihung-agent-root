import { renderMarkdown } from "../lib/markdown";

export default function Markdown({ text }) {
  return (
    <div
      className="markdown"
      dangerouslySetInnerHTML={{ __html: renderMarkdown(text ?? "") }}
    />
  );
}

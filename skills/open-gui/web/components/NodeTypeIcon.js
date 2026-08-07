// One glyph per node `type`, shown beside the existing `[DECISION]`/etc. type
// badge in both the compact tree spine and the detail pane — not a redesign
// of the badge, just a small visual anchor next to it. Plain characters, no
// icon library/dependency.
//
// `ℹ` (U+2139) is in the emoji-presentation set and can render as a colored
// glyph on some platforms (notably Safari/macOS); appending the text
// presentation selector U+FE0E forces the plain monospace form, keeping it
// consistent with the other three glyphs and the op-sec no-color-per-type
// theme constraint.
const ICONS = {
  decision: "◆",
  question: "?",
  artifact: "▤",
  info: "ℹ︎", // "ℹ" + text-presentation selector, see note above
};

export default function NodeTypeIcon({ type, className = "" }) {
  return (
    <span className={`node-type-icon ${className}`.trim()} aria-hidden="true">
      {ICONS[type] ?? "•"}
    </span>
  );
}

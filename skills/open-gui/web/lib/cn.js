// Minimal className joiner — this project has no Tailwind (plain
// hand-written CSS, globals.css), so no tailwind-merge conflict resolution
// is needed, just safe joining of conditional classes instead of manual
// template-literal concatenation (easy to get spacing/falsy handling wrong).
export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

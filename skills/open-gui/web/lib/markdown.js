// Minimal markdown renderer: headings, bold, inline code, fenced code blocks,
// ordered/unordered lists, paragraphs. Escapes HTML first so file/text content
// can never inject markup.

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function inline(text) {
  return text
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

export function renderMarkdown(src) {
  if (!src) return "";
  const lines = escapeHtml(src).split("\n");
  let html = "";
  let inCode = false;
  let listType = null;

  function closeList() {
    if (listType) {
      html += `</${listType}>`;
      listType = null;
    }
  }

  for (const line of lines) {
    if (line.trim().startsWith("```")) {
      closeList();
      if (!inCode) {
        html += "<pre><code>";
        inCode = true;
      } else {
        html += "</code></pre>";
        inCode = false;
      }
      continue;
    }
    if (inCode) {
      html += line + "\n";
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      closeList();
      const level = headingMatch[1].length;
      html += `<h${level}>${inline(headingMatch[2])}</h${level}>`;
      continue;
    }

    const ulMatch = line.match(/^[-*]\s+(.*)$/);
    if (ulMatch) {
      if (listType !== "ul") {
        closeList();
        html += "<ul>";
        listType = "ul";
      }
      html += `<li>${inline(ulMatch[1])}</li>`;
      continue;
    }

    const olMatch = line.match(/^\d+\.\s+(.*)$/);
    if (olMatch) {
      if (listType !== "ol") {
        closeList();
        html += "<ol>";
        listType = "ol";
      }
      html += `<li>${inline(olMatch[1])}</li>`;
      continue;
    }

    closeList();
    if (line.trim() === "") continue;
    html += `<p>${inline(line)}</p>`;
  }
  closeList();
  if (inCode) html += "</code></pre>";
  return html;
}

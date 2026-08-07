import { assertEquals } from "jsr:@std/assert@1";
import { validateTree } from "./schema.ts";

Deno.test("valid empty tree", () => {
  const result = validateTree({ topic: "t", status: "in_progress", nodes: [] });
  assertEquals(result.valid, true);
});

Deno.test("valid decision node, open and resolved", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      { id: "a", type: "decision", parent: null, title: "A", recommendation: "do X", status: "open" },
      {
        id: "b",
        type: "decision",
        parent: "a",
        title: "B",
        recommendation: "do Y",
        status: "resolved",
        resolution: "did Y",
        doc: "docs/adr/0001.md",
      },
    ],
  });
  assertEquals(result.valid, true);
});

Deno.test("resolved decision without resolution is invalid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      { id: "a", type: "decision", parent: null, title: "A", recommendation: "do X", status: "resolved" },
    ],
  });
  assertEquals(result.valid, false);
  assertEquals(result.errors.some((e) => e.includes("resolution")), true);
});

Deno.test("open decision with a resolution is invalid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      {
        id: "a",
        type: "decision",
        parent: null,
        title: "A",
        recommendation: "do X",
        status: "open",
        resolution: "premature",
      },
    ],
  });
  assertEquals(result.valid, false);
});

Deno.test("question node resolved via selectedLabel", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      {
        id: "q1",
        type: "question",
        parent: null,
        title: "Q",
        prompt: "Ship v1?",
        options: [{ label: "Yes" }, { label: "No", description: "defer" }],
        status: "resolved",
        answer: { selectedLabel: "Yes" },
      },
    ],
  });
  assertEquals(result.valid, true);
});

Deno.test("question node resolved via customText (Other)", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      {
        id: "q1",
        type: "question",
        parent: null,
        title: "Q",
        prompt: "Ship v1?",
        options: [],
        status: "resolved",
        answer: { customText: "Maybe next quarter", notes: "budget pending" },
      },
    ],
  });
  assertEquals(result.valid, true);
});

Deno.test("resolved question without an answer is invalid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      {
        id: "q1",
        type: "question",
        parent: null,
        title: "Q",
        prompt: "Ship v1?",
        options: [],
        status: "resolved",
      },
    ],
  });
  assertEquals(result.valid, false);
});

Deno.test("artifact node defaults to file kind", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      { id: "a", type: "artifact", parent: null, title: "Diagram", path: "docs/diagram.svg" },
    ],
  });
  assertEquals(result.valid, true);
});

Deno.test("artifact node with url kind is valid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      {
        id: "a",
        type: "artifact",
        parent: null,
        title: "Design mockup",
        kind: "url",
        url: "https://claude.ai/public/artifacts/abc123",
      },
    ],
  });
  assertEquals(result.valid, true);
});

Deno.test("url-kind artifact node with a path instead of url is invalid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      { id: "a", type: "artifact", parent: null, title: "X", kind: "url", path: "docs/x.svg" },
    ],
  });
  assertEquals(result.valid, false);
});

Deno.test("file-kind artifact node with a url instead of path is invalid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      { id: "a", type: "artifact", parent: null, title: "X", kind: "file", url: "https://claude.ai/x" },
    ],
  });
  assertEquals(result.valid, false);
});

Deno.test("artifact node with unknown kind is invalid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      { id: "a", type: "artifact", parent: null, title: "X", kind: "bogus", path: "x" },
    ],
  });
  assertEquals(result.valid, false);
});

Deno.test("artifact node with status field is invalid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      { id: "a", type: "artifact", parent: null, title: "Diagram", path: "docs/diagram.svg", status: "open" },
    ],
  });
  assertEquals(result.valid, false);
});

Deno.test("info node valid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [{ id: "i1", type: "info", parent: null, title: "Context", text: "some markdown" }],
  });
  assertEquals(result.valid, true);
});

Deno.test("unknown node type is invalid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [{ id: "x", type: "bogus", parent: null, title: "X" }],
  });
  assertEquals(result.valid, false);
});

Deno.test("dangling parent reference is invalid", () => {
  const result = validateTree({
    topic: "t",
    status: "in_progress",
    nodes: [
      { id: "a", type: "info", parent: "does-not-exist", title: "A", text: "x" },
    ],
  });
  assertEquals(result.valid, false);
  assertEquals(result.errors.some((e) => e.includes("does-not-exist")), true);
});

Deno.test("top-level status must be in_progress|complete", () => {
  const result = validateTree({ topic: "t", status: "done", nodes: [] });
  assertEquals(result.valid, false);
});

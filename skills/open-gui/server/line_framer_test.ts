import { assertEquals } from "jsr:@std/assert@1";
import { LineFramer } from "./line_framer.ts";

Deno.test("single complete line in one chunk", () => {
  const framer = new LineFramer();
  const lines = framer.feed('{"type":"data","data":"hi"}\n');
  assertEquals(lines, ['{"type":"data","data":"hi"}']);
});

Deno.test("multiple messages in one chunk", () => {
  const framer = new LineFramer();
  const lines = framer.feed('{"a":1}\n{"b":2}\n{"c":3}\n');
  assertEquals(lines, ['{"a":1}', '{"b":2}', '{"c":3}']);
});

Deno.test("message split across multiple chunks", () => {
  const framer = new LineFramer();
  assertEquals(framer.feed('{"type":"da'), []);
  assertEquals(framer.feed('ta","data":"x"}\n'), ['{"type":"data","data":"x"}']);
});

Deno.test("embedded escaped newline in a JSON string value does not break framing", () => {
  const framer = new LineFramer();
  const payload = JSON.stringify({ type: "data", data: "line1\nline2\r\nline3" }) + "\n";
  const lines = framer.feed(payload);
  assertEquals(lines.length, 1);
  const parsed = JSON.parse(lines[0]);
  assertEquals(parsed.data, "line1\nline2\r\nline3");
});

Deno.test("empty lines are dropped", () => {
  const framer = new LineFramer();
  const lines = framer.feed('{"a":1}\n\n\n{"b":2}\n');
  assertEquals(lines, ['{"a":1}', '{"b":2}']);
});

Deno.test("partial trailing data retained across feeds", () => {
  const framer = new LineFramer();
  assertEquals(framer.feed('{"a":1}\n{"b":2'), ['{"a":1}']);
  assertEquals(framer.feed('}\n{"c":3}\n'), ['{"b":2}', '{"c":3}']);
});

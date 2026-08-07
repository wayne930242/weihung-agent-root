// Newline-delimited message framing, shared by the sidecar IPC reader and (for
// testing) exercised against the same shapes the WS layer parses. See PROTOCOL.md.

export class LineFramer {
  #buffer = "";

  // Feed a raw chunk, get back zero or more complete lines (empty lines dropped).
  // Incomplete trailing data is retained for the next feed().
  feed(chunk: string): string[] {
    this.#buffer += chunk;
    const lines: string[] = [];
    let idx: number;
    while ((idx = this.#buffer.indexOf("\n")) !== -1) {
      const line = this.#buffer.slice(0, idx);
      this.#buffer = this.#buffer.slice(idx + 1);
      if (line) lines.push(line);
    }
    return lines;
  }
}

// Spawns and supervises the Node.js sidecar, speaks PROTOCOL.md §1 IPC to it.

import { LineFramer } from "./line_framer.ts";

export type SidecarMessage =
  | { type: "spawned"; pid: number }
  | { type: "data"; data: string }
  | { type: "exit"; code: number | null; signal: string | null }
  | { type: "error"; message: string };

export interface SpawnRequest {
  file: string;
  args: string[];
  cwd: string;
  env: Record<string, string>;
  cols: number;
  rows: number;
}

export class SidecarClient {
  #process: Deno.ChildProcess;
  #conn: Deno.Conn | null = null;
  #writer: WritableStreamDefaultWriter<Uint8Array> | null = null;
  #onMessage: ((msg: SidecarMessage) => void) | null = null;

  private constructor(process: Deno.ChildProcess) {
    this.#process = process;
  }

  static async start(sidecarDir: string, env: Record<string, string>): Promise<SidecarClient> {
    const command = new Deno.Command("node", {
      args: ["index.js"],
      cwd: sidecarDir,
      env,
      stdout: "piped",
      stderr: "piped",
    });
    const process = command.spawn();
    const client = new SidecarClient(process);

    // Loud stderr forwarding — a sidecar crash must be visible, not swallowed.
    (async () => {
      for await (const chunk of process.stderr) {
        await Deno.stderr.write(chunk);
      }
    })();

    const port = await client.#waitForReady(process.stdout);
    await client.#connect(port);
    return client;
  }

  async #waitForReady(stdout: ReadableStream<Uint8Array>): Promise<number> {
    const reader = stdout.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) throw new Error("sidecar exited before printing READY");
        buffer += decoder.decode(value, { stream: true });
        const match = buffer.match(/READY (\d+)/);
        if (match) return Number(match[1]);
      }
    } finally {
      reader.releaseLock();
    }
  }

  async #connect(port: number): Promise<void> {
    let lastErr: unknown;
    for (let attempt = 0; attempt < 10; attempt++) {
      try {
        this.#conn = await Deno.connect({ transport: "tcp", hostname: "127.0.0.1", port });
        // Acquire the writer once and hold it for the connection's lifetime.
        // Getting a fresh writer per #send() call let concurrent sends (e.g.
        // fast keystrokes, each its own WS message) race for the lock —
        // Deno.Conn's writable stream throws "already locked" when a second
        // getWriter() runs before the first's releaseLock(), silently
        // dropping that write. A single long-lived writer removes the race.
        this.#writer = this.#conn.writable.getWriter();
        this.#readLoop();
        return;
      } catch (err) {
        lastErr = err;
        await new Promise((r) => setTimeout(r, 50));
      }
    }
    throw new Error(`could not connect to sidecar IPC socket: ${lastErr}`);
  }

  async #readLoop(): Promise<void> {
    if (!this.#conn) return;
    const decoder = new TextDecoder();
    const framer = new LineFramer();
    try {
      for await (const chunk of this.#conn.readable) {
        for (const line of framer.feed(decoder.decode(chunk, { stream: true }))) {
          const msg = JSON.parse(line) as SidecarMessage;
          this.#onMessage?.(msg);
        }
      }
    } catch (err) {
      this.#onMessage?.({ type: "error", message: `IPC read loop failed: ${err}` });
    }
  }

  onMessage(handler: (msg: SidecarMessage) => void): void {
    this.#onMessage = handler;
  }

  async #send(msg: unknown): Promise<void> {
    if (!this.#writer) throw new Error("sidecar not connected");
    await this.#writer.write(new TextEncoder().encode(JSON.stringify(msg) + "\n"));
  }

  spawn(req: SpawnRequest): Promise<void> {
    return this.#send({ type: "spawn", ...req });
  }

  write(data: string): Promise<void> {
    return this.#send({ type: "write", data });
  }

  resize(cols: number, rows: number): Promise<void> {
    return this.#send({ type: "resize", cols, rows });
  }

  kill(): void {
    try {
      this.#process.kill("SIGTERM");
    } catch {
      // already dead
    }
  }
}

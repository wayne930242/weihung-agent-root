"use strict";

// Owns node-pty exclusively (see PROTOCOL.md §1). Speaks newline-delimited JSON over a
// TCP loopback socket to the Deno backend (127.0.0.1, OS-assigned port) — not a Unix
// domain socket: Deno's `transport: "unix"` has no Windows support at all (confirmed
// against Deno's own docs), and a loopback TCP socket sidesteps that entirely, for free
// also avoiding macOS's ~104-byte sockaddr_un.sun_path limit that bit the original
// Unix-socket approach. Never decides *which* process to spawn — that's the `spawn`
// message's payload, sent by the Deno backend (PROTOCOL.md §3).

const net = require("net");
const pty = require("node-pty");

let term = null;
let client = null;

function send(message) {
  if (client && client.writable) {
    client.write(JSON.stringify(message) + "\n");
  }
}

function killTermAndExit() {
  if (term) {
    try {
      term.kill();
    } catch {
      // already dead
    }
    term = null;
  }
  process.exit(0);
}

function handleMessage(msg) {
  switch (msg.type) {
    case "spawn": {
      if (term) {
        send({ type: "error", message: "a process is already spawned on this sidecar" });
        return;
      }
      try {
        term = pty.spawn(msg.file, msg.args || [], {
          name: "xterm-color",
          cols: msg.cols || 80,
          rows: msg.rows || 24,
          cwd: msg.cwd,
          env: msg.env || process.env,
          encoding: "utf8",
        });
      } catch (err) {
        send({ type: "error", message: `spawn failed: ${err.message}` });
        return;
      }
      term.onData((data) => send({ type: "data", data }));
      term.onExit(({ exitCode, signal }) => {
        send({ type: "exit", code: exitCode, signal: signal ?? null });
        term = null;
      });
      send({ type: "spawned", pid: term.pid });
      return;
    }
    case "write": {
      if (!term) {
        send({ type: "error", message: "write received before spawn" });
        return;
      }
      term.write(msg.data);
      return;
    }
    case "resize": {
      if (!term) {
        send({ type: "error", message: "resize received before spawn" });
        return;
      }
      term.resize(msg.cols, msg.rows);
      return;
    }
    default:
      send({ type: "error", message: `unknown message type: ${msg.type}` });
  }
}

const server = net.createServer((socket) => {
  client = socket;
  let buffer = "";
  socket.on("data", (chunk) => {
    buffer += chunk.toString("utf8");
    let newlineIndex;
    while ((newlineIndex = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, newlineIndex);
      buffer = buffer.slice(newlineIndex + 1);
      if (!line) continue;
      try {
        handleMessage(JSON.parse(line));
      } catch (err) {
        send({ type: "error", message: `malformed message: ${err.message}` });
      }
    }
  });
  socket.on("close", killTermAndExit);
  socket.on("error", killTermAndExit);
});

server.listen(0, "127.0.0.1", () => {
  console.log(`READY ${server.address().port}`);
});

process.on("SIGTERM", killTermAndExit);
process.on("SIGINT", killTermAndExit);

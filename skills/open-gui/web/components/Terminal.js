"use client";

import { useEffect, useRef } from "react";
import "@xterm/xterm/css/xterm.css";
import { useSocket } from "./SocketProvider";

const XTERM_THEMES = {
  dark: {
    background: "#0a0c0b",
    foreground: "#d7ddd4",
    cursor: "#9dff5c",
    cursorAccent: "#0a0c0b",
    selectionBackground: "#242825",
    black: "#0a0c0b",
    brightBlack: "#5c655e",
    green: "#9dff5c",
    brightGreen: "#9dff5c",
  },
  light: {
    background: "#f4f6f2",
    foreground: "#1c211b",
    cursor: "#15803d",
    cursorAccent: "#f4f6f2",
    selectionBackground: "#dde3d8",
    black: "#1c211b",
    brightBlack: "#6e7a6a",
    green: "#15803d",
    brightGreen: "#15803d",
  },
};

export default function TerminalPanel() {
  const containerRef = useRef(null);
  const { send, addListener, theme } = useSocket();
  const themeRef = useRef(theme);
  themeRef.current = theme;
  const termRef = useRef(null);

  // Live-updates xterm's palette when the "config" message arrives (it can
  // land after the terminal has already mounted) or if the user's Claude
  // Code theme setting changes across a reconnect.
  useEffect(() => {
    if (termRef.current) termRef.current.options.theme = XTERM_THEMES[theme];
  }, [theme]);

  useEffect(() => {
    let term = null;
    let disposed = false;
    let resizeObserver = null;
    // pty:snapshot/pty:data can arrive before the dynamic xterm import
    // resolves; buffer and replay in order once the terminal exists instead
    // of dropping them.
    const buffered = [];

    const offSnapshot = addListener("pty:snapshot", (msg) => {
      if (term) {
        term.reset();
        term.write(msg.data);
      } else {
        buffered.push({ reset: true, data: msg.data });
      }
    });
    const offData = addListener("pty:data", (msg) => {
      if (term) {
        term.write(msg.data);
      } else {
        buffered.push({ reset: false, data: msg.data });
      }
    });

    (async () => {
      const { Terminal } = await import("@xterm/xterm");
      const { FitAddon } = await import("@xterm/addon-fit");
      if (disposed) return;

      const t = new Terminal({
        fontFamily:
          'ui-monospace, "SFMono-Regular", Menlo, Consolas, "Liberation Mono", monospace',
        fontSize: 13,
        cursorBlink: true,
        theme: XTERM_THEMES[themeRef.current],
      });
      const fitAddon = new FitAddon();
      t.loadAddon(fitAddon);
      t.open(containerRef.current);

      // Register onResize before the first fit() call: fit() can change
      // cols/rows immediately (container is already laid out by the time
      // this runs), firing a resize event synchronously. Registering the
      // listener after that first fit() call — as this used to — misses
      // that event: the PTY stays at its spawn-time size (80x24) until some
      // later, genuinely different fit() (e.g. the user dragging the split
      // divider) finally produces a new value to send.
      t.onData((data) => send({ type: "pty:write", data }));
      t.onResize(({ cols, rows }) => send({ type: "pty:resize", cols, rows }));

      fitAddon.fit();

      for (const item of buffered) {
        if (item.reset) t.reset();
        t.write(item.data);
      }
      buffered.length = 0;

      resizeObserver = new ResizeObserver(() => {
        try {
          fitAddon.fit();
        } catch {
          // container may be mid-teardown; ignore transient sizing errors
        }
      });
      resizeObserver.observe(containerRef.current);

      term = t;
      termRef.current = t;
    })();

    return () => {
      disposed = true;
      offSnapshot();
      offData();
      resizeObserver?.disconnect();
      term?.dispose();
      termRef.current = null;
    };
  }, [send, addListener]);

  return <div className="terminal-pane" ref={containerRef} />;
}

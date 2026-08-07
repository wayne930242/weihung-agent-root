"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

// One WebSocket connection per browser tab (PROTOCOL.md §2), multiplexing PTY
// I/O, tree push, and doc/artifact preview. This provider owns that single
// connection; every consumer (terminal, tree, preview) subscribes by message
// `type` instead of opening its own socket.

const SocketContext = createContext(null);

const RECONNECT_DELAY_MS = 2000;
const THEME_OVERRIDE_KEY = "open-gui-theme-override";

function readStoredThemeOverride() {
  if (typeof window === "undefined") return "auto";
  const stored = window.localStorage.getItem(THEME_OVERRIDE_KEY);
  return stored === "dark" || stored === "light" ? stored : "auto";
}

export function SocketProvider({ children }) {
  const wsRef = useRef(null);
  const listenersRef = useRef(new Map());
  const pendingRef = useRef([]);
  const [connected, setConnected] = useState(false);
  const [fatal, setFatal] = useState(null);
  const [sessionEnded, setSessionEnded] = useState(null);
  const stopReconnectRef = useRef(false);
  // Backend-reported theme (Claude Code's own settings.json, best-effort) vs.
  // a manual override the user can set if that detection didn't land right —
  // "auto" defers to the backend value; "dark"/"light" wins over it. Override
  // persists in localStorage (client-side only, never sent to the backend).
  const [backendTheme, setBackendTheme] = useState("dark");
  const [themeOverride, setThemeOverrideState] = useState(readStoredThemeOverride);
  const theme = themeOverride === "auto" ? backendTheme : themeOverride;

  const setThemeOverride = useCallback((value) => {
    setThemeOverrideState(value);
    if (value === "auto") window.localStorage.removeItem(THEME_OVERRIDE_KEY);
    else window.localStorage.setItem(THEME_OVERRIDE_KEY, value);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    let cancelled = false;
    let reconnectTimer = null;

    function connect() {
      if (cancelled) return;
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${proto}//${window.location.host}/ws`);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        const pending = pendingRef.current;
        pendingRef.current = [];
        for (const msg of pending) ws.send(JSON.stringify(msg));
      };
      ws.onmessage = (event) => {
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }
        if (msg.type === "fatal") setFatal(msg.message);
        if (msg.type === "config" && msg.theme) setBackendTheme(msg.theme);
        if (msg.type === "session:ended") {
          setSessionEnded({ code: msg.code, signal: msg.signal });
          // The backend shuts itself down right after this — no point
          // retrying a connection to a process that's intentionally gone.
          stopReconnectRef.current = true;
        }
        const set = listenersRef.current.get(msg.type);
        if (set) for (const fn of set) fn(msg);
      };
      ws.onclose = () => {
        setConnected(false);
        if (!cancelled && !stopReconnectRef.current) {
          reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
        }
      };
      ws.onerror = () => ws.close();
    }

    connect();
    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  const send = useCallback((msg) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    } else {
      pendingRef.current.push(msg);
    }
  }, []);

  const addListener = useCallback((type, fn) => {
    if (!listenersRef.current.has(type)) listenersRef.current.set(type, new Set());
    listenersRef.current.get(type).add(fn);
    return () => listenersRef.current.get(type)?.delete(fn);
  }, []);

  return (
    <SocketContext.Provider
      value={{
        send,
        addListener,
        connected,
        fatal,
        sessionEnded,
        theme,
        themeOverride,
        setThemeOverride,
      }}
    >
      {children}
    </SocketContext.Provider>
  );
}

export function useSocket() {
  const ctx = useContext(SocketContext);
  if (!ctx) throw new Error("useSocket must be used within SocketProvider");
  return ctx;
}

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { useSocket } from "./SocketProvider";

// Read-only preview panel state: a `decision` node's `doc` or an `artifact`
// node's `path`, fetched via preview:request/preview:response matched by
// requestId (PROTOCOL.md §2).

const PreviewContext = createContext(null);

export function PreviewProvider({ children }) {
  const { send, addListener } = useSocket();
  const [state, setState] = useState({
    open: false,
    path: null,
    loading: false,
    content: null,
    error: null,
  });
  const requestIdRef = useRef(null);

  useEffect(() => {
    return addListener("preview:response", (msg) => {
      if (msg.requestId !== requestIdRef.current) return;
      setState((s) => ({
        ...s,
        loading: false,
        content: msg.content ?? null,
        error: msg.error ?? null,
      }));
    });
  }, [addListener]);

  const openPreview = useCallback(
    (path) => {
      const requestId = crypto.randomUUID();
      requestIdRef.current = requestId;
      // `doc`/`path` may carry a trailing `#heading` fragment (e.g.
      // "CONTEXT.md#language") — that fragment isn't part of the filesystem
      // path, so only the part before it is sent to the server's
      // preview:request reader.
      const filePath = path.split("#")[0];
      setState({ open: true, path: filePath, loading: true, content: null, error: null });
      send({ type: "preview:request", requestId, path: filePath });
    },
    [send],
  );

  const closePreview = useCallback(() => {
    setState((s) => ({ ...s, open: false }));
  }, []);

  return (
    <PreviewContext.Provider value={{ ...state, openPreview, closePreview }}>
      {children}
    </PreviewContext.Provider>
  );
}

export function usePreview() {
  const ctx = useContext(PreviewContext);
  if (!ctx) throw new Error("usePreview must be used within PreviewProvider");
  return ctx;
}

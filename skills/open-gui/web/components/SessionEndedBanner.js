"use client";

import { useSocket } from "./SocketProvider";

// Distinct from FatalBanner: the wrapped `claude` process exiting isn't
// necessarily an error (e.g. the user ran /exit) — neutral wording, not red.
export default function SessionEndedBanner() {
  const { sessionEnded } = useSocket();
  if (!sessionEnded) return null;
  return (
    <div className="session-ended-banner" role="status">
      <strong>Session ended</strong> — the underlying claude process exited
      {sessionEnded.signal ? ` (signal ${sessionEnded.signal})` : ""}
      {sessionEnded.code != null ? ` (code ${sessionEnded.code})` : ""}. This
      backend is shutting down; reload will not reconnect.
    </div>
  );
}

"use client";

import { useSocket } from "./SocketProvider";
import ThemeToggle from "./ThemeToggle";

// Session-level controls, fixed chrome outside the pannable canvas (user:
// "定案 or stop or 收斂都應該放到 navbar") — these must stay reachable
// regardless of where the viewport has panned/zoomed to, unlike a card
// that's part of the graph itself.
export default function Navbar({ topic, status }) {
  const { send } = useSocket();

  function finalize() {
    send({ type: "session:finalize" });
  }

  function stop() {
    send({ type: "session:stop" });
  }

  return (
    <div className="navbar">
      <span className="navbar-topic">{topic || "open-gui"}</span>
      {status && <span className={`tree-status tree-status-${status}`}>{status}</span>}
      <div className="navbar-right">
        <ThemeToggle />
        <button className="finalize-btn" onClick={finalize} title="Ask Claude to wrap up now">
          定案
        </button>
        <button className="stop-btn" onClick={stop} title="Stop this session now">
          Stop
        </button>
      </div>
    </div>
  );
}

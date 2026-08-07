"use client";

import { useSocket } from "./SocketProvider";

const OPTIONS = ["auto", "dark", "light"];

// Manual override for the backend-detected theme (SocketProvider), in case
// Claude Code's own settings.json wasn't read correctly in this environment.
// Persists client-side in localStorage; "auto" defers back to the backend.
export default function ThemeToggle() {
  const { themeOverride, setThemeOverride } = useSocket();

  function cycle() {
    const next = OPTIONS[(OPTIONS.indexOf(themeOverride) + 1) % OPTIONS.length];
    setThemeOverride(next);
  }

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={cycle}
      title="Theme: auto follows Claude Code's own setting"
    >
      {themeOverride}
    </button>
  );
}

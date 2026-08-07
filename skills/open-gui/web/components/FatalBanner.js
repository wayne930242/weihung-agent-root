"use client";

import { useSocket } from "./SocketProvider";

export default function FatalBanner() {
  const { fatal } = useSocket();
  if (!fatal) return null;
  return (
    <div className="fatal-banner" role="alert">
      <strong>Session error:</strong> {fatal}
    </div>
  );
}

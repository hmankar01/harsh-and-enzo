import { useEffect, useRef } from "react";
import type { LogEntry } from "../types";
import { AgentChip } from "./Avatars";

export default function Ticker({ logs }: { logs: LogEntry[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [logs.length]);

  return (
    <div className="ticker" role="log" aria-live="polite">
      {logs.map((entry) => (
        <div key={entry.id} className={`ticker-line ticker-${entry.kind}`}>
          <AgentChip agent={entry.agent} />
          <span className="ticker-text">
            {entry.kind === "match" && <span className="mark mark-match">✓ </span>}
            {entry.kind === "reject" && <span className="mark mark-reject">✗ </span>}
            {entry.text}
          </span>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}

import { useEffect, useState } from "react";
import type { DonePayload, JobMatch, LogEntry, Stage } from "../types";
import ResultsPanel from "./ResultsPanel";
import StageBar from "./StageBar";
import Ticker from "./Ticker";

const QUIPS = [
  "Harsh insists the trench coat helps him scrape faster.",
  "Enzo alphabetizes his rejection stamps while he waits.",
  "Enzo's rubric has rules. The rules have rules.",
  "Harsh once found a job posting from the future. They don't talk about it.",
  "Good sourcing takes minutes. Great sourcing takes slightly more minutes.",
];

interface Props {
  stage: Stage;
  logs: LogEntry[];
  matches: JobMatch[];
  done: DonePayload | null;
  error: string | null;
  onReset: () => void;
}

export default function MissionControl({ stage, logs, matches, done, error, onReset }: Props) {
  const [elapsed, setElapsed] = useState(0);
  const [quip, setQuip] = useState(0);
  const [bump, setBump] = useState(false);
  const running = stage !== "done" && !error;

  useEffect(() => {
    if (matches.length === 0) return;
    setBump(true);
    const t = setTimeout(() => setBump(false), 500);
    return () => clearTimeout(t);
  }, [matches.length]);

  useEffect(() => {
    if (!running) return;
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    const quips = setInterval(() => setQuip((q) => (q + 1) % QUIPS.length), 9000);
    return () => {
      clearInterval(timer);
      clearInterval(quips);
    };
  }, [running]);

  const mm = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const ss = String(elapsed % 60).padStart(2, "0");

  return (
    <div className="mission">
      <div className="card mission-card">
        <div className="mission-head">
          <StageBar stage={stage} />
          <div className="mission-meta">
            <span className="meta-timer">{mm}:{ss}</span>
            <span className={`meta-count${bump ? " bump" : ""}`}>
              {matches.length} match{matches.length === 1 ? "" : "es"}
            </span>
          </div>
        </div>

        <Ticker logs={logs} />

        {running && <p className="quip">{QUIPS[quip]}</p>}

        {error && (
          <div className="mission-error">
            <p>⚠ {error}</p>
            <button className="ghost-btn" onClick={onReset}>Back to the brief</button>
          </div>
        )}

        {done && (
          <div className="mission-done">
            <p>
              {done.no_results
                ? "Mission complete — no postings survived Enzo's rubric this time. Loosen a filter and redeploy."
                : `Mission complete: ${done.matches.length} matches from ${done.evaluated} postings evaluated.`}
            </p>
            <button className="ghost-btn" onClick={onReset}>New brief</button>
          </div>
        )}
      </div>

      <ResultsPanel matches={matches} final={done !== null} />
    </div>
  );
}

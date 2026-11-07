import { useCallback, useEffect, useRef, useState } from "react";
import { openStream, RateLimitError, startSearch } from "./api";
import Hero from "./components/Hero";
import LimitScreen from "./components/LimitScreen";
import MissionControl from "./components/MissionControl";
import RecruiterForm from "./components/RecruiterForm";
import type {
  DonePayload,
  JobMatch,
  LogEntry,
  RateLimitInfo,
  SearchForm,
  Stage,
} from "./types";

type Phase = "form" | "running" | "limited";

export default function App() {
  const [phase, setPhase] = useState<Phase>("form");
  const [stage, setStage] = useState<Stage>("idle");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [done, setDone] = useState<DonePayload | null>(null);
  const [limitInfo, setLimitInfo] = useState<RateLimitInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const logId = useRef(0);
  const source = useRef<EventSource | null>(null);

  const addLog = useCallback((entry: Omit<LogEntry, "id">) => {
    logId.current += 1;
    const id = logId.current;
    setLogs((prev) => [...prev.slice(-120), { ...entry, id }]);
  }, []);

  // Keep the action in view when a mission starts or the limit screen appears.
  useEffect(() => {
    if (phase !== "form") {
      document.getElementById("brief")?.scrollIntoView({ behavior: "smooth" });
    }
  }, [phase]);

  // Close any open stream when the app unmounts.
  useEffect(() => {
    return () => source.current?.close();
  }, []);

  const launch = useCallback(
    async (form: SearchForm) => {
      setSubmitting(true);
      setError(null);
      try {
        const searchId = await startSearch(form);
        setPhase("running");
        setStage("searching");
        setLogs([]);
        setMatches([]);
        setDone(null);

        const es = openStream(searchId);
        source.current = es;

        es.addEventListener("stage", (e) => {
          setStage(JSON.parse((e as MessageEvent).data).stage as Stage);
        });
        es.addEventListener("log", (e) => {
          addLog(JSON.parse((e as MessageEvent).data));
        });
        es.addEventListener("match", (e) => {
          const job = JSON.parse((e as MessageEvent).data) as JobMatch;
          setMatches((prev) => [...prev, job]);
        });
        es.addEventListener("done", (e) => {
          const payload = JSON.parse((e as MessageEvent).data) as DonePayload;
          setMatches(payload.matches);
          setDone(payload);
          setStage("done");
          es.close();
        });
        es.addEventListener("error", (e) => {
          const data = (e as MessageEvent).data;
          if (data) {
            try {
              setError(JSON.parse(data).message ?? "Something went sideways.");
            } catch {
              setError("Something went sideways.");
            }
            es.close();
          }
          // Errors without data are transport-level; EventSource auto-reconnects
          // and the backend replays the event log from the top of the cursor.
        });
      } catch (err) {
        if (err instanceof RateLimitError) {
          setLimitInfo(err.info);
          setPhase("limited");
        } else {
          setError(err instanceof Error ? err.message : "Could not reach the agency.");
        }
      } finally {
        setSubmitting(false);
      }
    },
    [addLog]
  );

  const reset = useCallback(() => {
    source.current?.close();
    setPhase("form");
    setStage("idle");
    setLogs([]);
    setMatches([]);
    setDone(null);
    setLimitInfo(null);
    setError(null);
  }, []);

  return (
    <div className="shell">
      <div className="aurora" aria-hidden="true">
        <div className="aurora-a" />
        <div className="aurora-b" />
        <div className="aurora-grid" />
      </div>
      <Hero />
      <div id="brief" className="brief-anchor">
        {phase === "form" && (
          <RecruiterForm onSubmit={launch} submitting={submitting} error={error} />
        )}
        {phase === "running" && (
          <MissionControl
            stage={stage}
            logs={logs}
            matches={matches}
            done={done}
            error={error}
            onReset={reset}
          />
        )}
        {phase === "limited" && limitInfo && <LimitScreen info={limitInfo} onReset={reset} />}
      </div>
      <footer className="footer">
        Built with two imaginary employees and one very real scraping pipeline
      </footer>
    </div>
  );
}

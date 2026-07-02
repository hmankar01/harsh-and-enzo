import type { Stage } from "../types";

const STAGES: { key: Stage; label: string }[] = [
  { key: "searching", label: "Searching" },
  { key: "scraping", label: "Scraping" },
  { key: "evaluating", label: "Evaluating" },
  { key: "ranking", label: "Ranking" },
];

export default function StageBar({ stage }: { stage: Stage }) {
  const activeIndex =
    stage === "done" ? STAGES.length : STAGES.findIndex((s) => s.key === stage);

  return (
    <ol className="stagebar">
      {STAGES.map((s, i) => {
        const state = i < activeIndex ? "done" : i === activeIndex ? "active" : "todo";
        return (
          <li key={s.key} className={`stage stage-${state}`}>
            <span className="stage-dot">{state === "done" ? "✓" : i + 1}</span>
            <span className="stage-label">{s.label}</span>
            {i < STAGES.length - 1 && <span className="stage-line" />}
          </li>
        );
      })}
    </ol>
  );
}

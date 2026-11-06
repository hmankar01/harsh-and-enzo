import { useEffect, useRef, useState } from "react";
import type { LogEntry, Stage } from "../types";

/**
 * The live holo-feed: Harsh (amber line-art agent) scans while Enzo (teal
 * line-art beagle) sniffs each job folder. Every animation state is driven by
 * the real pipeline events — no fake loops.
 *
 * verdict states (reject/match) play for ~1.8s, then fall back to the
 * stage-derived base state.
 */

type SceneState = "search" | "fetch" | "sniff" | "reject" | "match" | "done" | "idle";

interface Props {
  stage: Stage;
  lastLog?: LogEntry;
  matchCount: number;
}

function baseState(stage: Stage): SceneState {
  if (stage === "searching" || stage === "scraping") return "search";
  if (stage === "evaluating" || stage === "ranking") return "idle";
  if (stage === "done") return "done";
  return "idle";
}

export default function MissionScene({ stage, lastLog, matchCount }: Props) {
  const [scene, setScene] = useState<SceneState>("search");
  const [jobIndex, setJobIndex] = useState(0);
  const revert = useRef<number | null>(null);

  useEffect(() => {
    if (stage === "done") setScene("done");
    else if (stage === "searching" || stage === "scraping") setScene("search");
  }, [stage]);

  useEffect(() => {
    if (!lastLog) return;
    const num = lastLog.text.match(/#(\d+)/);
    if (num) setJobIndex(parseInt(num[1], 10));

    if (revert.current) window.clearTimeout(revert.current);

    if (lastLog.kind === "reject") {
      setScene("reject");
      revert.current = window.setTimeout(() => setScene(baseState(stage)), 1800);
    } else if (lastLog.kind === "match") {
      setScene("match");
      revert.current = window.setTimeout(() => setScene(baseState(stage)), 1800);
    } else if (lastLog.agent === "harsh" && stage === "evaluating") {
      setScene("fetch");
    } else if (lastLog.agent === "enzo" && stage === "evaluating") {
      setScene("sniff");
    }
    return () => {
      if (revert.current) window.clearTimeout(revert.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastLog?.id]);

  const folderVisible = scene === "fetch" || scene === "sniff" || scene === "reject" || scene === "match";

  return (
    <div className={`scene scene-${scene}`} aria-hidden="true">
      <div className="scan-beam" />
      <div className="scene-label">
        <span className="rec-dot" /> FIELD CAM 01 · LIVE
      </div>
      <div className="scene-meta">
        JOB {String(jobIndex).padStart(2, "0")} · MATCHED {String(matchCount).padStart(2, "0")}
      </div>
      <span className="corner corner-tl" />
      <span className="corner corner-tr" />
      <span className="corner corner-bl" />
      <span className="corner corner-br" />

      <svg viewBox="0 0 720 250" className="scene-svg" preserveAspectRatio="xMidYMax meet">
        <defs>
          <linearGradient id="cone-grad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="var(--harsh)" stopOpacity="0.5" />
            <stop offset="1" stopColor="var(--harsh)" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="beam-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="var(--green)" stopOpacity="0" />
            <stop offset="1" stopColor="var(--green)" stopOpacity="0.4" />
          </linearGradient>
          <filter id="holo-glow" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="1.6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* perspective grid floor */}
        <g className="grid-floor" stroke="var(--enzo)" strokeWidth="1">
          <line x1="0" y1="200" x2="720" y2="200" opacity="0.22" />
          <line x1="0" y1="213" x2="720" y2="213" opacity="0.12" />
          <line x1="0" y1="229" x2="720" y2="229" opacity="0.08" />
          <line x1="0" y1="248" x2="720" y2="248" opacity="0.05" />
          {[0, 90, 180, 270, 360, 450, 540, 630, 720].map((x) => (
            <line key={x} x1={x} y1="250" x2={360 + (x - 360) * 0.72} y2="200" opacity="0.06" />
          ))}
        </g>

        {/* radar */}
        <g className="radar" transform="translate(74, 66)" filter="url(#holo-glow)">
          <circle r="30" fill="none" stroke="var(--enzo)" strokeWidth="1" opacity="0.4" />
          <circle r="19" fill="none" stroke="var(--enzo)" strokeWidth="1" opacity="0.25" />
          <circle r="8" fill="none" stroke="var(--enzo)" strokeWidth="1" opacity="0.2" />
          <line x1="-30" y1="0" x2="30" y2="0" stroke="var(--enzo)" strokeWidth="0.5" opacity="0.2" />
          <line x1="0" y1="-30" x2="0" y2="30" stroke="var(--enzo)" strokeWidth="0.5" opacity="0.2" />
          <line className="radar-sweep" x1="0" y1="0" x2="0" y2="-29" stroke="var(--enzo)" strokeWidth="1.5" />
          <circle className="blip blip-1" cx="14" cy="-10" r="2" fill="var(--enzo)" />
          <circle className="blip blip-2" cx="-9" cy="13" r="2" fill="var(--enzo)" />
          <circle className="blip blip-3" cx="-16" cy="-14" r="2" fill="var(--harsh)" />
        </g>

        {/* scan cone from Harsh's device */}
        <polygon
          className="scan-cone"
          points="204,152 388,118 388,196"
          fill="url(#cone-grad)"
        />

        {/* HARSH — amber line-art agent */}
        <g
          className="harsh"
          transform="translate(170, 200)"
          stroke="var(--harsh)"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
          filter="url(#holo-glow)"
        >
          {/* legs */}
          <path d="M-8,0 L-4,-28 M8,0 L4,-28" />
          {/* trench coat */}
          <path d="M-14,-28 L-10,-62 L10,-62 L14,-28 Z" />
          <path d="M-11,-45 L11,-45" opacity="0.7" />
          <path d="M0,-62 L-4,-51 M0,-62 L4,-51" opacity="0.7" />
          {/* scanning arm + device */}
          <g className="harsh-arm">
            <path d="M6,-57 L27,-49" />
            <rect x="25" y="-54" width="11" height="8" rx="1.5" />
            <circle cx="30.5" cy="-50" r="1.4" fill="var(--harsh)" stroke="none" className="device-led" />
          </g>
          {/* head + fedora */}
          <circle cx="0" cy="-71" r="7" />
          <path d="M-11,-76 L13,-76" />
          <path d="M-7,-76 c0,-7 3,-9.5 7,-9.5 s7,2.5 7,9.5" />
          <circle cx="2.5" cy="-71" r="0.9" fill="var(--harsh)" stroke="none" />
        </g>

        {/* drop zone — where folders materialize */}
        <g className="drop-zone" stroke="var(--text-dim)" strokeWidth="1.2" fill="none" opacity="0.22">
          <path d="M444,-4 h-10 v-10 M512,-4 h10 v-10 M444,-56 h-10 v10 M512,-56 h10 v10" transform="translate(0,204)" strokeDasharray="none" />
          <rect x="442" y="152" width="72" height="50" strokeDasharray="4 5" rx="2" />
        </g>

        {/* ENZO — teal line-art beagle */}
        <g
          className="enzo"
          transform="translate(395, 200)"
          stroke="var(--enzo)"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
          filter="url(#holo-glow)"
        >
          {/* tail — curls up from the rear */}
          <path className="enzo-tail" d="M-31,-30 c-6,-2 -9,-8 -8,-15" />
          {/* body — chest deep, back slightly arched */}
          <path d="M-28,-16 c-4,-10 0,-19 9,-21 l28,-3 c8,-1 13,4 13,11 c0,8 -6,13 -14,14 l-24,2 c-6,0.5 -10,-1 -12,-3 z" />
          {/* haunch */}
          <path d="M-28,-16 c-3,-8 0,-15 6,-18" opacity="0.65" />
          {/* legs */}
          <g className="enzo-legs-front">
            <path d="M12,-13 L13,0 M21,-14 L22,0" />
          </g>
          <g className="enzo-legs-back">
            <path d="M-24,-13 L-24,0 M-15,-13 L-15,0" />
          </g>
          {/* head group — rotates down to sniff */}
          <g className="enzo-head">
            <circle cx="27" cy="-46" r="9.5" />
            {/* snout + nose */}
            <path d="M35,-48 L46,-44 L35,-40" />
            <circle cx="46" cy="-44" r="2" fill="var(--enzo)" stroke="none" />
            <circle cx="30" cy="-49" r="1.2" fill="var(--enzo)" stroke="none" />
            {/* floppy ear hanging beside the head */}
            <path className="enzo-ear" d="M23,-54 c-8,0 -11,9 -8,17 c4,-1.5 7,-5 8,-9" />
            {/* sniff ripples */}
            <g className="sniff-waves" strokeWidth="1.4">
              <path className="sniff-w1" d="M52,-48 a7,7 0 0 1 0,9" />
              <path className="sniff-w2" d="M57,-51 a11,11 0 0 1 0,15" />
              <path className="sniff-w3" d="M62,-54 a15,15 0 0 1 0,21" />
            </g>
          </g>
          {/* collar */}
          <path d="M17,-42 L23,-35" stroke="var(--harsh)" strokeWidth="2.6" />
        </g>

        {/* match beam */}
        <rect className="match-beam" x="440" y="30" width="76" height="170" fill="url(#beam-grad)" />

        {/* FOLDER — the job under the nose */}
        {folderVisible && (
          <g className="folder" transform="translate(478, 200)" filter="url(#holo-glow)">
            <g className="folder-body" stroke="var(--text-dim)" strokeWidth="1.8" fill="rgba(10,15,28,0.85)">
              <path d="M-28,-46 h16 l6,7 h34 v35 h-56 z" strokeLinejoin="round" />
              <text
                x="0"
                y="-18"
                textAnchor="middle"
                fill="var(--text-dim)"
                stroke="none"
                fontSize="10"
                fontFamily="JetBrains Mono, monospace"
                letterSpacing="1"
              >
                JOB #{jobIndex || "?"}
              </text>
            </g>
            {/* reject stamp */}
            <g className="stamp" stroke="var(--red)" strokeWidth="2.6" fill="none">
              <circle cx="0" cy="-26" r="15" />
              <path d="M-8,-34 L8,-18 M8,-34 L-8,-18" />
            </g>
          </g>
        )}

        {/* done state */}
        <g className="mission-complete" filter="url(#holo-glow)">
          <rect
            x="245"
            y="76"
            width="230"
            height="40"
            fill="none"
            stroke="var(--green)"
            strokeWidth="2"
            rx="3"
          />
          <text
            x="360"
            y="102"
            textAnchor="middle"
            fill="var(--green)"
            fontSize="17"
            fontFamily="JetBrains Mono, monospace"
            letterSpacing="4"
            fontWeight="600"
          >
            MISSION COMPLETE
          </text>
        </g>
      </svg>
    </div>
  );
}

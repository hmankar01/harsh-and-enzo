import { EnzoAvatar, HarshAvatar } from "./Avatars";

const MARQUEE =
  "SWEEPING LINKEDIN ◆ 24H WINDOW ◆ RUBRIC LOADED ◆ ENZO IS SNIFFING ◆ MATCH FOUND ◆ RANKED BY FRESHNESS ◆ NO FLUFF, ONLY SHORTLIST ◆ ";

export default function Hero() {
  return (
    <section>
      <div className="hero-status">
        <span className="hero-status-live">
          <span className="rec-dot" />
          AGENCY ONLINE
        </span>
        <span className="hero-status-unit">EST. 2026 · FIELD UNIT 01</span>
      </div>

      <div className="hero-body">
        <div className="hero-duo">
          <HarshAvatar size={92} />
          <EnzoAvatar size={92} />
        </div>

        <h1 className="hero-title">HARSH &amp; ENZO</h1>
        <p className="hero-sub">Talent&nbsp;Reconnaissance</p>
        <p className="hero-blurb">
          One agent. One very good boy. They sweep LinkedIn, grade every posting against
          your brief, and hand you a ranked shortlist — narrated live from the field.
        </p>

        <a className="hero-cta" href="#brief">
          Deploy the agents ↓
        </a>

        <div className="hero-pills">
          <span>25 POSTINGS / SWEEP</span>
          <span>LLM-GRADED RUBRIC</span>
          <span>RANKED BY FRESHNESS</span>
        </div>
      </div>

      <div className="marquee">
        <div className="marquee-track">
          <span>{MARQUEE}</span>
          <span aria-hidden="true">{MARQUEE}</span>
        </div>
      </div>
    </section>
  );
}

import { useState } from "react";
import type { SearchForm } from "../types";

const SKILL_OPTIONS = [
  "LLM",
  "RAG",
  "LangChain",
  "AI Agents",
  "Prompt Engineering",
  "Python",
  "Machine Learning",
  "NLP",
  "MLOps",
  "Computer Vision",
];

const DOMAIN_OPTIONS = [
  "CRM Automation",
  "AdTech / PPC",
  "FinTech / Accounting",
  "General Ops",
];

const SENIORITY_OPTIONS = ["Senior", "Staff", "Principal", "Lead"];

const YEARS = Array.from({ length: 11 }, (_, i) => i);

interface Props {
  onSubmit: (form: SearchForm) => void;
  submitting: boolean;
  error: string | null;
}

export default function RecruiterForm({ onSubmit, submitting, error }: Props) {
  const [expMin, setExpMin] = useState(0);
  const [expMax, setExpMax] = useState(2);
  const [seniority, setSeniority] = useState<string[]>([...SENIORITY_OPTIONS]);
  const [skills, setSkills] = useState<string[]>(["LLM", "AI Agents", "RAG"]);
  const [customSkill, setCustomSkill] = useState("");
  const [domains, setDomains] = useState<string[]>([]);
  const [customDomain, setCustomDomain] = useState("");
  const [sponsorship, setSponsorship] = useState(false);
  const [locMode, setLocMode] = useState<"remote" | "city" | "hybrid">("remote");
  const [city, setCity] = useState("");
  const [radius, setRadius] = useState(25);
  const [exclusions, setExclusions] = useState("");
  const [salaryFloor, setSalaryFloor] = useState("");

  const toggle = (list: string[], set: (v: string[]) => void, value: string) => {
    set(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  };

  const addCustomSkill = () => {
    const value = customSkill.trim();
    if (value && !skills.includes(value)) setSkills([...skills, value]);
    setCustomSkill("");
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      experience_min: expMin,
      experience_max: expMax,
      exclude_seniority: seniority,
      skills,
      domains,
      custom_domain: customDomain.trim() || undefined,
      requires_sponsorship: sponsorship,
      location: {
        mode: locMode,
        city: locMode === "remote" ? undefined : city.trim() || undefined,
        radius_miles: locMode === "hybrid" ? radius : undefined,
      },
      exclusion_keywords: exclusions.trim(),
      salary_floor: salaryFloor ? Number(salaryFloor) : undefined,
    });
  };

  return (
    <form className="card form-card" onSubmit={submit}>
      <span className="corner corner-tl" aria-hidden="true" />
      <span className="corner corner-tr" aria-hidden="true" />
      <span className="corner corner-bl" aria-hidden="true" />
      <span className="corner corner-br" aria-hidden="true" />

      <div className="form-head">
        <h2>Mission brief</h2>
        <span className="form-head-tag">FORM 07-A · CLASSIFIED</span>
      </div>
      <p className="form-intro">Describe the role. Harsh sweeps, Enzo grades, matches surface live.</p>

      <div className="form-grid">
        <fieldset className="field">
          <legend>Experience range</legend>
          <div className="row">
            <select value={expMin} onChange={(e) => setExpMin(Number(e.target.value))}>
              {YEARS.map((y) => (
                <option key={y} value={y}>
                  {y} yrs
                </option>
              ))}
            </select>
            <span className="range-dash">to</span>
            <select value={expMax} onChange={(e) => setExpMax(Number(e.target.value))}>
              {YEARS.filter((y) => y >= expMin).map((y) => (
                <option key={y} value={y}>
                  {y} yrs
                </option>
              ))}
            </select>
          </div>
        </fieldset>

        <fieldset className="field">
          <legend>Exclude seniority</legend>
          <div className="chip-row">
            {SENIORITY_OPTIONS.map((s) => (
              <label key={s} className={`chip ${seniority.includes(s) ? "chip-on chip-red" : ""}`}>
                <input
                  type="checkbox"
                  checked={seniority.includes(s)}
                  onChange={() => toggle(seniority, setSeniority, s)}
                />
                {s}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset className="field field-wide">
          <legend>Skills</legend>
          <div className="chip-row">
            {SKILL_OPTIONS.concat(skills.filter((s) => !SKILL_OPTIONS.includes(s))).map((s) => (
              <label key={s} className={`chip ${skills.includes(s) ? "chip-on" : ""}`}>
                <input
                  type="checkbox"
                  checked={skills.includes(s)}
                  onChange={() => toggle(skills, setSkills, s)}
                />
                {s}
              </label>
            ))}
            <span className="chip chip-input">
              <input
                type="text"
                placeholder="add skill…"
                value={customSkill}
                onChange={(e) => setCustomSkill(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addCustomSkill();
                  }
                }}
                onBlur={addCustomSkill}
              />
            </span>
          </div>
        </fieldset>

        <fieldset className="field field-wide">
          <legend>Domains</legend>
          <div className="chip-row">
            {DOMAIN_OPTIONS.map((d) => (
              <label key={d} className={`chip ${domains.includes(d) ? "chip-on" : ""}`}>
                <input
                  type="checkbox"
                  checked={domains.includes(d)}
                  onChange={() => toggle(domains, setDomains, d)}
                />
                {d}
              </label>
            ))}
            <span className="chip chip-input">
              <input
                type="text"
                placeholder="custom domain…"
                value={customDomain}
                onChange={(e) => setCustomDomain(e.target.value)}
              />
            </span>
          </div>
        </fieldset>

        <fieldset className="field">
          <legend>Visa sponsorship</legend>
          <label className="toggle">
            <input
              type="checkbox"
              checked={sponsorship}
              onChange={(e) => setSponsorship(e.target.checked)}
            />
            <span className="toggle-track" />
            <span className="toggle-label">
              {sponsorship ? "Required — reject non-sponsors" : "Not required"}
            </span>
          </label>
        </fieldset>

        <fieldset className="field">
          <legend>Salary floor (optional)</legend>
          <input
            type="number"
            min={0}
            step={5000}
            placeholder="e.g. 90000"
            value={salaryFloor}
            onChange={(e) => setSalaryFloor(e.target.value)}
          />
        </fieldset>

        <fieldset className="field field-wide">
          <legend>Location</legend>
          <div className="row row-wrap">
            {(["remote", "city", "hybrid"] as const).map((mode) => (
              <label key={mode} className={`chip ${locMode === mode ? "chip-on" : ""}`}>
                <input
                  type="radio"
                  name="locmode"
                  checked={locMode === mode}
                  onChange={() => setLocMode(mode)}
                />
                {mode === "remote" ? "Remote only" : mode === "city" ? "City" : "Hybrid + radius"}
              </label>
            ))}
            {locMode !== "remote" && (
              <input
                type="text"
                placeholder="City, Country"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                required
              />
            )}
            {locMode === "hybrid" && (
              <select value={radius} onChange={(e) => setRadius(Number(e.target.value))}>
                {[10, 25, 50, 75, 100].map((r) => (
                  <option key={r} value={r}>
                    within {r} mi
                  </option>
                ))}
              </select>
            )}
          </div>
        </fieldset>

        <fieldset className="field field-wide">
          <legend>Exclusion keywords</legend>
          <input
            type="text"
            placeholder="e.g. clearance required, contract-to-hire, on-call"
            value={exclusions}
            onChange={(e) => setExclusions(e.target.value)}
          />
        </fieldset>
      </div>

      {error && <p className="form-error">⚠ {error}</p>}

      <button className="launch-btn" type="submit" disabled={submitting}>
        {submitting ? "Briefing the agents…" : "Deploy Harsh & Enzo →"}
      </button>
      <p className="form-fineprint">DEMO BUILD · 2 MISSIONS PER VISITOR · AGENTS NARRATE LIVE</p>
    </form>
  );
}

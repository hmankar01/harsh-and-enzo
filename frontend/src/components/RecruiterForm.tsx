import { useEffect, useState } from "react";
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

const STORAGE_KEY = "henz:last-brief-v2";

const DEFAULT_FORM: SearchForm = {
  experience_min: 0,
  experience_max: 2,
  exclude_seniority: [...SENIORITY_OPTIONS],
  skills: ["LLM", "AI Agents", "RAG"],
  domains: [],
  requires_sponsorship: false,
  location: { remote: true, hybrid: false, onsite: false, cities: [], radius_miles: 25 },
  exclusion_keywords: "",
  salary_floor: undefined,
};

// Builder / Forward-Deployed-Engineer brief: applied AI + internal tools +
// automation, sponsorship required, no ML-research roles.
const BUILDER_PRESET: SearchForm = {
  experience_min: 0,
  experience_max: 2,
  exclude_seniority: [...SENIORITY_OPTIONS],
  skills: ["Python", "SQL", "AI Agents", "LLM", "Data Pipelines", "Automation"],
  domains: ["General Ops"],
  requires_sponsorship: true,
  location: { remote: true, hybrid: false, onsite: false, cities: [], radius_miles: 25 },
  exclusion_keywords:
    "model training, deep learning, research scientist, machine learning engineer, quant, PhD, fine-tuning",
  salary_floor: undefined,
};

function loadSaved(): SearchForm {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_FORM;
    const parsed = JSON.parse(raw) as Partial<SearchForm>;
    const result: SearchForm = {
      ...DEFAULT_FORM,
      ...parsed,
      location: {
        remote: false,
        hybrid: false,
        onsite: false,
        cities: [],
        ...(parsed.location ?? {}),
      },
    };
    // Clamp an impossible range (e.g. min > max) so the selects stay valid.
    if (result.experience_max < result.experience_min) {
      result.experience_max = result.experience_min;
    }
    return result;
  } catch {
    return DEFAULT_FORM;
  }
}

interface Props {
  onSubmit: (form: SearchForm) => void;
  submitting: boolean;
  error: string | null;
}

export default function RecruiterForm({ onSubmit, submitting, error }: Props) {
  const [form, setForm] = useState<SearchForm>(loadSaved);
  const [customSkill, setCustomSkill] = useState("");
  const [cityInput, setCityInput] = useState("");

  // Persist the brief so going back / reloading doesn't wipe it.
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(form));
    } catch {
      /* storage unavailable — ignore */
    }
  }, [form]);

  const set = <K extends keyof SearchForm>(key: K, value: SearchForm[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const toggle = (key: "exclude_seniority" | "skills" | "domains", value: string) => {
    setForm((prev) => {
      const list = prev[key] as string[];
      const next = list.includes(value)
        ? list.filter((v) => v !== value)
        : [...list, value];
      return { ...prev, [key]: next };
    });
  };

  const addCustomSkill = () => {
    const value = customSkill.trim();
    if (value && !form.skills.includes(value)) set("skills", [...form.skills, value]);
    setCustomSkill("");
  };

  const addCity = () => {
    const value = cityInput.trim();
    if (value && !form.location.cities.includes(value)) {
      set("location", { ...form.location, cities: [...form.location.cities, value] });
    }
    setCityInput("");
  };

  const removeCity = (city: string) => {
    set("location", {
      ...form.location,
      cities: form.location.cities.filter((c) => c !== city),
    });
  };

  const setWorkplace = (key: "remote" | "hybrid" | "onsite") => {
    set("location", { ...form.location, [key]: !form.location[key] });
  };

  return (
    <form className="card form-card" onSubmit={(e) => { e.preventDefault(); onSubmit(form); }}>
      <span className="corner corner-tl" aria-hidden="true" />
      <span className="corner corner-tr" aria-hidden="true" />
      <span className="corner corner-bl" aria-hidden="true" />
      <span className="corner corner-br" aria-hidden="true" />

      <div className="form-head">
        <h2>Mission brief</h2>
        <span className="form-head-tag">FORM 07-A · CLASSIFIED</span>
      </div>
      <p className="form-intro">Describe the role. Harsh sweeps, Enzo grades, matches surface live.</p>

      <button
        type="button"
        className="preset-btn"
        onClick={() => setForm(BUILDER_PRESET)}
        title="Applied AI / builder roles that sponsor visas"
      >
        ⚡ Builder / FDE brief
      </button>

      <div className="form-grid">
        <fieldset className="field">
          <legend>Experience range</legend>
          <div className="row">
            <select
              value={form.experience_min}
              onChange={(e) => {
                const min = Number(e.target.value);
                setForm((prev) => ({ ...prev, experience_min: min, experience_max: Math.max(prev.experience_max, min) }));
              }}
            >
              {YEARS.map((y) => (
                <option key={y} value={y}>
                  {y} yrs
                </option>
              ))}
            </select>
            <span className="range-dash">to</span>
            <select
              value={form.experience_max}
              onChange={(e) => set("experience_max", Number(e.target.value))}
            >
              {YEARS.filter((y) => y >= form.experience_min).map((y) => (
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
              <label key={s} className={`chip ${form.exclude_seniority.includes(s) ? "chip-on chip-red" : ""}`}>
                <input
                  type="checkbox"
                  checked={form.exclude_seniority.includes(s)}
                  onChange={() => toggle("exclude_seniority", s)}
                />
                {s}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset className="field field-wide">
          <legend>Skills</legend>
          <div className="chip-row">
            {SKILL_OPTIONS.concat(form.skills.filter((s) => !SKILL_OPTIONS.includes(s))).map((s) => (
              <label key={s} className={`chip ${form.skills.includes(s) ? "chip-on" : ""}`}>
                <input
                  type="checkbox"
                  checked={form.skills.includes(s)}
                  onChange={() => toggle("skills", s)}
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
              <label key={d} className={`chip ${form.domains.includes(d) ? "chip-on" : ""}`}>
                <input
                  type="checkbox"
                  checked={form.domains.includes(d)}
                  onChange={() => toggle("domains", d)}
                />
                {d}
              </label>
            ))}
            <span className="chip chip-input">
              <input
                type="text"
                placeholder="custom domain…"
                value={form.custom_domain ?? ""}
                onChange={(e) => set("custom_domain", e.target.value || undefined)}
              />
            </span>
          </div>
        </fieldset>

        <fieldset className="field">
          <legend>Visa sponsorship</legend>
          <label className="toggle">
            <input
              type="checkbox"
              checked={form.requires_sponsorship}
              onChange={(e) => set("requires_sponsorship", e.target.checked)}
            />
            <span className="toggle-track" />
            <span className="toggle-label">
              {form.requires_sponsorship ? "Required — reject non-sponsors" : "Not required"}
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
            value={form.salary_floor ?? ""}
            onChange={(e) => set("salary_floor", e.target.value ? Number(e.target.value) : undefined)}
          />
        </fieldset>

        <fieldset className="field field-wide">
          <legend>Workplace type</legend>
          <div className="chip-row">
            {(["remote", "hybrid", "onsite"] as const).map((w) => (
              <label key={w} className={`chip ${form.location[w] ? "chip-on" : ""}`}>
                <input
                  type="checkbox"
                  checked={form.location[w]}
                  onChange={() => setWorkplace(w)}
                />
                {w === "remote" ? "Remote" : w === "hybrid" ? "Hybrid" : "Onsite"}
              </label>
            ))}
          </div>
          {form.location.hybrid && (
            <div className="row" style={{ marginTop: 8 }}>
              <select
                value={form.location.radius_miles ?? 25}
                onChange={(e) =>
                  set("location", { ...form.location, radius_miles: Number(e.target.value) })
                }
              >
                {[10, 25, 50, 75, 100].map((r) => (
                  <option key={r} value={r}>
                    within {r} mi
                  </option>
                ))}
              </select>
            </div>
          )}
        </fieldset>

        <fieldset className="field field-wide">
          <legend>Locations (cities / states)</legend>
          <div className="chip-row">
            {form.location.cities.map((c) => (
              <span key={c} className="chip chip-on">
                {c}
                <button
                  type="button"
                  className="chip-x"
                  aria-label={`Remove ${c}`}
                  onClick={() => removeCity(c)}
                >
                  ×
                </button>
              </span>
            ))}
            <span className="chip chip-input">
              <input
                type="text"
                placeholder="add city or state…"
                value={cityInput}
                onChange={(e) => setCityInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addCity();
                  }
                }}
                onBlur={addCity}
              />
            </span>
          </div>
        </fieldset>

        <fieldset className="field field-wide">
          <legend>Exclusion keywords</legend>
          <input
            type="text"
            placeholder="e.g. clearance required, contract-to-hire, on-call"
            value={form.exclusion_keywords}
            onChange={(e) => set("exclusion_keywords", e.target.value)}
          />
        </fieldset>
      </div>

      {error && <p className="form-error">⚠ {error}</p>}

      <button className="launch-btn" type="submit" disabled={submitting}>
        {submitting ? "Briefing the agents…" : "Deploy Harsh & Enzo →"}
      </button>
      <p className="form-fineprint">DEMO BUILD · 7 MISSIONS PER VISITOR · AGENTS NARRATE LIVE</p>
    </form>
  );
}

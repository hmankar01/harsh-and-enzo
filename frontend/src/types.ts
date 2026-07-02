export type Stage = "idle" | "searching" | "scraping" | "evaluating" | "ranking" | "done";

export type Agent = "harsh" | "enzo" | "system";

export interface LogEntry {
  id: number;
  agent: Agent;
  text: string;
  kind: "info" | "reject" | "match";
}

export interface JobMatch {
  rank?: number;
  title: string;
  company: string;
  salary_range: string;
  experience_required: string;
  posted_date: string;
  url: string;
  reason: string;
}

export interface LocationSpec {
  mode: "remote" | "city" | "hybrid";
  city?: string;
  radius_miles?: number;
}

export interface SearchForm {
  experience_min: number;
  experience_max: number;
  exclude_seniority: string[];
  skills: string[];
  domains: string[];
  custom_domain?: string;
  requires_sponsorship: boolean;
  location: LocationSpec;
  exclusion_keywords: string;
  salary_floor?: number;
}

export interface RateLimitInfo {
  message: string;
  contact_linkedin: string;
  contact_email: string;
}

export interface DonePayload {
  matches: JobMatch[];
  evaluated: number;
  no_results: boolean;
}

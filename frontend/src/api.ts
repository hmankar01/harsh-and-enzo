import type { RateLimitInfo, SearchForm } from "./types";

export const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class RateLimitError extends Error {
  info: RateLimitInfo;
  constructor(info: RateLimitInfo) {
    super(info.message);
    this.info = info;
  }
}

export async function startSearch(form: SearchForm): Promise<string> {
  const response = await fetch(`${API_BASE}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(form),
  });
  if (response.status === 429) {
    throw new RateLimitError(await response.json());
  }
  if (!response.ok) {
    throw new Error(`Search failed to start (${response.status})`);
  }
  const data = await response.json();
  return data.search_id as string;
}

export function openStream(searchId: string): EventSource {
  return new EventSource(`${API_BASE}/api/search/${searchId}/stream`);
}

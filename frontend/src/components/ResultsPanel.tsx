import type { JobMatch } from "../types";

export default function ResultsPanel({ matches, final }: { matches: JobMatch[]; final: boolean }) {
  if (matches.length === 0) return null;

  return (
    <section className="results">
      <h2 className="results-title">
        {final ? "Final shortlist — ranked by freshness" : "Matches so far"}
      </h2>
      <div className="results-grid">
        {matches.map((job, i) => (
          <article className="job-card" key={job.url}>
            <div className="job-rank">#{job.rank ?? i + 1}</div>
            <h3 className="job-title">{job.title}</h3>
            <p className="job-company">{job.company}</p>
            <dl className="job-facts">
              <div>
                <dt>Salary</dt>
                <dd>{job.salary_range}</dd>
              </div>
              <div>
                <dt>Experience</dt>
                <dd>{job.experience_required}</dd>
              </div>
              <div>
                <dt>Posted</dt>
                <dd>{job.posted_date}</dd>
              </div>
            </dl>
            <p className="job-reason">{job.reason}</p>
            <a className="job-link" href={job.url} target="_blank" rel="noopener noreferrer">
              View on LinkedIn ↗
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}

import type { RateLimitInfo } from "../types";
import { EnzoAvatar, HarshAvatar } from "./Avatars";

export default function LimitScreen({ info }: { info: RateLimitInfo }) {
  return (
    <div className="card limit-card">
      <div className="limit-duo">
        <HarshAvatar size={64} />
        <EnzoAvatar size={64} />
      </div>
      <h2 className="limit-title">The agency is closed for the day</h2>
      <p className="limit-message">{info.message}</p>
      <div className="limit-actions">
        <a
          className="launch-btn"
          href={info.contact_linkedin}
          target="_blank"
          rel="noopener noreferrer"
        >
          Message Harsh on LinkedIn
        </a>
        <a className="ghost-btn" href={`mailto:${info.contact_email}`}>
          Or email {info.contact_email}
        </a>
      </div>
    </div>
  );
}

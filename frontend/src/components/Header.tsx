import { EnzoAvatar, HarshAvatar } from "./Avatars";

export default function Header() {
  return (
    <header className="header">
      <div className="header-duo">
        <HarshAvatar size={46} />
        <EnzoAvatar size={46} />
      </div>
      <div>
        <h1 className="header-title">
          Harsh <span className="amp">&amp;</span> Enzo
        </h1>
        <p className="header-tag">Talent Reconnaissance · Two agents. One shortlist.</p>
      </div>
    </header>
  );
}

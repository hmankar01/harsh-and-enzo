interface AvatarProps {
  size?: number;
}

/** Harsh — the field scout. Amber, radar dish, always moving. */
export function HarshAvatar({ size = 40 }: AvatarProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-label="Harsh">
      <circle cx="24" cy="24" r="22" fill="var(--harsh-dim)" stroke="var(--harsh)" strokeWidth="2" />
      <path d="M14 30 A 12 12 0 0 1 34 30" fill="none" stroke="var(--harsh)" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M18 26 A 7 7 0 0 1 30 26" fill="none" stroke="var(--harsh)" strokeWidth="2" strokeLinecap="round" opacity="0.7" />
      <circle cx="24" cy="31" r="3" fill="var(--harsh)" />
      <line x1="24" y1="31" x2="33" y2="18" stroke="var(--harsh)" strokeWidth="2" strokeLinecap="round" />
      <circle cx="34" cy="16.5" r="2" fill="var(--harsh)" />
    </svg>
  );
}

/** Enzo — the analyst. Teal, monocle-and-clipboard energy. */
export function EnzoAvatar({ size = 40 }: AvatarProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-label="Enzo">
      <circle cx="24" cy="24" r="22" fill="var(--enzo-dim)" stroke="var(--enzo)" strokeWidth="2" />
      <circle cx="20" cy="21" r="7" fill="none" stroke="var(--enzo)" strokeWidth="2.5" />
      <line x1="25" y1="26" x2="33" y2="34" stroke="var(--enzo)" strokeWidth="3" strokeLinecap="round" />
      <path d="M17 21 l2.4 2.4 L24 18.6" fill="none" stroke="var(--enzo)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function AgentChip({ agent }: { agent: "harsh" | "enzo" | "system" }) {
  if (agent === "harsh") return <HarshAvatar size={22} />;
  if (agent === "enzo") return <EnzoAvatar size={22} />;
  return <span className="system-chip">◆</span>;
}

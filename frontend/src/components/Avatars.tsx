interface AvatarProps {
  size?: number;
}

/** Harsh — the field agent. Amber line-art: fedora, coat collar, steady eyes. */
export function HarshAvatar({ size = 40 }: AvatarProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-label="Harsh, the agent">
      <circle cx="24" cy="24" r="22" fill="var(--harsh-dim)" stroke="var(--harsh)" strokeWidth="2" />
      {/* fedora */}
      <path
        d="M13 20 h22 M16 20 c0-5 3.4-8 8-8 s8 3 8 8"
        fill="none"
        stroke="var(--harsh)"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <path d="M16 16.5 h16" stroke="var(--harsh)" strokeWidth="2" strokeLinecap="round" opacity="0.65" />
      {/* eyes */}
      <circle cx="19.5" cy="26" r="1.6" fill="var(--harsh)" />
      <circle cx="28.5" cy="26" r="1.6" fill="var(--harsh)" />
      {/* coat collar */}
      <path
        d="M13 40 l7-7 4 4 4-4 7 7"
        fill="none"
        stroke="var(--harsh)"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Enzo — the detective dog. Teal line-art: floppy ears, wet nose, tactical collar. */
export function EnzoAvatar({ size = 40 }: AvatarProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-label="Enzo, the dog">
      <circle cx="24" cy="24" r="22" fill="var(--enzo-dim)" stroke="var(--enzo)" strokeWidth="2" />
      {/* head */}
      <path
        d="M15 20 c0-6 4-9.5 9-9.5 s9 3.5 9 9.5 c0 4-1.6 7.5-4 9.5 h-10 c-2.4-2-4-5.5-4-9.5 z"
        fill="none"
        stroke="var(--enzo)"
        strokeWidth="2.2"
        strokeLinejoin="round"
      />
      {/* floppy ears */}
      <path
        d="M15.5 17 c-4 1-5.5 5-4.5 9.5 2.5-.5 4.5-2 5.5-4.5 M32.5 17 c4 1 5.5 5 4.5 9.5 -2.5-.5-4.5-2-5.5-4.5"
        fill="none"
        stroke="var(--enzo)"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* eyes + nose */}
      <circle cx="20" cy="21.5" r="1.5" fill="var(--enzo)" />
      <circle cx="28" cy="21.5" r="1.5" fill="var(--enzo)" />
      <path d="M24 26.5 l-2 -2 h4 z" fill="var(--enzo)" />
      <path d="M24 26.5 v2.5" stroke="var(--enzo)" strokeWidth="1.6" strokeLinecap="round" />
      {/* collar */}
      <path d="M17 33.5 h14" stroke="var(--enzo)" strokeWidth="2.4" strokeLinecap="round" />
      <circle cx="24" cy="36" r="1.6" fill="var(--enzo)" />
    </svg>
  );
}

export function AgentChip({ agent }: { agent: "harsh" | "enzo" | "system" }) {
  if (agent === "harsh") return <HarshAvatar size={22} />;
  if (agent === "enzo") return <EnzoAvatar size={22} />;
  return <span className="system-chip">◆</span>;
}

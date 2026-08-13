import type { Session } from "./schedule";

export type ScheduleVariant = {
  id: string;
  label: string;
  description: string;
  sessions: Session[];
  metrics: {
    conflicts: number;
    coverage: number;
    objective: number;
  };
};

function shift(day: number, period: number, delta: number): { day: number; period: number } {
  let p = period + delta;
  let d = day;
  if (p > 6) {
    p = 1;
    d = (d + 1) % 5;
  }
  if (p < 1) {
    p = 6;
    d = (d - 1 + 5) % 5;
  }
  return { day: d, period: p };
}

export function buildBeforeSessions(base: Session[]): Session[] {
  return base.map((s) => ({ ...s }));
}

export function buildAfterSessions(base: Session[]): Session[] {
  const moveIds = new Set([base[0]?.id, base[3]?.id, base[7]?.id, base[12]?.id].filter(Boolean) as string[]);
  return base.map((s) => {
    if (!moveIds.has(s.id)) return { ...s };
    const next = shift(s.day, s.period, 1);
    return { ...s, day: next.day, period: next.period };
  });
}

export const beforeMetrics = {
  conflicts: 7,
  coverage: 88,
  objective: 4120,
};

export const afterMetrics = {
  conflicts: 1,
  coverage: 97,
  objective: 4820,
};

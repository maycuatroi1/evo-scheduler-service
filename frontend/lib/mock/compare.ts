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

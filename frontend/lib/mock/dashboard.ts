export type KpiTone = "primary" | "accent" | "warning" | "neutral";

export type Kpi = {
  id: string;
  label: string;
  value: string;
  hint: string;
  tone: KpiTone;
  progress?: number;
};

export type RecentAction = {
  id: string;
  actor: string;
  verb: string;
  target: string;
  at: string;
  status: "ok" | "pending" | "failed";
};

export const kpis: Kpi[] = [
  {
    id: "active-classes",
    label: "Active Classes",
    value: "128",
    hint: "12 starting this week",
    tone: "primary",
    progress: 72,
  },
  {
    id: "teachers",
    label: "Teachers (GV)",
    value: "46",
    hint: "4 unavailable",
    tone: "accent",
    progress: 88,
  },
  {
    id: "workshops",
    label: "Workshops",
    value: "9",
    hint: "2 under maintenance",
    tone: "neutral",
    progress: 60,
  },
  {
    id: "scheduling",
    label: "Scheduling Completion",
    value: "84%",
    hint: "107 of 128 classes scheduled",
    tone: "warning",
    progress: 84,
  },
];

export const recentActions: RecentAction[] = [
  {
    id: "r1",
    actor: "Nguyễn Thị Lan",
    verb: "imported",
    target: "Teachers.xlsx",
    at: "2026-08-13 09:42",
    status: "ok",
  },
  {
    id: "r2",
    actor: "Trần Văn Minh",
    verb: "ran schedule for",
    target: "Class 10A - Math",
    at: "2026-08-13 09:15",
    status: "ok",
  },
  {
    id: "r3",
    actor: "Lê Hoàng Phúc",
    verb: "edited constraint on",
    target: "Workshop B",
    at: "2026-08-13 08:50",
    status: "pending",
  },
  {
    id: "r4",
    actor: "Phạm Thu Hà",
    verb: "rebalanced slots for",
    target: "Fall 2026",
    at: "2026-08-12 17:30",
    status: "failed",
  },
  {
    id: "r5",
    actor: "Vũ Đức Anh",
    verb: "approved import for",
    target: "StudentGroups.xlsx",
    at: "2026-08-12 16:05",
    status: "ok",
  },
];

export const upcomingSchedule = [
  { day: "Mon", load: 42 },
  { day: "Tue", load: 55 },
  { day: "Wed", load: 61 },
  { day: "Thu", load: 38 },
  { day: "Fri", load: 47 },
  { day: "Sat", load: 22 },
];

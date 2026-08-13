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

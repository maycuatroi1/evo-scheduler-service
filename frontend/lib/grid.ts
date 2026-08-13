import type { Session } from "@/lib/mock/schedule";
import type { SessionRow } from "@/lib/api";

const DAY_LABELS_VI = [
  "Thứ 2",
  "Thứ 3",
  "Thứ 4",
  "Thứ 5",
  "Thứ 6",
  "Thứ 7",
  "Chủ nhật",
];

const DAY_CODES = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

export type DayAxis = { index: number; code: string; label: string };
export type PeriodAxis = { index: number; label: string };

const DEFAULT_DAYS: DayAxis[] = DAY_LABELS_VI.slice(0, 6).map((label, i) => ({
  index: i,
  code: DAY_CODES[i],
  label,
}));

const DEFAULT_PERIODS: PeriodAxis[] = [0, 1, 2, 3, 4].map((p) => ({
  index: p,
  label: "Tiết " + (p + 1),
}));

export function dayLabel(day: number): string {
  return DAY_LABELS_VI[day] ?? "Ngày " + day;
}

export function deriveDayAxis(rows: SessionRow[] | Session[]): DayAxis[] {
  const source =
    rows.length > 0 && typeof rows[0] === "object" && "module_code" in rows[0]
      ? (rows as SessionRow[])
      : (rows as Session[]);
  let days: number[];
  if (source.length > 0 && "module_code" in source[0]) {
    days = (source as SessionRow[])
      .map((r) => r.day)
      .filter((d): d is number => d !== null && d >= 0);
  } else {
    days = (source as Session[])
      .map((s) => s.day)
      .filter((d) => d >= 0);
  }
  if (days.length === 0) return DEFAULT_DAYS;
  const dataMax = Math.max(...days);
  const start = 0;
  const end = Math.max(5, dataMax);
  const out: DayAxis[] = [];
  for (let d = start; d <= end; d++) {
    out.push({ index: d, code: DAY_CODES[d] ?? "D" + d, label: DAY_LABELS_VI[d] ?? "Ngày " + d });
  }
  return out;
}

export function derivePeriodAxis(rows: SessionRow[] | Session[]): PeriodAxis[] {
  const source = rows as Array<SessionRow | Session>;
  let periods: number[];
  if (source.length > 0 && "module_code" in source[0]) {
    periods = (source as SessionRow[])
      .map((r) => r.period)
      .filter((p): p is number => p !== null && p >= 0);
  } else {
    periods = (source as Session[]).map((s) => s.period).filter((p) => p >= 0);
  }
  if (periods.length === 0) return DEFAULT_PERIODS;
  const min = Math.min(...periods);
  const max = Math.max(...periods);
  const out: PeriodAxis[] = [];
  for (let p = min; p <= max; p++) {
    out.push({ index: p, label: "Tiết " + (p + 1) });
  }
  return out;
}

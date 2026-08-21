"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card, Empty, Field, Note, PageHeader, inputClass } from "@/components/ui";
import { createApiClient, type SessionRow } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";

const DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"];

/** Bảng giáo viên toàn tuần: mỗi dòng một giáo viên, mỗi cột một tiết. */
export default function BangGiaoVienPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<SessionRow[]>([]);
  const [scheduleId, setScheduleId] = useState<number | null>(null);
  const [shift, setShift] = useState<"S" | "C" | "A">("S");
  const [onlyGap, setOnlyGap] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    const api = createApiClient(token);
    setLoading(true);
    setError(null);
    try {
      const list = await api.listSchedules();
      if (!list.length) {
        setRows([]);
        return;
      }
      const id = scheduleId ?? list[0].id;
      setScheduleId(id);
      setRows(await api.getSessions(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải thời khoá biểu");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const placed = rows.filter((r) => r.day !== null && r.period !== null);
  const periods = placed.map((r) => r.period as number);
  const maxPeriod = periods.length ? Math.max(...periods) : 9;
  const half = Math.floor((maxPeriod + 1) / 2);

  const cols: number[] =
    shift === "A"
      ? Array.from({ length: maxPeriod + 1 }, (_, i) => i)
      : shift === "S"
        ? Array.from({ length: half }, (_, i) => i)
        : Array.from({ length: maxPeriod + 1 - half }, (_, i) => i + half);

  const days = [...new Set(placed.map((r) => r.day as number))].sort((a, b) => a - b);
  const dayList = days.length ? days : [0, 1, 2, 3, 4];

  // Gom theo giáo viên
  const byTeacher = new Map<string, { name: string; cells: Map<string, string> }>();
  for (const r of placed) {
    for (const t of r.teachers ?? []) {
      if (!byTeacher.has(t.code))
        byTeacher.set(t.code, { name: t.name, cells: new Map() });
      const entry = byTeacher.get(t.code)!;
      const dur = r.duration_slots || 1;
      for (let k = 0; k < dur; k++) {
        entry.cells.set(
          `${r.day}|${(r.period as number) + k}`,
          r.student_group_code
        );
      }
    }
  }

  let list = [...byTeacher.entries()].sort((a, b) =>
    a[1].name.localeCompare(b[1].name, "vi")
  );

  if (onlyGap) {
    list = list.filter(([, v]) => {
      for (const d of dayList) {
        const ps = cols.filter((p) => v.cells.has(`${d}|${p}`));
        if (ps.length > 1 && ps[ps.length - 1] - ps[0] + 1 > ps.length) return true;
      }
      return false;
    });
  }

  if (!token) return <Empty>Cần đăng nhập để xem bảng giáo viên.</Empty>;

  return (
    <>
      <PageHeader
        title="Bảng giáo viên"
        subtitle="Toàn tuần trên một bảng: mỗi dòng một giáo viên, mỗi cột một tiết. Ô ghi mã nhóm đang dạy."
        actions={
          <Button onClick={() => void load()} disabled={loading}>
            {loading ? "Đang tải…" : "↻ Tải lại"}
          </Button>
        }
      />

      {error && (
        <Note tone="error" icon="✕">
          {error}
        </Note>
      )}

      <Card
        title={`${list.length} giáo viên`}
        flush
        actions={
          <div className="flex flex-wrap items-end gap-3">
            <Field label="Buổi">
              <select
                className={inputClass}
                value={shift}
                onChange={(e) => setShift(e.target.value as "S" | "C" | "A")}
              >
                <option value="S">Buổi sáng</option>
                <option value="C">Buổi chiều</option>
                <option value="A">Cả ngày</option>
              </select>
            </Field>
            <label className="flex items-center gap-1.5 pb-1.5 text-[12.5px]">
              <input
                type="checkbox"
                checked={onlyGap}
                onChange={(e) => setOnlyGap(e.target.checked)}
              />
              Chỉ giáo viên có tiết trống
            </label>
          </div>
        }
      >
        {list.length === 0 ? (
          <Empty>
            {loading
              ? "Đang tải…"
              : onlyGap
                ? "Không giáo viên nào có tiết trống giữa buổi."
                : "Chưa có buổi học nào được xếp lịch."}
          </Empty>
        ) : (
          <div className="max-h-[560px] overflow-auto">
            <table className="w-full border-collapse text-[11px]">
              <thead>
                <tr>
                  <th className="sticky left-0 top-0 z-20 min-w-[140px] border border-border bg-head px-2 py-1.5 text-left font-display text-[11.5px]">
                    Giáo viên
                  </th>
                  {dayList.map((d) =>
                    cols.map((p) => (
                      <th
                        key={`${d}|${p}`}
                        className="sticky top-0 z-10 min-w-[30px] border border-border bg-head px-1 py-1 text-center font-display text-[10px]"
                      >
                        {p === cols[0] && (
                          <div className="font-semibold">{DAYS[d] ?? `N${d}`}</div>
                        )}
                        <div className="font-normal text-foreground-3">{p + 1}</div>
                      </th>
                    ))
                  )}
                  <th className="sticky top-0 z-10 border border-border bg-head px-2 py-1 text-center font-display text-[10.5px]">
                    Tổng
                  </th>
                </tr>
              </thead>
              <tbody>
                {list.map(([code, v]) => {
                  let total = 0;
                  return (
                    <tr key={code}>
                      <td className="sticky left-0 z-10 border border-border bg-panel px-2 py-1 text-[11.5px] font-medium">
                        {v.name}
                      </td>
                      {dayList.map((d) =>
                        cols.map((p) => {
                          const hit = v.cells.get(`${d}|${p}`);
                          if (hit) total++;
                          return (
                            <td
                              key={`${d}|${p}`}
                              className={`border border-border px-0.5 py-1 text-center font-mono text-[9px] ${
                                hit ? "bg-vocational-bg" : ""
                              }`}
                            >
                              {hit ?? ""}
                            </td>
                          );
                        })
                      )}
                      <td className="tabular border border-border bg-head px-2 py-1 text-center font-mono font-semibold">
                        {total}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}

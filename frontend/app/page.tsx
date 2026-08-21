"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { createApiClient, type StatsResponse } from "@/lib/api";
import { Button, Card, Empty, Note, PageHeader, Pill, Stat, Table } from "@/components/ui";
import { useV2 } from "@/lib/useV2";
import type { Group, Homeroom, WorkloadRow } from "@/lib/api-v2";

export default function DashboardPage() {
  const { token } = useAuth();
  const { api: v2 } = useV2();
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [homerooms, setHomerooms] = useState<Homeroom[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [workload, setWorkload] = useState<WorkloadRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token || !v2) return;
    setLoading(true);
    setError(null);
    try {
      const [s, h, g, w] = await Promise.all([
        createApiClient(token).getStats(),
        v2.listHomerooms(),
        v2.listGroups(),
        v2.workload(),
      ]);
      setStats(s);
      setHomerooms(h);
      setGroups(g);
      setWorkload(w.teachers);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải thống kê");
    } finally {
      setLoading(false);
    }
  }, [token, v2]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!token) return <Empty>Đăng nhập để xem tổng quan.</Empty>;

  const c = stats?.counts;
  const splitClasses = homerooms.filter((h) => h.group_count > 1);
  const overCap = groups.filter((g) => g.practice_batches > 1);
  const overQuota = workload.filter((w) => w.over > 0);
  const maxLoad = Math.max(1, ...(stats?.weekly_load ?? []).map((d) => d.load));

  return (
    <>
      <PageHeader
        title="Tổng quan"
        subtitle={
          stats
            ? `Đơn vị ${stats.tenant_code} · học kỳ I năm học 2026–2027`
            : "Đang tải dữ liệu…"
        }
        actions={
          <>
            <Button onClick={() => void load()} disabled={loading}>
              {loading ? "Đang tải…" : "↻ Tải lại"}
            </Button>
            <Link href="/xep-lich">
              <Button variant="primary">▶ Xếp thời khoá biểu</Button>
            </Link>
          </>
        }
      />

      {error && (
        <Note tone="error" icon="✕">
          {error}
        </Note>
      )}

      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <Stat
          label="Buổi cần xếp"
          value={c?.sessions ?? "—"}
          hint={`${c?.sessions_assigned ?? 0} đã xếp`}
          tone="culture"
        />
        <Stat
          label="Tỉ lệ phủ lịch"
          value={stats ? `${stats.completion}%` : "—"}
          tone={stats && stats.completion >= 95 ? "ok" : "warn"}
        />
        <Stat
          label="Nhóm nghề"
          value={groups.length}
          hint={`${homerooms.length} lớp văn hoá`}
          tone="vocational"
        />
        <Stat label="Giáo viên" value={c?.teachers ?? "—"} />
        <Stat
          label="Cần xử lý"
          value={splitClasses.length + overCap.length + overQuota.length}
          hint="cảnh báo dữ liệu"
          tone={
            overCap.length || overQuota.length ? "error" : "ok"
          }
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Việc cần xử lý">
          {splitClasses.length === 0 &&
            overCap.length === 0 &&
            overQuota.length === 0 && (
              <Note tone="ok" icon="✓">
                Không có cảnh báo nào. Dữ liệu sẵn sàng để xếp lịch.
              </Note>
            )}

          {overCap.slice(0, 3).map((g) => (
            <Note key={g.id} tone="error" icon="✕">
              <b>{g.name}</b> có {g.size} học sinh, vượt trần thực hành{" "}
              {g.hazardous ? 10 : 18} — phải chia <b>{g.practice_batches} ca</b>.
            </Note>
          ))}

          {overQuota.slice(0, 3).map((w) => (
            <Note key={w.code} tone="warn" icon="!">
              <b>{w.name}</b> vượt định mức: {w.standard_hours}/{w.quota} giờ
              chuẩn.
            </Note>
          ))}

          {splitClasses.slice(0, 3).map((h) => (
            <Note key={h.id} tone="warn" icon="⚯">
              Lớp <b>{h.code}</b> tách {h.group_count} nhóm nghề — các nhóm không
              được trùng giờ nhau.
            </Note>
          ))}
        </Card>

        <Card title="Tải giảng dạy · nhiều nhất" flush>
          <Table
            head={
              <>
                <th className="px-3 py-2">Giáo viên</th>
                <th className="px-3 py-2 text-right">Giờ chuẩn</th>
                <th className="w-28 px-3 py-2">So định mức</th>
              </>
            }
          >
            {workload.length === 0 && (
              <tr>
                <td colSpan={3}>
                  <Empty>Chưa có dữ liệu tải giảng dạy.</Empty>
                </td>
              </tr>
            )}
            {workload.slice(0, 6).map((w) => (
              <tr key={w.code} className="border-b border-border last:border-0">
                <td className="px-3 py-2">
                  <b>{w.name}</b>
                  <div className="font-mono text-[10.5px] text-foreground-3">
                    {w.code}
                  </div>
                </td>
                <td className="tabular px-3 py-2 text-right font-mono">
                  {w.standard_hours}
                </td>
                <td className="px-3 py-2">
                  {w.over > 0 ? (
                    <Pill tone="error">Vượt {w.over}</Pill>
                  ) : (
                    <Pill tone="ok">{Math.round(w.usage_pct)}%</Pill>
                  )}
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>

      {stats && stats.weekly_load.length > 0 && (
        <Card title="Tải theo ngày trong tuần">
          <div className="flex h-32 items-end gap-2">
            {stats.weekly_load.map((d) => (
              <div key={d.day} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t bg-vocational"
                  style={{ height: `${(d.load / maxLoad) * 100}%` }}
                  title={`${d.load} buổi`}
                />
                <span className="text-[11px] text-foreground-3">
                  {["T2", "T3", "T4", "T5", "T6", "T7", "CN"][Number(d.day)] ??
                    String(d.day)}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {stats && stats.schedules.length > 0 && (
        <Card title="Phương án gần đây" flush>
          <Table
            head={
              <>
                <th className="px-3 py-2">Tên</th>
                <th className="px-3 py-2">Trạng thái</th>
                <th className="px-3 py-2 text-right">Giá trị mục tiêu</th>
              </>
            }
          >
            {stats.schedules.map((s) => (
              <tr key={s.id} className="border-b border-border last:border-0">
                <td className="px-3 py-2">
                  <b>{s.name}</b>
                  <span className="ml-1.5 font-mono text-[10.5px] text-foreground-3">
                    #{s.id}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <Pill
                    tone={
                      s.status === "published" || s.status === "solved"
                        ? "ok"
                        : s.status === "failed"
                          ? "error"
                          : "muted"
                    }
                  >
                    {s.status}
                  </Pill>
                </td>
                <td className="tabular px-3 py-2 text-right font-mono">
                  {s.objective_value ?? "—"}
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </>
  );
}

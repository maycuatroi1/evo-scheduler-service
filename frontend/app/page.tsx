"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { createApiClient, type StatsResponse } from "@/lib/api";
import type { Kpi, KpiTone, RecentAction } from "@/lib/mock/dashboard";

const toneRing: Record<KpiTone, string> = {
  primary: "text-primary",
  accent: "text-accent",
  warning: "text-amber-600",
  neutral: "text-foreground",
};

const toneBar: Record<KpiTone, string> = {
  primary: "bg-primary",
  accent: "bg-accent",
  warning: "bg-amber-500",
  neutral: "bg-slate-400",
};

const statusBadge: Record<string, string> = {
  ok: "bg-accent/15 text-accent",
  pending: "bg-amber-500/15 text-amber-700",
  failed: "bg-destructive/15 text-destructive",
};

const statusLabel: Record<string, string> = {
  solved: "ok",
  draft: "pending",
  failed: "failed",
  solving: "pending",
  published: "ok",
};

export default function DashboardPage() {
  const { token } = useAuth();
  const api = useMemo(() => createApiClient(token), [token]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      setStats(null);
      return;
    }
    setLoading(true);
    setError(null);
    api
      .getStats()
      .then(setStats)
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Lỗi tải thống kê"),
      )
      .finally(() => setLoading(false));
  }, [token, api]);

  const kpis: Kpi[] = stats
    ? [
        {
          id: "teachers",
          label: "Giáo viên",
          value: String(stats.counts.teachers),
          hint: stats.counts.teachers === 0 ? "Chưa có dữ liệu" : "Đã import",
          tone: "primary",
          progress: stats.counts.teachers ? 100 : 0,
        },
        {
          id: "sessions",
          label: "Buổi học",
          value: String(stats.counts.sessions),
          hint: stats.counts.sessions_assigned + " đã xếp lịch",
          tone: "accent",
          progress:
            stats.counts.sessions
              ? Math.round(
                  (stats.counts.sessions_assigned * 100) /
                    stats.counts.sessions,
                )
              : 0,
        },
        {
          id: "resources",
          label: "Tài nguyên",
          value: String(stats.counts.resources),
          hint: "Phòng và thiết bị",
          tone: "neutral",
        },
        {
          id: "completion",
          label: "Tỉ lệ xếp lịch",
          value: stats.completion + "%",
          hint: stats.counts.sessions_assigned + " / " + stats.counts.sessions,
          tone: "warning",
          progress: stats.completion,
        },
      ]
    : [];

  const recentActions: RecentAction[] = (stats?.schedules ?? []).map((s) => ({
    id: "s-" + s.id,
    actor: "Lịch #" + s.id,
    verb: s.name,
    target: "mục tiêu " + (s.objective_value ?? "-"),
    at: "",
    status: (statusLabel[s.status] ?? "pending") as RecentAction["status"],
  }));

  const weeklyLoad = stats?.weekly_load ?? [];
  const maxLoad = Math.max(1, ...weeklyLoad.map((d) => d.load));

  if (!token) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-foreground">Dashboard</h2>
        <p className="text-sm text-foreground/60">
          Dán JWT token ở thanh trên cùng để xem thống kê thật.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Dashboard</h2>
          <p className="text-sm text-foreground/60">
            Thống kê tenant <span className="font-semibold">{stats?.tenant_code}</span> từ backend.
          </p>
        </div>
        <Link
          href="/import"
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
        >
          Import dữ liệu
        </Link>
      </div>

      {loading && (
        <p className="text-sm text-foreground/60">Đang tải thống kê...</p>
      )}
      {error && (
        <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs font-medium text-destructive">
          {error}
        </p>
      )}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((k) => (
          <div
            key={k.id}
            className="rounded-lg border border-border bg-white p-4 shadow-sm dark:bg-slate-900"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-foreground/50">
              {k.label}
            </p>
            <p className={"mt-1 text-3xl font-bold " + toneRing[k.tone]}>{k.value}</p>
            <p className="mt-1 text-xs text-foreground/60">{k.hint}</p>
            {typeof k.progress === "number" && (
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-border">
                <div
                  className={"h-full " + toneBar[k.tone]}
                  style={{ width: k.progress + "%" }}
                />
              </div>
            )}
          </div>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-white p-4 shadow-sm lg:col-span-2 dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Lịch gần đây</h3>
          {recentActions.length === 0 ? (
            <p className="text-xs text-foreground/60">Chưa có lịch nào.</p>
          ) : (
            <ul className="divide-y divide-border">
              {recentActions.map((a) => (
                <li key={a.id} className="flex items-center justify-between py-2 text-sm">
                  <div className="min-w-0">
                    <p className="truncate text-foreground">
                      <span className="font-semibold">{a.actor}</span>{" "}
                      <span className="text-foreground/60">{a.verb}</span>{" "}
                      <span className="font-medium">{a.target}</span>
                    </p>
                  </div>
                  <span
                    className={
                      "ml-3 rounded-full px-2 py-0.5 text-xs font-medium capitalize " +
                      statusBadge[a.status]
                    }
                  >
                    {a.status === "ok" ? "thành công" : a.status === "pending" ? "chờ" : "lỗi"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-lg border border-border bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Tải theo ngày</h3>
          {weeklyLoad.length === 0 ? (
            <p className="text-xs text-foreground/60">Chưa có lịch để thống kê.</p>
          ) : (
            <div className="flex h-40 items-end justify-between gap-2">
              {weeklyLoad.map((d) => (
                <div key={d.day} className="flex flex-1 flex-col items-center gap-1">
                  <div
                    className="w-full rounded-t bg-primary/80"
                    style={{ height: (d.load / maxLoad) * 100 + "%" }}
                    title={d.load + " buổi"}
                  />
                  <span className="text-xs text-foreground/60">{d.day}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

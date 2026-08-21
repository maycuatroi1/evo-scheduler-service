"use client";

import { useMemo, useState } from "react";
import { ReadOnlyScheduleGrid } from "@/components/compare/ReadOnlyScheduleGrid";
import { ScheduleSelector } from "@/components/ScheduleSelector";
import { useAuth } from "@/components/providers/AuthProvider";
import { createApiClient, toGridSessions, type SessionRow } from "@/lib/api";

type VariantMetrics = {
  conflicts: number;
  coverage: number;
  objective: number;
};

export default function ComparePage() {
  const { token } = useAuth();
  const [scheduleId, setScheduleId] = useState<number | null>(null);
  const [before, setBefore] = useState<SessionRow[]>([]);
  const [after, setAfter] = useState<SessionRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRun, setHasRun] = useState(false);

  const api = useMemo(() => createApiClient(token), [token]);

  async function handleCompare() {
    if (scheduleId === null) return;
    setBusy(true);
    setError(null);
    setHasRun(false);
    try {
      const beforeRows = await api.getSessions(scheduleId);
      setBefore(beforeRows);
      await api.solve(scheduleId);
      const afterRows = await api.getSessions(scheduleId);
      setAfter(afterRows);
      setHasRun(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi so sánh");
    } finally {
      setBusy(false);
    }
  }

  const beforeGrid = toGridSessions(before);
  const afterGrid = toGridSessions(after);

  const movedIds = useMemo(() => {
    const set = new Set<string>();
    const beforeMap = new Map(beforeGrid.map((s) => [s.id, s]));
    for (const s of afterGrid) {
      const b = beforeMap.get(s.id);
      if (b && (b.day !== s.day || b.period !== s.period)) set.add(s.id);
    }
    return set;
  }, [beforeGrid, afterGrid]);

  function metrics(rows: SessionRow[]): VariantMetrics {
    const total = rows.length;
    const assigned = rows.filter((r) => r.day !== null).length;
    const buckets = new Map<string, number>();
    let conflicts = 0;
    for (const r of rows) {
      if (r.day === null || r.period === null) continue;
      const key = r.day + ":" + r.period;
      const n = buckets.get(key) ?? 0;
      if (n > 0) conflicts += 1;
      buckets.set(key, n + 1);
    }
    const coverage = total ? Math.round((assigned * 100) / total) : 0;
    return { conflicts, coverage, objective: 0 };
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-foreground">So sánh lịch</h2>
          <p className="text-sm text-foreground-2">
            Chụp nhanh lịch trước và sau khi chạy bộ giải.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ScheduleSelector value={scheduleId} onChange={setScheduleId} />
          <button
            type="button"
            onClick={handleCompare}
            disabled={busy || scheduleId === null}
            className="rounded-md bg-primary px-4 py-1.5 text-xs font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "Đang chạy..." : "Chạy so sánh"}
          </button>
        </div>
      </div>

      {error && (
        <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs font-medium text-destructive">
          {error}
        </p>
      )}

      {hasRun && (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <VariantPanel
            label="Trước re-solve"
            description="Trạng thái lịch trước tối ưu."
            sessions={beforeGrid}
            metrics={metrics(before)}
          />
          <VariantPanel
            label="Sau re-solve"
            description="Trạng thái lịch sau khi chạy bộ giải."
            sessions={afterGrid}
            metrics={metrics(after)}
            highlightIds={movedIds}
          />
        </div>
      )}

      {!hasRun && !busy && (
        <p className="text-sm text-foreground-2">
          Chọn lịch rồi bấm "Chạy so sánh" để xem trước / sau.
        </p>
      )}
    </div>
  );
}

function VariantPanel({
  label,
  description,
  sessions,
  metrics,
  highlightIds,
}: {
  label: string;
  description: string;
  sessions: ReturnType<typeof toGridSessions>;
  metrics: VariantMetrics;
  highlightIds?: Set<string>;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-panel p-4 shadow-sm">
      <div>
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-foreground">{label}</h3>
          <div className="flex gap-3 text-xs">
            <span className="rounded bg-destructive/10 px-1.5 py-0.5 font-semibold text-destructive">
              Xung đột: {metrics.conflicts}
            </span>
            <span className="rounded bg-primary/10 px-1.5 py-0.5 font-semibold text-primary">
              Phủ: {metrics.coverage}%
            </span>
          </div>
        </div>
        <p className="mt-1 text-xs text-foreground-2">{description}</p>
      </div>
      <ReadOnlyScheduleGrid
        variantLabel={label}
        sessions={sessions}
        highlightIds={highlightIds}
      />
    </div>
  );
}

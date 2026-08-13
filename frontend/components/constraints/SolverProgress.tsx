"use client";

import { useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { createApiClient, exportBlob, type SolveResponse } from "@/lib/api";

type Phase = "idle" | "running" | "done" | "error";

type Props = {
  scheduleId: number | null;
  onSolved?: () => void;
};

export function SolverProgress({ scheduleId, onSolved }: Props) {
  const { token } = useAuth();
  const api = createApiClient(token);
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<SolveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  async function start() {
    if (phase === "running" || scheduleId === null) return;
    setPhase("running");
    setError(null);
    setResult(null);
    try {
      const res = await api.solve(scheduleId);
      setResult(res);
      setPhase(res.status === "failed" ? "error" : "done");
      if (res.status !== "failed") onSolved?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi chạy bộ giải");
      setPhase("error");
    }
  }

  function reset() {
    setPhase("idle");
    setResult(null);
    setError(null);
  }

  async function handleExport() {
    if (scheduleId === null) return;
    setExporting(true);
    try {
      await exportBlob(api.exportUrl(scheduleId), token, "schedule.xlsx");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi xuất file");
    } finally {
      setExporting(false);
    }
  }

  const placed =
    result?.tier_results.reduce((a, t) => a + t.num_assignments, 0) ?? 0;
  const totalSessions =
    result?.tier_results.reduce((a, t) => a + t.num_sessions, 0) ?? 0;
  const violations = result?.violations.length ?? 0;

  return (
    <section className="rounded-lg border border-border bg-sidebar p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-foreground/60">
            Tối ưu lịch
          </h3>
          <p className="mt-1 text-xs text-foreground/60">
            Chạy bộ giải để xếp lịch và tính lại chỉ số mục tiêu.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={start}
            disabled={phase === "running" || scheduleId === null}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {phase === "running" ? "Đang tối ưu..." : "Bắt đầu tối ưu"}
          </button>
          {phase === "done" && (
            <button
              type="button"
              onClick={handleExport}
              disabled={exporting}
              className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
            >
              {exporting ? "Đang xuất..." : "Xuất Excel"}
            </button>
          )}
          {phase !== "idle" && (
            <button
              type="button"
              onClick={reset}
              className="rounded-md border border-border px-4 py-2 text-sm font-semibold text-foreground hover:bg-primary/10"
            >
              Chạy lại
            </button>
          )}
        </div>
      </div>

      {scheduleId === null && (
        <p className="mt-3 text-xs text-foreground/60">
          Chọn một lịch trước khi chạy bộ giải.
        </p>
      )}

      <div className="mt-4">
        <div className="mb-1 flex items-center justify-between text-xs text-foreground/60">
          <span>
            {phase === "idle" && "Sẵn sàng"}
            {phase === "running" && "Đang chạy bộ giải..."}
            {phase === "done" && "Hoàn tất"}
            {phase === "error" && "Lỗi"}
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-border">
          <div
            className={
              "h-full rounded-full transition-[width] duration-150 " +
              (phase === "error" ? "bg-destructive" : "bg-primary")
            }
            style={{
              width:
                phase === "idle"
                  ? "0%"
                  : phase === "running"
                    ? "100%"
                    : "100%",
            }}
          />
        </div>
      </div>

      {phase === "done" && result && (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <MetricCard
            label="Số buổi đã xếp"
            value={placed + " / " + totalSessions}
            tone="primary"
          />
          <MetricCard
            label="Vi phạm"
            value={String(violations)}
            tone={violations === 0 ? "accent" : "warning"}
          />
          <MetricCard
            label="Giá trị mục tiêu"
            value={
              result.objective_value != null
                ? result.objective_value.toLocaleString("vi-VN")
                : "-"
            }
            tone="accent"
          />
        </div>
      )}

      {phase === "error" && (
        <div className="mt-4 space-y-2">
          {error && (
            <p className="text-xs font-medium text-destructive">{error}</p>
          )}
          {result && result.violations.length > 0 && (
            <ul className="list-inside list-disc text-xs text-destructive">
              {result.violations.slice(0, 8).map((v, i) => (
                <li key={i}>{v}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "primary" | "accent" | "warning";
}) {
  const toneText =
    tone === "primary"
      ? "text-primary"
      : tone === "accent"
        ? "text-accent"
        : "text-amber-600";
  return (
    <div className="rounded-md border border-border bg-background p-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-foreground/60">
        {label}
      </p>
      <p className={"mt-1 text-xl font-bold " + toneText}>{value}</p>
    </div>
  );
}

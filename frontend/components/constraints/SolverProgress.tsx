"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import {
  createApiClient,
  exportBlob,
  type SolveJobStatus,
} from "@/lib/api";

type Phase = "idle" | "running" | "done" | "error";

const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 10 * 60 * 1000;

const PHASE_LABELS: Record<string, string> = {
  building_model: "Đang dựng mô hình",
  solving: "Đang giải",
  post_processing: "Đang xử lý kết quả",
};

type Props = {
  scheduleId: number | null;
  onSolved?: () => void;
};

export function SolverProgress({ scheduleId, onSolved }: Props) {
  const { token } = useAuth();
  const api = createApiClient(token);
  const [phase, setPhase] = useState<Phase>("idle");
  const [job, setJob] = useState<SolveJobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startedAtRef = useRef<number>(0);
  const onSolvedRef = useRef(onSolved);
  onSolvedRef.current = onSolved;

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => stopTimer, [stopTimer]);

  const poll = useCallback(
    (jobId: string) => {
      const elapsed = Date.now() - startedAtRef.current;
      if (elapsed > POLL_TIMEOUT_MS) {
        stopTimer();
        setPhase("error");
        setError("Quá thời gian chờ bộ giải (10 phút).");
        return;
      }
      timerRef.current = setTimeout(async () => {
        try {
          const st = await api.solveJobStatus(jobId);
          setJob(st);
          if (st.status === "solved") {
            stopTimer();
            setPhase("done");
            onSolvedRef.current?.();
            return;
          }
          if (st.status === "failed") {
            stopTimer();
            setPhase("error");
            setError(st.error || "Bộ giải không tìm được phương án.");
            return;
          }
          poll(jobId);
        } catch {
          poll(jobId);
        }
      }, POLL_INTERVAL_MS);
    },
    [api, stopTimer],
  );

  async function start() {
    if (phase === "running" || scheduleId === null) return;
    stopTimer();
    setPhase("running");
    setError(null);
    setJob(null);
    startedAtRef.current = Date.now();
    try {
      const res = await api.solve(scheduleId);
      const st = await api.solveJobStatus(res.solve_job_id);
      setJob(st);
      if (st.status === "solved") {
        setPhase("done");
        onSolved?.();
        return;
      }
      if (st.status === "failed") {
        setPhase("error");
        setError(st.error || "Bộ giải không tìm được phương án.");
        return;
      }
      poll(res.solve_job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi chạy bộ giải");
      setPhase("error");
    }
  }

  function reset() {
    stopTimer();
    setPhase("idle");
    setJob(null);
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

  const tierResults = job?.metrics?.tier_results ?? [];
  const placed = tierResults.reduce((a, t) => a + t.num_assignments, 0);
  const totalSessions = tierResults.reduce((a, t) => a + t.num_sessions, 0);
  const violations = job?.metrics?.violations ?? [];
  const progress = phase === "running" ? (job?.progress ?? 5) : phase === "done" ? 100 : 0;
  const phaseLabel =
    phase === "running" && job?.phase
      ? (PHASE_LABELS[job.phase] ?? job.phase)
      : null;

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
            {phase === "running" && (phaseLabel ?? "Đang chờ bộ giải...")}
            {phase === "done" && "Hoàn tất"}
            {phase === "error" && "Lỗi"}
          </span>
          {phase === "running" && <span>{progress}%</span>}
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-border">
          <div
            className={
              "h-full rounded-full transition-[width] duration-300 " +
              (phase === "error" ? "bg-destructive" : "bg-primary")
            }
            style={{ width: progress + "%" }}
          />
        </div>
      </div>

      {phase === "done" && job && (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <MetricCard
            label="Số buổi đã xếp"
            value={placed + " / " + totalSessions}
            tone="primary"
          />
          <MetricCard
            label="Vi phạm"
            value={String(violations.length)}
            tone={violations.length === 0 ? "accent" : "warning"}
          />
          <MetricCard
            label="Giá trị mục tiêu"
            value={
              job.objective_value != null
                ? job.objective_value.toLocaleString("vi-VN")
                : "-"
            }
            tone="accent"
          />
        </div>
      )}

      {phase === "done" && tierResults.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          {tierResults.map((t) => (
            <span
              key={t.tier}
              className="rounded-full border border-border bg-background px-3 py-1 text-foreground/70"
            >
              {t.tier === "culture" ? "Văn hóa" : "Nghề"}:{" "}
              {t.num_assignments}/{t.num_sessions} buổi
              {t.objective_value != null &&
                " (mục tiêu " + t.objective_value.toLocaleString("vi-VN") + ")"}
            </span>
          ))}
        </div>
      )}

      {phase === "error" && (
        <div className="mt-4 space-y-2">
          {error && (
            <p className="text-xs font-medium text-destructive">{error}</p>
          )}
          {violations.length > 0 && (
            <ul className="list-inside list-disc text-xs text-destructive">
              {violations.slice(0, 12).map((v, i) => (
                <li key={i}>{v}</li>
              ))}
            </ul>
          )}
          {violations.length > 12 && (
            <p className="text-xs text-foreground/60">
              Còn {violations.length - 12} vấn đề nữa.
            </p>
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

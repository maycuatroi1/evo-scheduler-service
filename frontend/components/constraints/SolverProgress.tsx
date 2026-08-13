"use client";

import { useEffect, useRef, useState } from "react";
import { finalSolverMetrics, type SolverMetrics } from "@/lib/mock/constraints";

type Phase = "idle" | "running" | "done";

const TOTAL_MS = 3000;
const TICK_MS = 60;

export function SolverProgress() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [metrics, setMetrics] = useState<SolverMetrics | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  function start() {
    if (phase === "running") return;
    setPhase("running");
    setProgress(0);
    setMetrics(null);
    const startedAt = Date.now();
    timerRef.current = setInterval(() => {
      const elapsed = Date.now() - startedAt;
      const pct = Math.min(100, Math.round((elapsed / TOTAL_MS) * 100));
      setProgress(pct);
      if (pct >= 100) {
        if (timerRef.current) clearInterval(timerRef.current);
        setMetrics(finalSolverMetrics);
        setPhase("done");
      }
    }, TICK_MS);
  }

  function reset() {
    if (timerRef.current) clearInterval(timerRef.current);
    setPhase("idle");
    setProgress(0);
    setMetrics(null);
  }

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
            disabled={phase === "running"}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {phase === "running" ? "Đang tối ưu..." : "Bắt đầu tối ưu"}
          </button>
          {phase === "done" && (
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

      <div className="mt-4">
        <div className="mb-1 flex items-center justify-between text-xs text-foreground/60">
          <span>
            {phase === "idle" && "Sẵn sàng"}
            {phase === "running" && "Đang chạy bộ giải..."}
            {phase === "done" && "Hoàn tất"}
          </span>
          <span className="font-semibold text-foreground">{progress}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full bg-primary transition-[width] duration-75 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {phase === "done" && metrics && (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <MetricCard
            label="Số buổi đã xếp"
            value={`${metrics.sessionsPlaced} / ${metrics.sessionsTotal}`}
            tone="primary"
          />
          <MetricCard
            label="Xung đột còn lại"
            value={String(metrics.remainingConflicts)}
            tone={metrics.remainingConflicts === 0 ? "accent" : "warning"}
          />
          <MetricCard
            label="Giá trị mục tiêu"
            value={metrics.objectiveValue.toLocaleString("vi-VN")}
            tone="accent"
          />
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
      <p className={`mt-1 text-xl font-bold ${toneText}`}>{value}</p>
    </div>
  );
}

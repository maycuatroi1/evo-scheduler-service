"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { createApiClient, type FeasibilityReport } from "@/lib/api";

type Props = {
  scheduleId: number | null;
  reloadToken?: number;
};

const TIER_LABELS: Record<string, string> = {
  culture: "Văn hóa",
  vocational: "Nghề",
  all: "Toàn bộ",
};

export function FeasibilityPanel({ scheduleId, reloadToken }: Props) {
  const { token } = useAuth();
  const api = createApiClient(token);
  const [report, setReport] = useState<FeasibilityReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token || scheduleId === null) {
      setReport(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReport(await api.getFeasibility(scheduleId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi kiểm tra dữ liệu");
    } finally {
      setLoading(false);
    }
  }, [token, scheduleId, reloadToken]);

  useEffect(() => {
    load();
  }, [load]);

  if (!token || scheduleId === null) return null;

  return (
    <section className="rounded-lg border border-border bg-panel p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-foreground-2">
            Kiểm tra dữ liệu
          </h3>
          <p className="mt-1 text-xs text-foreground-2">
            Những mâu thuẫn khiến không lịch nào tồn tại, phát hiện trước khi
            chạy bộ giải.
          </p>
        </div>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="rounded-md border border-border px-4 py-2 text-sm font-semibold text-foreground hover:bg-primary/10 disabled:opacity-50"
        >
          {loading ? "Đang kiểm tra..." : "Kiểm tra lại"}
        </button>
      </div>

      {error && (
        <p className="mt-3 text-xs font-medium text-destructive">{error}</p>
      )}

      {report && report.feasible && (
        <p className="mt-3 rounded-md border border-accent/40 bg-accent/10 px-3 py-2 text-sm text-accent">
          Dữ liệu không có mâu thuẫn hiển nhiên. Có thể chạy bộ giải.
        </p>
      )}

      {report && !report.feasible && (
        <p className="mt-3 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
          {report.blocking_count} vấn đề khiến bộ giải chắc chắn không tìm được
          lịch. Hãy sửa dữ liệu hoặc nới khung thời khoá biểu trước khi chạy.
        </p>
      )}

      {report?.tiers.map((tier) => (
        <div key={tier.tier} className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-foreground-2">
            {TIER_LABELS[tier.tier] ?? tier.tier} — {tier.num_sessions} buổi /{" "}
            {tier.total_slots} tiết mỗi tuần
          </p>
          {tier.issues.length === 0 ? (
            <p className="mt-1 text-xs text-foreground-3">Không có vấn đề.</p>
          ) : (
            <ul className="mt-2 flex flex-col gap-1">
              {tier.issues.map((issue, index) => (
                <li
                  key={tier.tier + index}
                  className={
                    "flex gap-2 rounded-md border px-3 py-2 text-xs " +
                    (issue.severity === "error"
                      ? "border-destructive/30 bg-destructive/5 text-destructive"
                      : "border-border bg-background text-foreground/70")
                  }
                >
                  <span className="font-semibold uppercase">
                    {issue.severity === "error" ? "Lỗi" : "Lưu ý"}
                  </span>
                  <span>{issue.message}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </section>
  );
}

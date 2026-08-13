import { ReadOnlyScheduleGrid } from "@/components/compare/ReadOnlyScheduleGrid";
import {
  afterMetrics,
  buildAfterSessions,
  buildBeforeSessions,
  beforeMetrics,
} from "@/lib/mock/compare";
import { sessions as initialSessions } from "@/lib/mock/schedule";

export default function ComparePage() {
  const beforeSessions = buildBeforeSessions(initialSessions);
  const afterSessions = buildAfterSessions(initialSessions);
  const movedIds = new Set(
    afterSessions
      .filter((s, i) => {
        const before = beforeSessions[i];
        return before && (before.day !== s.day || before.period !== s.period);
      })
      .map((s) => s.id),
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">So sánh lịch</h2>
          <p className="text-sm text-foreground/60">
            So sánh lịch trước và sau khi chạy lại bộ giải (bản mẫu - mock).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <VariantPanel
          label="Trước re-solve"
          description="Trạng thái lịch trước tối ưu."
          sessions={beforeSessions}
          metrics={beforeMetrics}
        />
        <VariantPanel
          label="Sau re-solve"
          description="Trạng thái lịch sau khi chạy bộ giải."
          sessions={afterSessions}
          metrics={afterMetrics}
          highlightIds={movedIds}
        />
      </div>
    </div>
  );
}

type VariantMetrics = {
  conflicts: number;
  coverage: number;
  objective: number;
};

function VariantPanel({
  label,
  description,
  sessions,
  metrics,
  highlightIds,
}: {
  label: string;
  description: string;
  sessions: ReturnType<typeof buildBeforeSessions>;
  metrics: VariantMetrics;
  highlightIds?: Set<string>;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-sidebar p-4 shadow-sm">
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
            <span className="rounded bg-accent/10 px-1.5 py-0.5 font-semibold text-accent">
              Mục tiêu: {metrics.objective}
            </span>
          </div>
        </div>
        <p className="mt-1 text-xs text-foreground/60">{description}</p>
      </div>
      <ReadOnlyScheduleGrid
        variantLabel={label}
        sessions={sessions}
        highlightIds={highlightIds}
      />
    </div>
  );
}

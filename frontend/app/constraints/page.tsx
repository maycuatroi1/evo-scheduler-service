"use client";

import { useState } from "react";
import { ConstraintBuilder } from "@/components/constraints/ConstraintBuilder";
import { SolverProgress } from "@/components/constraints/SolverProgress";
import { ScheduleSelector } from "@/components/ScheduleSelector";

export default function ConstraintsPage() {
  const [scheduleId, setScheduleId] = useState<number | null>(null);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Ràng buộc</h2>
          <p className="text-sm text-foreground/60">
            Cấu hình trọng số và chạy tối ưu lịch thật từ backend.
          </p>
        </div>
        <ScheduleSelector value={scheduleId} onChange={setScheduleId} />
      </div>
      <ConstraintBuilder scheduleId={scheduleId} />
      <SolverProgress scheduleId={scheduleId} />
    </div>
  );
}

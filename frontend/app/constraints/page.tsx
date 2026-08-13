import { ConstraintBuilder } from "@/components/constraints/ConstraintBuilder";
import { SolverProgress } from "@/components/constraints/SolverProgress";

export default function ConstraintsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Ràng buộc</h2>
          <p className="text-sm text-foreground/60">
            Xây dựng bộ ràng buộc và chạy tối ưu lịch (bản mẫu - mock).
          </p>
        </div>
      </div>
      <ConstraintBuilder />
      <SolverProgress />
    </div>
  );
}

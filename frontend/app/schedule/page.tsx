import { ScheduleGrid } from "@/components/schedule/ScheduleGrid";

export default function SchedulePage() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-foreground">Schedule Grid</h2>
        <span className="text-xs text-foreground/60">
          Prototype - mock data, khoa Điện
        </span>
      </div>
      <ScheduleGrid />
    </div>
  );
}

"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useDroppable,
  useSensor,
  useSensors,
  type DragCancelEvent,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import {
  distinctTeachers,
  distinctValues,
  type Conflict,
  type SessionRow,
} from "@/lib/api";
import {
  deriveDayAxis,
  derivePeriodAxis,
  type DayAxis,
  type PeriodAxis,
} from "@/lib/grid";
import { isConflict, type Session } from "@/lib/mock/schedule";
import { SessionCard, SessionCardPreview } from "./SessionCard";

type ViewMode = "teacher" | "class" | "room";

type Filters = {
  teacher: string;
  classCode: string;
  room: string;
};

const NONE = "all";

function cellId(day: number, period: number) {
  return "cell-" + day + "-" + period;
}

type Props = {
  scheduleId: number | null;
  sessions: Session[];
  conflicts: Conflict[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
};

export function ScheduleGrid({
  scheduleId,
  sessions,
  conflicts,
  loading,
  error,
  onRefresh,
}: Props) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [view, setView] = useState<ViewMode>("teacher");
  const [localOverride, setLocalOverride] = useState<Session[] | null>(null);
  const [filters, setFilters] = useState<Filters>({
    teacher: NONE,
    classCode: NONE,
    room: NONE,
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  );

  const days: DayAxis[] = useMemo(() => deriveDayAxis(sessions), [sessions]);
  const periods: PeriodAxis[] = useMemo(
    () => derivePeriodAxis(sessions),
    [sessions],
  );

  const effectiveSessions = localOverride ?? sessions;

  const conflictCells = useMemo(() => {
    const set = new Set<string>();
    for (const c of conflicts) set.add(cellId(c.day, c.period));
    return set;
  }, [conflicts]);

  const activeSession = useMemo(
    () => effectiveSessions.find((s) => s.id === activeId) ?? null,
    [effectiveSessions, activeId],
  );

  const cellMap = useMemo(() => {
    const map = new Map<string, Session[]>();
    for (const s of effectiveSessions) {
      const key = cellId(s.day, s.period);
      const arr = map.get(key) ?? [];
      arr.push(s);
      map.set(key, arr);
    }
    return map;
  }, [effectiveSessions]);

  const teacherOptions = useMemo(
    () => distinctTeachers(sessions.length ? toRows(sessions) : []),
    [sessions],
  );
  const classOptions = useMemo(
    () => distinctValues(toRows(sessions), "student_group_code"),
    [sessions],
  );
  const roomOptions = useMemo(
    () => distinctValues(toRows(sessions), "resource_code"),
    [sessions],
  );

  const anyFilterActive =
    filters.teacher !== NONE ||
    filters.classCode !== NONE ||
    filters.room !== NONE;

  const onDragStart = (e: DragStartEvent) => setActiveId(String(e.active.id));

  const onDragEnd = (e: DragEndEvent) => {
    setActiveId(null);
    if (!e.over) return;
    const dragged = effectiveSessions.find((s) => s.id === String(e.active.id));
    if (!dragged) return;
    const match = String(e.over.id).match(/^cell-(\d+)-(-?\d+)$/);
    if (!match) return;
    const day = Number(match[1]);
    const period = Number(match[2]);
    if (dragged.day === day && dragged.period === period) return;
    setLocalOverride((prev) => {
      const base = prev ?? effectiveSessions;
      return base.map((s) => (s.id === dragged.id ? { ...s, day, period } : s));
    });
  };

  const onDragCancel = (_e: DragCancelEvent) => setActiveId(null);

  const onCardClick = (s: Session) =>
    setFilters((prev) => ({
      ...prev,
      teacher: prev.teacher === s.teacherCode ? NONE : s.teacherCode,
    }));

  if (loading) {
    return (
      <p className="text-sm text-foreground/60">Đang tải dữ liệu lịch...</p>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col gap-2">
        <p className="text-sm font-semibold text-destructive">{error}</p>
        <button
          type="button"
          onClick={onRefresh}
          className="self-start rounded-md border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-primary/10"
        >
          Thử lại
        </button>
      </div>
    );
  }

  if (!scheduleId) {
    return (
      <p className="text-sm text-foreground/60">
        Chưa có lịch nào. Hãy tạo lịch ở trang Ràng buộc hoặc Import dữ liệu trước.
      </p>
    );
  }

  if (effectiveSessions.length === 0) {
    return (
      <p className="text-sm text-foreground/60">
        Chưa có buổi học nào được xếp lịch. Chạy bộ giải ở trang Ràng buộc để
        xếp lịch.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-border bg-sidebar p-3 text-sidebar-foreground">
        <FilterSelect
          label="Giáo viên"
          value={filters.teacher}
          onChange={(v) => setFilters((p) => ({ ...p, teacher: v }))}
          options={teacherOptions.map((t) => ({
            value: t.code,
            label: t.code + " - " + t.name,
          }))}
        />
        <FilterSelect
          label="Lớp"
          value={filters.classCode}
          onChange={(v) => setFilters((p) => ({ ...p, classCode: v }))}
          options={classOptions.map((c) => ({ value: c, label: c }))}
        />
        <FilterSelect
          label="Phòng"
          value={filters.room}
          onChange={(v) => setFilters((p) => ({ ...p, room: v }))}
          options={roomOptions.map((r) => ({ value: r, label: r }))}
        />
        <div className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase text-foreground/60">
            Xem theo
          </span>
          <div className="flex overflow-hidden rounded-md border border-border">
            {(["teacher", "class", "room"] as ViewMode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setView(m)}
                className={[
                  "px-3 py-1.5 text-xs font-semibold capitalize transition-colors",
                  view === m
                    ? "bg-primary text-white"
                    : "bg-background text-foreground hover:bg-primary/10",
                ].join(" ")}
              >
                {m === "teacher" ? "giáo viên" : m === "class" ? "lớp" : "phòng"}
              </button>
            ))}
          </div>
        </div>
        {anyFilterActive && (
          <button
            type="button"
            onClick={() => setFilters({ teacher: NONE, classCode: NONE, room: NONE })}
            className="self-end rounded-md border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-destructive hover:text-white"
          >
            Bỏ lọc
          </button>
        )}
        {localOverride && (
          <button
            type="button"
            onClick={() => setLocalOverride(null)}
            className="self-end rounded-md border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-primary/10"
          >
            Hoàn tác kéo thả
          </button>
        )}
        <div className="ml-auto self-end text-xs text-foreground/60">
          {effectiveSessions.length} buổi
          {conflicts.length > 0 && (
            <span className="ml-2 rounded bg-destructive/15 px-1.5 py-0.5 font-semibold text-destructive">
              {conflicts.length} xung đột
            </span>
          )}
        </div>
      </div>

      <DndContext
        sensors={sensors}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
        onDragCancel={onDragCancel}
      >
        <div className="overflow-auto rounded-lg border border-border bg-sidebar shadow-sm">
          <div
            className="grid min-w-[860px]"
            style={{
              gridTemplateColumns: "90px repeat(" + days.length + ", minmax(160px, 1fr))",
            }}
          >
            <div className="sticky left-0 top-0 z-30 border-b border-r border-border bg-sidebar px-2 py-2 text-[11px] font-semibold uppercase text-foreground/60">
              Tiết / Ngày
            </div>
            {days.map((d) => (
              <div
                key={d.index}
                className="sticky top-0 z-20 border-b border-r border-border bg-sidebar px-2 py-2 text-sm font-bold text-foreground"
              >
                <div>{d.code}</div>
                <div className="text-[11px] font-medium text-foreground/60">
                  {d.label}
                </div>
              </div>
            ))}

            {periods.map((p) => (
              <PeriodRow
                key={p.index}
                period={p.index}
                periodLabel={p.label}
                days={days}
                cellMap={cellMap}
                conflictCells={conflictCells}
                activeSession={activeSession}
                view={view}
                anyFilterActive={anyFilterActive}
                filters={filters}
                onCardClick={onCardClick}
              />
            ))}
          </div>
        </div>

        <DragOverlay dropAnimation={null}>
          {activeSession ? (
            <SessionCardPreview session={activeSession} />
          ) : null}
        </DragOverlay>
      </DndContext>

      <p className="text-xs text-foreground/60">
        Kéo thẻ giữa các ô. Viền đỏ = trùng giáo viên, phòng hoặc lớp. Bấm thẻ
        để lọc theo giáo viên.
      </p>
    </div>
  );
}

function toRows(sessions: Session[]): SessionRow[] {
  return sessions.map((s) => ({
    id: Number(s.id),
    module_code: s.moduleCode,
    module_name: s.moduleName,
    student_group_code: s.classCode,
    student_group_name: s.classCode,
    session_type: s.type === "TH" ? "practice" : "theory",
    tier: null,
    duration_slots: 1,
    is_locked: false,
    day: s.day,
    period: s.period,
    day_name: null,
    resource_code: s.room || null,
    teachers: s.teacherCode
      ? [{ code: s.teacherCode, name: s.teacherName }]
      : [],
  }));
}

function PeriodRow({
  period,
  periodLabel,
  days,
  cellMap,
  conflictCells,
  activeSession,
  view,
  anyFilterActive,
  filters,
  onCardClick,
}: {
  period: number;
  periodLabel: string;
  days: DayAxis[];
  cellMap: Map<string, Session[]>;
  conflictCells: Set<string>;
  activeSession?: Session | null;
  view: ViewMode;
  anyFilterActive: boolean;
  filters: Filters;
  onCardClick: (s: Session) => void;
}) {
  return (
    <>
      <div className="sticky left-0 z-10 flex items-center border-b border-r border-border bg-sidebar px-2 text-xs font-semibold text-foreground">
        {periodLabel}
      </div>
      {days.map((d) => (
        <GridCell
          key={d.index}
          day={d.index}
          period={period}
          list={cellMap.get(cellId(d.index, period)) ?? []}
          conflict={conflictCells.has(cellId(d.index, period))}
          activeSession={activeSession}
          view={view}
          anyFilterActive={anyFilterActive}
          filters={filters}
          onCardClick={onCardClick}
        />
      ))}
    </>
  );
}

function GridCell({
  day,
  period,
  list,
  conflict,
  activeSession,
  view,
  anyFilterActive,
  filters,
  onCardClick,
}: {
  day: number;
  period: number;
  list: Session[];
  conflict: boolean;
  activeSession?: Session | null;
  view: ViewMode;
  anyFilterActive: boolean;
  filters: Filters;
  onCardClick: (s: Session) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: cellId(day, period) });
  const wouldConflict = useMemo(
    () =>
      isOver &&
      !!activeSession &&
      isConflict(list, { ...activeSession, day, period }),
    [isOver, activeSession, list, day, period],
  );
  const hasConflict = conflict || isConflict(list);

  return (
    <div
      ref={setNodeRef}
      className={[
        "min-h-[88px] border-b border-r border-border bg-background/40 p-1 transition-colors",
        isOver && !wouldConflict ? "bg-primary/5" : "",
        wouldConflict || hasConflict
          ? "ring-2 ring-inset ring-destructive"
          : "",
      ].join(" ")}
    >
      <div className="flex flex-col gap-1">
        {list.map((s) => {
          const highlighted =
            (filters.teacher !== NONE && s.teacherCode === filters.teacher) ||
            (filters.classCode !== NONE && s.classCode === filters.classCode) ||
            (filters.room !== NONE && s.room === filters.room);
          const dimmed = anyFilterActive && !highlighted;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => onCardClick(s)}
              className="block w-full text-left"
            >
              <SessionCard
                session={s}
                view={view}
                highlighted={highlighted}
                dimmed={dimmed}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[11px] font-semibold uppercase text-foreground/60">
        {label}
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-border bg-background px-2 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none"
      >
        <option value={NONE}>Tất cả</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

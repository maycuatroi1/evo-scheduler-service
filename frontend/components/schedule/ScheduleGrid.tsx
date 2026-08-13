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
  classes,
  days,
  isConflict,
  periods,
  rooms,
  sessions as initialSessions,
  teachers,
  type Session,
} from "@/lib/mock/schedule";
import { SessionCard, SessionCardPreview } from "./SessionCard";

type ViewMode = "teacher" | "class" | "room";

type Filters = {
  teacher: string;
  classCode: string;
  room: string;
};

const NONE = "all";

function cellId(day: number, period: number) {
  return `cell-${day}-${period}`;
}

function GridCell({
  day,
  period,
  list,
  activeSession,
  view,
  anyFilterActive,
  filters,
  onCardClick,
}: {
  day: number;
  period: number;
  list: Session[];
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
  const hasConflict = isConflict(list);

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

export function ScheduleGrid() {
  const [sessions, setSessions] = useState<Session[]>(initialSessions);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [view, setView] = useState<ViewMode>("teacher");
  const [filters, setFilters] = useState<Filters>({
    teacher: NONE,
    classCode: NONE,
    room: NONE,
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  );

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeId) ?? null,
    [sessions, activeId],
  );

  const cellMap = useMemo(() => {
    const map = new Map<string, Session[]>();
    for (const s of sessions) {
      const key = cellId(s.day, s.period);
      const arr = map.get(key) ?? [];
      arr.push(s);
      map.set(key, arr);
    }
    return map;
  }, [sessions]);

  const anyFilterActive =
    filters.teacher !== NONE ||
    filters.classCode !== NONE ||
    filters.room !== NONE;

  const onDragStart = (e: DragStartEvent) => setActiveId(String(e.active.id));

  const onDragEnd = (e: DragEndEvent) => {
    setActiveId(null);
    if (!e.over) return;
    const dragged = sessions.find((s) => s.id === String(e.active.id));
    if (!dragged) return;
    const match = String(e.over.id).match(/^cell-(\d+)-(\d+)$/);
    if (!match) return;
    const day = Number(match[1]);
    const period = Number(match[2]);
    if (dragged.day === day && dragged.period === period) return;
    setSessions((prev) =>
      prev.map((s) => (s.id === dragged.id ? { ...s, day, period } : s)),
    );
  };

  const onDragCancel = (_e: DragCancelEvent) => setActiveId(null);

  const onCardClick = (s: Session) =>
    setFilters((prev) => ({
      ...prev,
      teacher:
        prev.teacher === s.teacherCode ? NONE : s.teacherCode,
    }));

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-border bg-sidebar p-3 text-sidebar-foreground">
        <FilterSelect
          label="Teacher"
          value={filters.teacher}
          onChange={(v) => setFilters((p) => ({ ...p, teacher: v }))}
          options={teachers.map((t) => ({
            value: t.code,
            label: `${t.code} - ${t.name}`,
          }))}
        />
        <FilterSelect
          label="Class"
          value={filters.classCode}
          onChange={(v) => setFilters((p) => ({ ...p, classCode: v }))}
          options={classes.map((c) => ({ value: c, label: c }))}
        />
        <FilterSelect
          label="Room"
          value={filters.room}
          onChange={(v) => setFilters((p) => ({ ...p, room: v }))}
          options={rooms.map((r) => ({ value: r, label: r }))}
        />
        <div className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase text-foreground/60">
            View by
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
                {m}
              </button>
            ))}
          </div>
        </div>
        {anyFilterActive && (
          <button
            type="button"
            onClick={() =>
              setFilters({ teacher: NONE, classCode: NONE, room: NONE })
            }
            className="self-end rounded-md border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-destructive hover:text-white"
          >
            Clear filters
          </button>
        )}
        <div className="ml-auto self-end text-xs text-foreground/60">
          {sessions.length} sessions
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
              gridTemplateColumns: `90px repeat(${days.length}, minmax(160px, 1fr))`,
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
                cellMap={cellMap}
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
        Kéo thẻ giữa các ô. Viền đỏ = trùng giáo viên hoặc phòng. Bấm thẻ để
        lọc theo giáo viên.
      </p>
    </div>
  );
}

function PeriodRow({
  period,
  periodLabel,
  cellMap,
  activeSession,
  view,
  anyFilterActive,
  filters,
  onCardClick,
}: {
  period: number;
  periodLabel: string;
  cellMap: Map<string, Session[]>;
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
        <option value={NONE}>All</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

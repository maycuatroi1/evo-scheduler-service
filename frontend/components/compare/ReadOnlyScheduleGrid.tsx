import { days, periods, type Session } from "@/lib/mock/schedule";

type Props = {
  variantLabel: string;
  sessions: Session[];
  highlightIds?: Set<string>;
};

function cellId(day: number, period: number) {
  return `${day}-${period}`;
}

export function ReadOnlyScheduleGrid({ variantLabel, sessions, highlightIds }: Props) {
  const cellMap = new Map<string, Session[]>();
  for (const s of sessions) {
    const key = cellId(s.day, s.period);
    const arr = cellMap.get(key) ?? [];
    arr.push(s);
    cellMap.set(key, arr);
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-foreground">{variantLabel}</span>
        <span className="text-xs text-foreground/60">{sessions.length} buổi</span>
      </div>
      <div className="overflow-auto rounded-lg border border-border bg-sidebar shadow-sm">
        <div
          className="grid min-w-[640px]"
          style={{
            gridTemplateColumns: `70px repeat(${days.length}, minmax(110px, 1fr))`,
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
              <div className="text-[11px] font-medium text-foreground/60">{d.label}</div>
            </div>
          ))}
          {periods.map((p) => (
            <Row
              key={p.index}
              period={p.index}
              periodLabel={p.label}
              cellMap={cellMap}
              highlightIds={highlightIds}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Row({
  period,
  periodLabel,
  cellMap,
  highlightIds,
}: {
  period: number;
  periodLabel: string;
  cellMap: Map<string, Session[]>;
  highlightIds?: Set<string>;
}) {
  return (
    <>
      <div className="sticky left-0 z-10 flex items-center border-b border-r border-border bg-sidebar px-2 text-xs font-semibold text-foreground">
        {periodLabel}
      </div>
      {days.map((d) => {
        const list = cellMap.get(cellId(d.index, period)) ?? [];
        return (
          <div
            key={d.index}
            className="min-h-[64px] border-b border-r border-border bg-background/40 p-1"
          >
            <div className="flex flex-col gap-1">
              {list.map((s) => {
                const moved = highlightIds?.has(s.id);
                return (
                  <div
                    key={s.id}
                    className={[
                      "rounded-md border border-border border-l-4 px-1.5 py-1 text-left shadow-sm",
                      s.type === "LT" ? "border-l-primary" : "border-l-accent",
                      moved ? "ring-2 ring-accent" : "",
                    ].join(" ")}
                  >
                    <div className="flex items-center justify-between gap-1">
                      <span className="truncate text-[11px] font-bold text-foreground">
                        {s.moduleCode}
                      </span>
                      <span
                        className={[
                          "rounded border px-1 text-[9px] font-semibold",
                          s.type === "LT"
                            ? "border-primary/30 bg-primary/10 text-primary"
                            : "border-accent/30 bg-accent/10 text-accent",
                        ].join(" ")}
                      >
                        {s.type}
                      </span>
                    </div>
                    <div className="truncate text-[11px] font-semibold text-foreground">
                      {s.teacherName}
                    </div>
                    <div className="truncate text-[10px] text-foreground/70">
                      {s.classCode} - {s.room}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </>
  );
}

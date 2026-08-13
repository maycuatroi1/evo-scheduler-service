import { CSS } from "@dnd-kit/utilities";
import { useDraggable } from "@dnd-kit/core";
import type { Session } from "@/lib/mock/schedule";

type ViewMode = "teacher" | "class" | "room";

type Props = {
  session: Session;
  view: ViewMode;
  highlighted: boolean;
  dimmed: boolean;
  dragging?: boolean;
};

const typeStyles: Record<Session["type"], string> = {
  LT: "bg-primary/10 text-primary border-primary/30",
  TH: "bg-accent/10 text-accent border-accent/30",
};

const cardTone: Record<Session["type"], string> = {
  LT: "border-l-primary",
  TH: "border-l-accent",
};

export function SessionCard({
  session,
  view,
  highlighted,
  dimmed,
  dragging,
}: Props) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: session.id,
    });

  const style = {
    transform: CSS.Translate.toString(transform),
  };

  const head =
    view === "teacher"
      ? session.teacherName
      : view === "class"
        ? session.classCode
        : session.room;
  const sub =
    view === "teacher"
      ? `${session.classCode} - ${session.room}`
      : view === "class"
        ? `${session.teacherName} - ${session.room}`
        : `${session.teacherName} - ${session.classCode}`;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={[
        "select-none rounded-md border border-border border-l-4 bg-white px-2 py-1.5 text-left shadow-sm transition-opacity",
        cardTone[session.type],
        highlighted ? "ring-2 ring-accent ring-offset-1" : "",
        dimmed || isDragging ? "opacity-40" : "hover:shadow-md",
        dragging ? "cursor-grabbing" : "cursor-grab",
      ].join(" ")}
      data-session-id={session.id}
    >
      <div className="flex items-center justify-between gap-1">
        <span className="truncate text-xs font-bold text-foreground">
          {session.moduleCode}
        </span>
        <span
          className={`rounded border px-1 text-[10px] font-semibold ${typeStyles[session.type]}`}
        >
          {session.type}
        </span>
      </div>
      <div className="mt-0.5 truncate text-xs font-semibold text-foreground">
        {head}
      </div>
      <div className="truncate text-[11px] text-foreground/70">{sub}</div>
    </div>
  );
}

export function SessionCardPreview({ session }: { session: Session }) {
  return (
    <div className="w-44 rounded-md border border-border border-l-4 border-l-primary bg-white px-2 py-1.5 shadow-lg">
      <div className="flex items-center justify-between gap-1">
        <span className="truncate text-xs font-bold text-foreground">
          {session.moduleCode}
        </span>
        <span
          className={`rounded border px-1 text-[10px] font-semibold ${typeStyles[session.type]}`}
        >
          {session.type}
        </span>
      </div>
      <div className="mt-0.5 truncate text-xs font-semibold text-foreground">
        {session.teacherName}
      </div>
      <div className="truncate text-[11px] text-foreground/70">
        {session.classCode} - {session.room}
      </div>
    </div>
  );
}

"use client";

import { useEffect } from "react";
import type { Session } from "@/lib/mock/schedule";
import { tierColor, tierLabel, sessionTypeLabel } from "@/lib/labels";

type Props = {
  session: Session | null;
  onClose: () => void;
  onFilterTeacher?: (code: string) => void;
};

function InfoRow({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 border-b border-border/60 py-2.5 last:border-0">
      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center text-foreground/50">
        {icon}
      </span>
      <div className="min-w-0 flex-1">
        <dt className="text-[11px] font-semibold uppercase tracking-wide text-foreground/50">
          {label}
        </dt>
        <dd className="mt-0.5 text-sm font-medium text-foreground">{children}</dd>
      </div>
    </div>
  );
}

export function SessionDetailModal({ session, onClose, onFilterTeacher }: Props) {
  useEffect(() => {
    if (!session) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [session, onClose]);

  if (!session) return null;

  const tc = tierColor(session.tier);
  const teachers = session.teachers ?? (session.teacherCode ? [{ code: session.teacherCode, name: session.teacherName }] : []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Chi tiết buổi học"
    >
      <div
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative z-10 w-full max-w-md overflow-hidden rounded-xl border border-border bg-sidebar shadow-2xl">
        <div className={`flex items-center justify-between gap-3 border-b border-border px-5 py-3.5 ${tc.soft}`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${tc.dot}`} />
            <span className="truncate text-base font-bold text-foreground">
              {session.moduleName || session.moduleCode}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-foreground/60 transition-colors hover:bg-foreground/10 hover:text-foreground"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2 border-b border-border px-5 py-3">
          <span className={`rounded border px-2 py-0.5 text-[11px] font-semibold ${tc.badge}`}>
            {tierLabel(session.tier)}
          </span>
          <span className={`rounded border px-2 py-0.5 text-[11px] font-semibold ${
            session.type === "TH"
              ? "border-accent/30 bg-accent/10 text-accent"
              : "border-primary/30 bg-primary/10 text-primary"
          }`}>
            {sessionTypeLabel(session.type)}
          </span>
          {session.locked && (
            <span className="flex items-center gap-1 rounded border border-foreground/20 bg-foreground/5 px-2 py-0.5 text-[11px] font-semibold text-foreground/60">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="5" y="11" width="14" height="10" rx="2" />
                <path d="M8 11V7a4 4 0 0 1 8 0v4" />
              </svg>
              Đã khóa
            </span>
          )}
          <span className="ml-auto font-mono text-[11px] text-foreground/40">
            #{session.id}
          </span>
        </div>

        <dl className="px-5 py-2">
          <InfoRow
            label="Mã môn học"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /></svg>}
          >
            {session.moduleCode}
          </InfoRow>

          {teachers.length > 0 && (
            <InfoRow
              label={teachers.length > 1 ? "Giáo viên (%s)".replace("%s", String(teachers.length)) : "Giáo viên"}
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>}
            >
              <div className="flex flex-col gap-1">
                {teachers.map((t) => (
                  <span key={t.code} className="flex items-center gap-1.5">
                    {t.name}
                    <code className="rounded bg-foreground/5 px-1 text-[11px] text-foreground/50">{t.code}</code>
                  </span>
                ))}
              </div>
            </InfoRow>
          )}

          <InfoRow
            label="Lớp học"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c3 3 9 3 12 0v-5" /></svg>}
          >
            {session.className || session.classCode}
            {session.className && session.classCode !== session.className && (
              <code className="ml-1.5 rounded bg-foreground/5 px-1 text-[11px] text-foreground/50">{session.classCode}</code>
            )}
          </InfoRow>

          <InfoRow
            label="Phòng / Thiết bị"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4" /></svg>}
          >
            {session.room || <span className="text-foreground/40">(chưa xếp phòng)</span>}
          </InfoRow>

          <InfoRow
            label="Thời gian"
            icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>}
          >
            {session.dayName || dayLabelVi(session.day)}
            {", tiết %s".replace("%s", String(session.period + 1))}
            {session.duration && session.duration > 1 && (
              <span className="text-foreground/50"> ({session.duration} tiết)</span>
            )}
          </InfoRow>
        </dl>

        <div className="flex items-center gap-2 border-t border-border bg-foreground/[0.02] px-5 py-3">
          {onFilterTeacher && session.teacherCode && (
            <button
              type="button"
              onClick={() => {
                onFilterTeacher(session.teacherCode);
                onClose();
              }}
              className="flex items-center gap-1.5 rounded-md border border-border bg-sidebar px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:bg-primary/5 hover:text-primary"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z" /></svg>
              Lọc theo GV này
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="ml-auto rounded-md bg-primary px-4 py-1.5 text-xs font-semibold text-white transition-opacity hover:opacity-90"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}

function dayLabelVi(day: number): string {
  const labels = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"];
  return labels[day] ?? "Ngày " + day;
}

"use client";

import type { ReactNode } from "react";

/* Bộ thành phần dùng chung cho các trang. Gom vào một chỗ để mọi trang
   trông như một hệ thống, và để đổi kiểu dáng chỉ phải sửa một nơi. */

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-wrap items-end gap-3 border-b border-border pb-4">
      <div className="min-w-0 flex-1">
        <h1 className="text-2xl font-bold">{title}</h1>
        {subtitle && (
          <p className="mt-1 max-w-[74ch] text-sm text-foreground-2">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function Card({
  title,
  actions,
  children,
  flush,
}: {
  title?: string;
  actions?: ReactNode;
  children: ReactNode;
  flush?: boolean;
}) {
  return (
    <section className="mb-4 overflow-hidden rounded-lg border border-border bg-panel shadow-[var(--shadow)]">
      {title && (
        <header className="flex flex-wrap items-center gap-2.5 border-b border-border bg-panel-2 px-4 py-2.5">
          <h2 className="text-[13.5px] font-semibold uppercase tracking-wide">
            {title}
          </h2>
          {actions && <div className="ml-auto flex flex-wrap gap-2">{actions}</div>}
        </header>
      )}
      <div className={flush ? "" : "p-4"}>{children}</div>
    </section>
  );
}

type Tone = "culture" | "vocational" | "ok" | "warn" | "error" | "muted";

const PILL: Record<Tone, string> = {
  culture: "bg-culture-bg text-culture border-culture",
  vocational: "bg-vocational-bg text-vocational border-vocational",
  ok: "bg-ok-bg text-ok border-ok",
  warn: "bg-warn-bg text-warn border-warn",
  error: "bg-destructive-bg text-destructive border-destructive",
  muted: "bg-head text-foreground-3 border-border-2",
};

export function Pill({
  tone = "muted",
  children,
}: {
  tone?: Tone;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full border px-2 py-[2px] text-[10.5px] font-semibold ${PILL[tone]}`}
    >
      {children}
    </span>
  );
}

export function Button({
  variant = "default",
  size = "md",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "primary" | "ghost";
  size?: "sm" | "md";
}) {
  const base =
    "inline-flex items-center gap-1.5 rounded-md border font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-culture";
  const sizes = { sm: "px-2.5 py-1 text-[11.5px]", md: "px-3.5 py-1.5 text-[12.5px]" };
  const variants = {
    default: "border-border-2 bg-panel text-foreground hover:border-vocational hover:text-vocational",
    primary: "border-vocational bg-vocational text-white hover:brightness-110",
    ghost: "border-transparent bg-transparent hover:bg-panel-2",
  };
  return (
    <button
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
      {...props}
    />
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[10.5px] uppercase tracking-wider text-foreground-3">
        {label}
      </span>
      {children}
    </label>
  );
}

export const inputClass =
  "rounded-md border border-border-2 bg-panel px-2.5 py-1.5 text-[12.5px] text-foreground focus:border-culture focus:outline-none";

export function Table({
  head,
  children,
}: {
  head: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-[13px]">
        <thead>
          <tr className="border-b border-border-2 bg-panel-2 text-left font-display text-[11.5px] uppercase tracking-wide text-foreground-3">
            {head}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Note({
  tone = "muted",
  icon,
  children,
}: {
  tone?: Tone;
  icon?: string;
  children: ReactNode;
}) {
  const map: Record<Tone, string> = {
    culture: "border-culture bg-culture-bg",
    vocational: "border-vocational bg-vocational-bg",
    ok: "border-ok bg-ok-bg",
    warn: "border-warn bg-warn-bg",
    error: "border-destructive bg-destructive-bg",
    muted: "border-border-2 bg-panel-2",
  };
  return (
    <div className={`mb-2.5 flex gap-2.5 rounded-md border p-3 last:mb-0 ${map[tone]}`}>
      {icon && (
        <span className="mt-[1px] flex-none font-mono text-[12px] font-bold">
          {icon}
        </span>
      )}
      <div className="min-w-0 flex-1 text-[13px] leading-relaxed">{children}</div>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <p className="px-1 py-6 text-center text-[13px] text-foreground-3">{children}</p>
  );
}

export function Stat({
  label,
  value,
  hint,
  tone = "muted",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: Tone;
}) {
  const bar: Record<Tone, string> = {
    culture: "border-t-culture",
    vocational: "border-t-vocational",
    ok: "border-t-ok",
    warn: "border-t-warn",
    error: "border-t-destructive",
    muted: "border-t-border-2",
  };
  return (
    <div
      className={`rounded-lg border border-border border-t-[3px] bg-panel px-3.5 py-3 shadow-[var(--shadow)] ${bar[tone]}`}
    >
      <div className="text-[10.5px] uppercase tracking-wider text-foreground-3">
        {label}
      </div>
      <div className="tabular font-display text-[27px] font-bold leading-tight">
        {value}
      </div>
      {hint && <div className="text-[11.5px] text-foreground-3">{hint}</div>}
    </div>
  );
}

"use client";

import { useMemo, useState } from "react";
import {
  constraintTemplates,
  entityGroups,
  periodOptions,
  seedConstraints,
  weekDays,
  type ConstraintMode,
  type ConstraintType,
  type CreatedConstraint,
} from "@/lib/mock/constraints";
import { rooms } from "@/lib/mock/schedule";
import { EntitySelect } from "./EntitySelect";

const paramLabelByKind = (param: string, kind: string): string => {
  switch (kind) {
    case "day":
      return weekDays.find((d) => d.code === param)?.label ?? param;
    case "period_range":
      return `Tiết ${param}`;
    case "resource":
      return param;
    case "quantity":
      return param;
    case "day_count":
      return `${param} ngày`;
    default:
      return param;
  }
};

export function ConstraintBuilder() {
  const [items, setItems] = useState<CreatedConstraint[]>(seedConstraints);
  const [type, setType] = useState<ConstraintType>("unavailability");
  const [entity, setEntity] = useState("");
  const [param, setParam] = useState("");
  const [mode, setMode] = useState<ConstraintMode>("hard");
  const [weight, setWeight] = useState(5);

  const template = useMemo(
    () => constraintTemplates.find((t) => t.type === type) ?? constraintTemplates[0],
    [type],
  );

  const entityLabel = useMemo(() => {
    for (const g of entityGroups) {
      const hit = g.options.find((o) => o.value === entity);
      if (hit) return hit.label;
    }
    return "";
  }, [entity]);

  const canCreate = entity.trim() !== "" && param.trim() !== "";

  function handleCreate() {
    if (!canCreate) return;
    const next: CreatedConstraint = {
      id: `C-${String(items.length + 1).padStart(3, "0")}`,
      type,
      typeLabel: template.label,
      entity: entityLabel || entity,
      param: paramLabelByKind(param, template.paramKind),
      mode,
      weight,
      status: "active",
      summary: buildSummary(template.label, entityLabel || entity, param, template.paramKind),
    };
    setItems((prev) => [next, ...prev]);
    setEntity("");
    setParam("");
    setWeight(5);
    setMode("hard");
  }

  function toggleStatus(id: string) {
    setItems((prev) =>
      prev.map((c) =>
        c.id === id
          ? { ...c, status: c.status === "active" ? "inactive" : "active" }
          : c,
      ),
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <section className="rounded-lg border border-border bg-sidebar p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-foreground/60">
          Tạo ràng buộc
        </h3>
        <div className="mt-4 flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase text-foreground/60">
              Loại ràng buộc
            </label>
            <select
              value={type}
              onChange={(e) => {
                setType(e.target.value as ConstraintType);
                setEntity("");
                setParam("");
              }}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
            >
              {constraintTemplates.map((t) => (
                <option key={t.type} value={t.type}>
                  {t.label} ({t.type})
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-foreground/60">{template.description}</p>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold uppercase text-foreground/60">
              {template.entityLabel}
            </label>
            <EntitySelect
              groups={entityGroupsFor(type)}
              value={entity}
              onChange={setEntity}
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold uppercase text-foreground/60">
              {template.paramLabel}
            </label>
            <ParamInput
              kind={template.paramKind}
              value={param}
              onChange={setParam}
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold uppercase text-foreground/60">
              Chế độ
            </label>
            <div className="flex overflow-hidden rounded-md border border-border w-fit">
              {(["hard", "soft"] as ConstraintMode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className={[
                    "px-4 py-1.5 text-sm font-semibold transition-colors",
                    mode === m
                      ? m === "hard"
                        ? "bg-destructive text-white"
                        : "bg-accent text-white"
                      : "bg-background text-foreground hover:bg-primary/10",
                  ].join(" ")}
                >
                  {m === "hard" ? "Hard" : "Soft"}
                </button>
              ))}
            </div>
          </div>

          {mode === "soft" && (
            <div>
              <label className="mb-1 flex items-center justify-between text-xs font-semibold uppercase text-foreground/60">
                <span>Trọng số</span>
                <span className="text-primary">{weight}</span>
              </label>
              <input
                type="range"
                min={1}
                max={10}
                step={1}
                value={weight}
                onChange={(e) => setWeight(Number(e.target.value))}
                className="w-full accent-primary"
              />
              <div className="mt-1 flex justify-between text-[10px] text-foreground/40">
                <span>1</span>
                <span>10</span>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleCreate}
            disabled={!canCreate}
            className="self-start rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Thêm ràng buộc
          </button>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-sidebar p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-foreground/60">
            Danh sách ràng buộc
          </h3>
          <span className="text-xs text-foreground/60">
            {items.filter((c) => c.status === "active").length} / {items.length} đang bật
          </span>
        </div>
        <ul className="mt-4 flex flex-col gap-2">
          {items.map((c) => (
            <li
              key={c.id}
              className="rounded-md border border-border bg-background p-3 shadow-sm"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                      {c.typeLabel}
                    </span>
                    <span
                      className={[
                        "rounded px-1.5 py-0.5 text-[10px] font-semibold",
                        c.mode === "hard"
                          ? "bg-destructive/10 text-destructive"
                          : "bg-accent/10 text-accent",
                      ].join(" ")}
                    >
                      {c.mode === "hard" ? "Hard" : `Soft w=${c.weight}`}
                    </span>
                    {c.status === "inactive" && (
                      <span className="rounded bg-foreground/10 px-1.5 py-0.5 text-[10px] font-semibold text-foreground/60">
                        Đang tắt
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm font-medium text-foreground">{c.summary}</p>
                  <p className="truncate text-xs text-foreground/60">
                    {c.entity} - {c.param}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => toggleStatus(c.id)}
                  aria-label="Bật/tắt ràng buộc"
                  className={[
                    "relative h-5 w-10 shrink-0 rounded-full transition-colors",
                    c.status === "active" ? "bg-accent" : "bg-foreground/20",
                  ].join(" ")}
                >
                  <span
                    className={[
                      "absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all",
                      c.status === "active" ? "left-5" : "left-0.5",
                    ].join(" ")}
                  />
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function entityGroupsFor(type: ConstraintType) {
  switch (type) {
    case "unavailability":
      return entityGroups;
    case "capacity_limit":
      return entityGroups.filter((g) => g.id === "room");
    case "quota_limit":
    case "preference":
      return entityGroups.filter((g) => g.id === "teacher");
    case "resource_requirement":
    case "adjacency":
    case "distribution":
      return entityGroups.filter((g) => g.id === "class");
    case "exclusion":
      return entityGroups;
    default:
      return entityGroups;
  }
}

function ParamInput({
  kind,
  value,
  onChange,
}: {
  kind: string;
  value: string;
  onChange: (v: string) => void;
}) {
  if (kind === "day") {
    return (
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
      >
        <option value="">Chọn ngày</option>
        {weekDays.map((d) => (
          <option key={d.code} value={d.code}>
            {d.label}
          </option>
        ))}
      </select>
    );
  }
  if (kind === "period_range") {
    return (
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
      >
        <option value="">Chọn tiết</option>
        {periodOptions.map((p) => (
          <option key={p.value} value={p.value}>
            {p.label}
          </option>
        ))}
      </select>
    );
  }
  if (kind === "resource") {
    return (
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
      >
        <option value="">Chọn tài nguyên</option>
        {rooms.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
    );
  }
  if (kind === "day_count") {
    return (
      <input
        type="number"
        min={1}
        max={6}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Số ngày"
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
      />
    );
  }
  return (
    <input
      type="number"
      min={1}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Nhập số lượng"
      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
    />
  );
}

function buildSummary(
  typeLabel: string,
  entityLabel: string,
  param: string,
  kind: string,
): string {
  const paramText = paramLabelByKind(param, kind);
  if (!entityLabel) return `${typeLabel}: ${paramText}`;
  return `${entityLabel}: ${typeLabel} - ${paramText}`;
}

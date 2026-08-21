"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { EntityGroup } from "@/lib/mock/constraints";

type Props = {
  groups: EntityGroup[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

export function EntitySelect({ groups, value, onChange, placeholder }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeGroup, setActiveGroup] = useState(groups[0]?.id ?? "");
  const rootRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const options = useMemo(() => {
    const group = groups.find((g) => g.id === activeGroup) ?? groups[0];
    if (!group) return [];
    const q = query.trim().toLowerCase();
    if (!q) return group.options;
    return group.options.filter(
      (o) =>
        o.value.toLowerCase().includes(q) || o.label.toLowerCase().includes(q),
    );
  }, [groups, activeGroup, query]);

  const selectedLabel = useMemo(() => {
    for (const g of groups) {
      const hit = g.options.find((o) => o.value === value);
      if (hit) return hit.label;
    }
    return "";
  }, [groups, value]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => {
          setOpen((o) => !o);
          if (!open) setTimeout(() => inputRef.current?.focus(), 0);
        }}
        className="flex w-full items-center justify-between rounded-md border border-border bg-background px-3 py-2 text-left text-sm text-foreground hover:border-primary/60 focus:outline-none focus:ring-2 focus:ring-primary/30"
      >
        <span className={selectedLabel ? "text-foreground" : "text-foreground/40"}>
          {selectedLabel || placeholder || "Chọn đối tượng"}
        </span>
        <span className="ml-2 text-xs text-foreground-3">&#9662;</span>
      </button>
      {open && (
        <div className="absolute z-30 mt-1 w-full rounded-md border border-border bg-panel shadow-lg">
          <div className="flex gap-1 border-b border-border p-2">
            {groups.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => {
                  setActiveGroup(g.id);
                  setQuery("");
                }}
                className={[
                  "rounded px-2 py-1 text-xs font-semibold transition-colors",
                  activeGroup === g.id
                    ? "bg-primary text-white"
                    : "bg-background text-foreground hover:bg-primary/10",
                ].join(" ")}
              >
                {g.label}
              </button>
            ))}
          </div>
          <div className="border-b border-border p-2">
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Tìm kiếm..."
              className="w-full rounded border border-border bg-background px-2 py-1.5 text-sm text-foreground focus:border-primary focus:outline-none"
            />
          </div>
          <ul className="max-h-52 overflow-auto">
            {options.length === 0 && (
              <li className="px-3 py-2 text-xs text-foreground-3">
                Không tìm thấy kết quả.
              </li>
            )}
            {options.map((o) => (
              <li key={o.value}>
                <button
                  type="button"
                  onClick={() => {
                    onChange(o.value);
                    setOpen(false);
                    setQuery("");
                  }}
                  className={[
                    "block w-full px-3 py-2 text-left text-sm hover:bg-primary/10",
                    o.value === value ? "bg-primary/5 font-semibold text-primary" : "text-foreground",
                  ].join(" ")}
                >
                  {o.label}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

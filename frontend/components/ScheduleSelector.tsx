"use client";

import { useAuth } from "@/components/providers/AuthProvider";
import { createApiClient } from "@/lib/api";
import { useEffect, useMemo, useState } from "react";
import type { ScheduleSummary } from "@/lib/api";

type Props = {
  value: number | null;
  onChange: (id: number | null) => void;
};

export function ScheduleSelector({ value, onChange }: Props) {
  const { token } = useAuth();
  const [schedules, setSchedules] = useState<ScheduleSummary[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setSchedules([]);
      return;
    }
    const api = createApiClient(token);
    api
      .listSchedules()
      .then((list) => {
        setSchedules(list);
        if (value === null && list.length > 0) onChange(list[0].id);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Lỗi tải lịch"));
  }, [token]);

  const api = useMemo(() => createApiClient(token), [token]);

  async function handleCreate() {
    const name = window.prompt("Tên lịch mới:", "Lịch học kỳ");
    if (!name) return;
    setCreating(true);
    setError(null);
    try {
      const created = await api.createSchedule(name);
      const list = await api.listSchedules();
      setSchedules(list);
      onChange(created.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không tạo được lịch");
    } finally {
      setCreating(false);
    }
  }

  if (!token) {
    return (
      <p className="text-xs text-foreground/60">
        Cần đăng nhập (JWT) để xem lịch. Dán token vào ô bên dưới.
      </p>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <select
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:border-primary focus:outline-none"
      >
        <option value="">-- Chọn lịch --</option>
        {schedules.map((s) => (
          <option key={s.id} value={s.id}>
            #{s.id} {s.name} ({s.status})
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={handleCreate}
        disabled={creating}
        className="rounded-md border border-border bg-background px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-primary/10 disabled:opacity-50"
      >
        {creating ? "Đang tạo..." : "+ Tạo lịch"}
      </button>
      {error && (
        <span className="text-xs font-medium text-destructive">{error}</span>
      )}
    </div>
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import {
  createApiClient,
  type HorizonConfig,
  type HorizonInput,
} from "@/lib/api";

type Props = {
  onChange?: () => void;
};

const FIELDS: {
  key: keyof HorizonInput;
  label: string;
  hint: string;
  min: number;
  max: number;
}[] = [
  {
    key: "days_per_week",
    label: "Số ngày học mỗi tuần",
    hint: "Tính từ thứ 2. Chọn 6 nếu học cả thứ 7.",
    min: 1,
    max: 7,
  },
  {
    key: "periods_per_day",
    label: "Số tiết mỗi ngày",
    hint: "Học cả sáng lẫn chiều thì cộng cả hai buổi, ví dụ 5 + 5 = 10.",
    min: 1,
    max: 16,
  },
  {
    key: "morning_count",
    label: "Số tiết buổi sáng",
    hint: "Dùng để phân biệt buổi sáng và buổi chiều khi xếp lịch.",
    min: 0,
    max: 16,
  },
  {
    key: "weeks",
    label: "Số tuần",
    hint: "Để 1 nếu thời khoá biểu lặp lại hằng tuần.",
    min: 1,
    max: 8,
  },
];

function toInput(config: HorizonConfig): Required<HorizonInput> {
  return {
    weeks: config.weeks,
    days_per_week: config.days_per_week,
    periods_per_day: config.periods_per_day,
    morning_count: config.morning_count,
  };
}

export function HorizonSettings({ onChange }: Props) {
  const { token } = useAuth();
  const api = createApiClient(token);
  const [config, setConfig] = useState<HorizonConfig | null>(null);
  const [draft, setDraft] = useState<Required<HorizonInput> | null>(null);
  const [isDefault, setIsDefault] = useState(true);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    if (!token) {
      setConfig(null);
      setDraft(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.getHorizon();
      setConfig(res.horizon);
      setDraft(toInput(res.horizon));
      setIsDefault(res.is_default);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải cấu hình");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const dirty =
    draft && config
      ? FIELDS.some((f) => draft[f.key] !== toInput(config)[f.key])
      : false;

  const previewSlots = draft
    ? draft.weeks * draft.days_per_week * draft.periods_per_day
    : 0;

  async function handleSave() {
    if (!draft) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const next = await api.putHorizon(draft);
      setConfig(next);
      setDraft(toInput(next));
      setIsDefault(false);
      setSaved(true);
      onChange?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi lưu cấu hình");
    } finally {
      setSaving(false);
    }
  }

  if (!token) return null;
  if (loading) {
    return (
      <p className="text-sm text-foreground/60">Đang tải cấu hình thời khoá biểu...</p>
    );
  }
  if (!draft || !config) return null;

  return (
    <section className="rounded-lg border border-border bg-sidebar p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-foreground/60">
            Khung thời khoá biểu
          </h3>
          <p className="mt-1 text-xs text-foreground/60">
            Số tiết khả dụng mỗi tuần. Mỗi lớp và mỗi giáo viên không thể vượt
            quá con số này.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isDefault && (
            <span className="rounded bg-border/60 px-2 py-0.5 text-xs font-semibold text-foreground/70">
              Đang dùng mặc định
            </span>
          )}
          {saved && !dirty && (
            <span className="rounded bg-accent/15 px-2 py-0.5 text-xs font-semibold text-accent">
              Đã lưu
            </span>
          )}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {FIELDS.map((field) => (
          <div key={field.key}>
            <label className="mb-1 block text-xs font-semibold uppercase text-foreground/60">
              {field.label}
            </label>
            <input
              type="number"
              min={field.min}
              max={field.max}
              value={draft[field.key]}
              onChange={(e) =>
                setDraft({ ...draft, [field.key]: Number(e.target.value) })
              }
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
            />
            <p className="mt-1 text-[11px] text-foreground/50">{field.hint}</p>
          </div>
        ))}
      </div>

      <p className="mt-4 text-sm text-foreground/70">
        Tổng cộng{" "}
        <span className="font-bold text-primary">{previewSlots} tiết</span> mỗi
        tuần
        {dirty && (
          <span className="text-foreground/50">
            {" "}
            (đang là {config.total_slots} tiết)
          </span>
        )}
        .
      </p>

      <div className="mt-3 flex items-center gap-2">
        <button
          type="button"
          onClick={handleSave}
          disabled={!dirty || saving}
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {saving ? "Đang lưu..." : "Lưu khung giờ"}
        </button>
        {dirty && (
          <button
            type="button"
            onClick={() => setDraft(toInput(config))}
            className="rounded-md border border-border px-4 py-2 text-sm font-semibold text-foreground hover:bg-primary/10"
          >
            Hoàn tác
          </button>
        )}
        {error && (
          <span className="text-xs font-medium text-destructive">{error}</span>
        )}
      </div>
    </section>
  );
}

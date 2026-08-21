"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { createApiClient, type Weights } from "@/lib/api";

type Props = {
  scheduleId: number | null;
};

const WEIGHT_LABELS: { key: keyof Weights; label: string; hint: string }[] = [
  {
    key: "idle_teacher",
    label: "Trống giờ giáo viên",
    hint: "Phạt khi giáo viên có khoảng trống giữa các tiết.",
  },
  {
    key: "room_change",
    label: "Đổi phòng",
    hint: "Phạt khi một lớp đổi phòng nhiều trong ngày.",
  },
  {
    key: "compact_schedule",
    label: "Đặc lịch",
    hint: "Phạt khi lịch rải quá nhiều ngày.",
  },
  {
    key: "teacher_load_balance",
    label: "Cân bằng tải giáo viên",
    hint: "Phạt khi phân bổ tiết không đều giữa các ngày.",
  },
];

export function ConstraintBuilder({ scheduleId }: Props) {
  const { token } = useAuth();
  const api = createApiClient(token);
  const [weights, setWeights] = useState<Weights | null>(null);
  const [draft, setDraft] = useState<Weights | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    if (!token || scheduleId === null) {
      setWeights(null);
      setDraft(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const w = await api.getWeights(scheduleId);
      setWeights(w);
      setDraft(w);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải trọng số");
    } finally {
      setLoading(false);
    }
  }, [token, scheduleId]);

  useEffect(() => {
    load();
  }, [load]);

  const dirty =
    draft && weights ? !shallowEqual(draft, weights) : false;

  async function handleSave() {
    if (!draft || scheduleId === null) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const w = await api.putWeights(scheduleId, draft);
      setWeights(w);
      setDraft(w);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi lưu trọng số");
    } finally {
      setSaving(false);
    }
  }

  if (!token) {
    return (
      <p className="text-sm text-foreground-2">
        Cần dán JWT token để chỉnh trọng số.
      </p>
    );
  }

  if (scheduleId === null) {
    return (
      <p className="text-sm text-foreground-2">
        Chọn một lịch để cấu hình trọng số.
      </p>
    );
  }

  if (loading) {
    return <p className="text-sm text-foreground-2">Đang tải trọng số...</p>;
  }

  if (!draft) return null;

  return (
    <section className="rounded-lg border border-border bg-panel p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-foreground-2">
          Trọng số mục tiêu
        </h3>
        {saved && !dirty && (
          <span className="rounded bg-accent/15 px-2 py-0.5 text-xs font-semibold text-accent">
            Đã lưu
          </span>
        )}
      </div>
      <div className="mt-4 flex flex-col gap-4">
        {WEIGHT_LABELS.map((item) => (
          <div key={item.key}>
            <label className="mb-1 flex items-center justify-between text-xs font-semibold uppercase text-foreground-2">
              <span>{item.label}</span>
              <span className="text-primary">{draft[item.key]}</span>
            </label>
            <input
              type="range"
              min={0}
              max={10}
              step={1}
              value={draft[item.key]}
              onChange={(e) =>
                setDraft({ ...draft, [item.key]: Number(e.target.value) })
              }
              className="w-full accent-primary"
            />
            <p className="mt-1 text-[11px] text-foreground-3">{item.hint}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-2">
        <button
          type="button"
          onClick={handleSave}
          disabled={!dirty || saving}
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {saving ? "Đang lưu..." : "Lưu trọng số"}
        </button>
        {dirty && (
            <button
              type="button"
              onClick={() => setDraft(weights)}
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

function shallowEqual(a: Weights, b: Weights): boolean {
  return (
    a.idle_teacher === b.idle_teacher &&
    a.room_change === b.room_change &&
    a.compact_schedule === b.compact_schedule &&
    a.teacher_load_balance === b.teacher_load_balance
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Card,
  Empty,
  Note,
  PageHeader,
  Pill,
  Stat,
  inputClass,
} from "@/components/ui";
import { useV2 } from "@/lib/useV2";
import type { MySchedule, MySession, MyWorkload } from "@/lib/api-v2";

const DAY_LABEL = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"];

const TYPE_LABEL: Record<string, string> = {
  theory: "Lý thuyết",
  practice: "Thực hành",
  internship: "Thực tập",
  exam: "Kiểm tra",
};

function typeTone(t: string): "culture" | "vocational" | "muted" {
  if (t === "practice") return "vocational";
  if (t === "theory") return "culture";
  return "muted";
}

/** Một buổi học. Dạng thẻ để đọc được trên điện thoại (NFR-10). */
function SessionCard({ s }: { s: MySession }) {
  const tiet =
    s.duration_slots > 1
      ? "Tiết " + (s.period + 1) + "–" + (s.period + s.duration_slots)
      : "Tiết " + (s.period + 1);
  return (
    <div className="rounded-md border border-border-2 bg-panel px-3 py-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-display text-[12px] font-semibold text-foreground-2">
          {tiet}
        </span>
        <Pill tone={s.shift === "morning" ? "culture" : "vocational"}>
          {s.shift === "morning" ? "Sáng" : "Chiều"}
        </Pill>
        <Pill tone={typeTone(s.session_type)}>
          {TYPE_LABEL[s.session_type] ?? s.session_type}
        </Pill>
        {s.location && s.location !== "on_campus" && (
          <Pill tone="warn">Ngoài trường</Pill>
        )}
      </div>
      <p className="mt-1 text-[13.5px] font-semibold">{s.module_name}</p>
      <p className="mt-0.5 text-[12px] text-foreground-2">
        {s.group_code}
        {s.room ? " · " + s.room : ""}
        {s.teachers.length ? " · " + s.teachers.join(", ") : ""}
      </p>
    </div>
  );
}

export default function LichCuaToiPage() {
  const { api } = useV2();
  const [data, setData] = useState<MySchedule | null>(null);
  const [workload, setWorkload] = useState<MyWorkload | null>(null);
  const [group, setGroup] = useState("");
  const [groupInput, setGroupInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!api) return;
    setLoading(true);
    setError(null);
    try {
      const r = await api.mySchedule(group ? { group } : undefined);
      setData(r);
      if (r.role === "teacher" && r.teacher_code) {
        try {
          setWorkload(await api.myWorkload());
        } catch {
          // Chưa gắn hồ sơ giáo viên thì bỏ qua, lịch vẫn hiện.
          setWorkload(null);
        }
      } else {
        setWorkload(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải lịch cá nhân");
    } finally {
      setLoading(false);
    }
  }, [api, group]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!api) return <Empty>Cần đăng nhập để xem lịch của bạn.</Empty>;

  const sessions = data?.sessions ?? [];
  const byDay = new Map<number, MySession[]>();
  for (const s of sessions) {
    const list = byDay.get(s.day) ?? [];
    list.push(s);
    byDay.set(s.day, list);
  }
  const days = [...byDay.keys()].sort((a, b) => a - b);
  const tongTiet = sessions.reduce((n, s) => n + s.duration_slots, 0);
  const laSinhVien = data?.role === "student";

  return (
    <>
      <PageHeader
        title="Lịch của tôi"
        subtitle={
          data
            ? data.schedule_name
              ? data.schedule_name +
                (data.published ? " · đã xuất bản" : " · bản nháp")
              : "Chưa có lịch nào được xuất bản"
            : "Đang tải..."
        }
      />

      {error && <Note tone="error">{error}</Note>}
      {data?.detail && <Note tone="warn">{data.detail}</Note>}

      {laSinhVien && (
        <Card title="Chọn nhóm nghề">
          <div className="flex flex-wrap items-end gap-2">
            <input
              className={inputClass}
              placeholder="Nhập mã nhóm, ví dụ 11A3"
              value={groupInput}
              onChange={(e) => setGroupInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") setGroup(groupInput.trim());
              }}
            />
            <button
              type="button"
              onClick={() => setGroup(groupInput.trim())}
              className="rounded-md border border-vocational bg-vocational px-3.5 py-1.5 text-[12.5px] font-semibold text-white hover:brightness-110"
            >
              Xem lịch
            </button>
          </div>
        </Card>
      )}

      {sessions.length > 0 && (
        <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Số buổi" value={sessions.length} tone="culture" />
          <Stat label="Tổng tiết" value={tongTiet} tone="culture" />
          {workload && (
            <>
              <Stat
                label="Giờ chuẩn"
                value={workload.standard_hours}
                tone="vocational"
                hint={"Định mức " + workload.quota}
              />
              <Stat
                label="Đạt định mức"
                value={workload.usage_pct + "%"}
                tone={workload.usage_pct > 100 ? "warn" : "ok"}
              />
            </>
          )}
        </div>
      )}

      {loading ? (
        <Empty>Đang tải...</Empty>
      ) : sessions.length === 0 ? (
        <Empty>
          {laSinhVien && !group
            ? "Nhập mã nhóm nghề để xem lịch."
            : "Chưa có buổi học nào trong lịch này."}
        </Empty>
      ) : (
        days.map((d) => (
          <Card key={d} title={DAY_LABEL[d] ?? "Ngày " + d}>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {(byDay.get(d) ?? []).map((s) => (
                <SessionCard key={s.session_id} s={s} />
              ))}
            </div>
          </Card>
        ))
      )}
    </>
  );
}

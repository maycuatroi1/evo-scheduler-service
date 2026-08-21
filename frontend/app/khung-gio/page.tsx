"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  Field,
  Empty,
  Note,
  PageHeader,
  Table,
  inputClass,
} from "@/components/ui";
import type { BellPeriod } from "@/lib/api-v2";
import { useV2 } from "@/lib/useV2";

type Cfg = {
  morning_start: string;
  afternoon_start: string;
  period_minutes: number;
  break_minutes: number;
  long_break_after: number;
  long_break_minutes: number;
  periods_per_shift: number;
};

const DEFAULTS: Cfg = {
  morning_start: "07:00",
  afternoon_start: "13:00",
  period_minutes: 45,
  break_minutes: 5,
  long_break_after: 2,
  long_break_minutes: 15,
  periods_per_shift: 5,
};

export default function KhungGioPage() {
  const { api } = useV2();
  const [cfg, setCfg] = useState<Cfg>(DEFAULTS);
  const [periods, setPeriods] = useState<{
    morning: BellPeriod[];
    afternoon: BellPeriod[];
  }>({ morning: [], afternoon: [] });
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!api) return;
    try {
      const r = await api.getBellTimes();
      setCfg({ ...DEFAULTS, ...(r.config as Partial<Cfg>) });
      setPeriods(r.periods);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải mốc giờ");
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  async function save(next: Cfg) {
    if (!api) return;
    setBusy(true);
    setError(null);
    try {
      const r = await api.setBellTimes(next as unknown as Record<string, unknown>);
      setPeriods(r.periods);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi lưu mốc giờ");
    } finally {
      setBusy(false);
    }
  }

  const set = (k: keyof Cfg, v: string | number) =>
    setCfg((p) => ({ ...p, [k]: v }));

  // Chào cờ 7h25 thứ Hai — mốc duy nhất trường đã công bố
  const t1 = periods.morning[0];
  const covers725 = t1 && t1.start <= "07:25" && t1.end >= "07:25";

  if (!api) return <Empty>Cần đăng nhập để cấu hình khung giờ.</Empty>;

  return (
    <>
      <PageHeader
        title="Khung giờ & mốc giờ"
        subtitle="Giờ bắt đầu và kết thúc từng tiết, dùng để in lên bản thời khoá biểu và tính ràng buộc di chuyển giữa các cơ sở."
        actions={
          <>
            <Button onClick={() => void save(DEFAULTS)} disabled={busy}>
              Mặc định
            </Button>
            <Button variant="primary" onClick={() => void save(cfg)} disabled={busy}>
              {busy ? "Đang lưu…" : "Lưu mốc giờ"}
            </Button>
          </>
        }
      />

      {error && (
        <Note tone="error" icon="✕">
          {error}
        </Note>
      )}
      {saved && (
        <Note tone="ok" icon="✓">
          Đã lưu mốc giờ.
        </Note>
      )}

      <Card title="Tham số sinh mốc giờ">
        <div className="flex flex-wrap gap-3">
          <Field label="Tiết đầu buổi sáng">
            <input
              className={inputClass + " w-28"}
              value={cfg.morning_start}
              onChange={(e) => set("morning_start", e.target.value)}
              placeholder="07:00"
            />
          </Field>
          <Field label="Tiết đầu buổi chiều">
            <input
              className={inputClass + " w-28"}
              value={cfg.afternoon_start}
              onChange={(e) => set("afternoon_start", e.target.value)}
              placeholder="13:00"
            />
          </Field>
          <Field label="Độ dài tiết (phút)">
            <input
              type="number"
              className={inputClass + " w-24"}
              value={cfg.period_minutes}
              onChange={(e) => set("period_minutes", Number(e.target.value))}
            />
          </Field>
          <Field label="Nghỉ giữa tiết (phút)">
            <input
              type="number"
              className={inputClass + " w-24"}
              value={cfg.break_minutes}
              onChange={(e) => set("break_minutes", Number(e.target.value))}
            />
          </Field>
          <Field label="Nghỉ dài sau tiết">
            <input
              type="number"
              className={inputClass + " w-24"}
              value={cfg.long_break_after}
              onChange={(e) => set("long_break_after", Number(e.target.value))}
            />
          </Field>
          <Field label="Dài nghỉ giữa buổi (phút)">
            <input
              type="number"
              className={inputClass + " w-28"}
              value={cfg.long_break_minutes}
              onChange={(e) => set("long_break_minutes", Number(e.target.value))}
            />
          </Field>
        </div>

        {t1 && (
          <Note tone={covers725 ? "ok" : "warn"} icon={covers725 ? "✓" : "!"}>
            {covers725 ? (
              <>
                Chào cờ thứ Hai <b>7h25</b> nằm trong tiết 1 ({t1.start}–{t1.end})
                — khớp với thời khoá biểu trường đang phát hành.
              </>
            ) : (
              <>
                Chào cờ thứ Hai <b>7h25</b> không nằm trong tiết 1 ({t1.start}–
                {t1.end}). Kiểm tra lại giờ tiết đầu buổi sáng.
              </>
            )}
          </Note>
        )}
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {(
          [
            ["Buổi sáng", periods.morning],
            ["Buổi chiều", periods.afternoon],
          ] as [string, BellPeriod[]][]
        ).map(([label, rows]) => (
          <Card key={label} title={label} flush>
            <Table
              head={
                <>
                  <th className="w-16 px-3 py-2 text-right">Tiết</th>
                  <th className="px-3 py-2">Bắt đầu</th>
                  <th className="px-3 py-2">Kết thúc</th>
                </>
              }
            >
              {rows.length === 0 && (
                <tr>
                  <td colSpan={3}>
                    <Empty>Chưa sinh mốc giờ.</Empty>
                  </td>
                </tr>
              )}
              {rows.map((p) => (
                <tr key={p.period} className="border-b border-border last:border-0">
                  <td className="tabular px-3 py-2 text-right font-mono">
                    {p.period}
                  </td>
                  <td className="tabular px-3 py-2 font-mono">{p.start}</td>
                  <td className="tabular px-3 py-2 font-mono">{p.end}</td>
                </tr>
              ))}
            </Table>
          </Card>
        ))}
      </div>

      <Card title="Ca học văn hoá theo khối">
        <Note tone="muted" icon="§">
          Trường cố định ca theo khối: <b>khối 10 học sáng</b>,{" "}
          <b>khối 11 học chiều</b>, <b>khối 12 học cả ngày</b>. Ca học nghề là
          phần bù, hệ thống tự suy ra — không cần khai riêng.
          <div className="mt-1.5 border-t border-dashed border-current pt-1.5 text-[12px] opacity-90">
            Khối 10 và 12 cùng học văn hoá buổi sáng nên cùng dồn về xưởng buổi
            chiều. Đây là điểm nghẽn tài nguyên nặng nhất trong tuần.
          </div>
        </Note>
      </Card>
    </>
  );
}

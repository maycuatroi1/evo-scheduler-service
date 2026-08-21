"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  Empty,
  Field,
  Note,
  PageHeader,
  Pill,
  Stat,
  Table,
  inputClass,
} from "@/components/ui";
import { useV2 } from "@/lib/useV2";
import type {
  SwapCandidate,
  TrayItem,
  Verdict,
  Version,
} from "@/lib/api-v2";

const DAY_LABEL = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"];

/* Bảng màu bắt buộc khi tinh chỉnh (SRS §7.5). Hồng đậm là chặn hẳn. */
const VERDICT_INFO: Record<
  Verdict,
  { label: string; tone: "ok" | "warn" | "error" | "muted"; swatch: string }
> = {
  green: { label: "Đổi được", tone: "ok", swatch: "bg-ok" },
  orange: {
    label: "Vi phạm hạn chế xếp",
    tone: "warn",
    swatch: "bg-warn",
  },
  pink: { label: "Vi phạm ràng buộc", tone: "warn", swatch: "bg-warn/50" },
  pink_dark: {
    label: "Trùng tiết — không đổi được",
    tone: "error",
    swatch: "bg-destructive",
  },
};

export default function TinhChinhPage() {
  const { api } = useV2();
  const [versions, setVersions] = useState<Version[]>([]);
  const [scheduleId, setScheduleId] = useState<number | null>(null);
  const [tray, setTray] = useState<TrayItem[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [scope, setScope] = useState<"group" | "all">("group");
  const [cands, setCands] = useState<SwapCandidate[]>([]);
  const [target, setTarget] = useState<number | null>(null);
  const [placeDay, setPlaceDay] = useState(0);
  const [placePeriod, setPlacePeriod] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const loadVersions = useCallback(async () => {
    if (!api) return;
    try {
      const r = await api.versions();
      setVersions(r.versions);
      if (r.versions.length && scheduleId === null)
        setScheduleId(r.versions[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải danh sách lịch");
    }
  }, [api, scheduleId]);

  const loadTray = useCallback(async () => {
    if (!api || scheduleId === null) return;
    try {
      const r = await api.listTray(scheduleId);
      setTray(r.tray);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải khay tiết chờ");
    }
  }, [api, scheduleId]);

  useEffect(() => {
    void loadVersions();
  }, [loadVersions]);

  useEffect(() => {
    void loadTray();
  }, [loadTray]);

  async function findCandidates() {
    if (!api || scheduleId === null) return;
    const sid = Number(sessionId);
    if (!sid) {
      setError("Nhập mã buổi học cần đổi.");
      return;
    }
    setBusy(true);
    setError(null);
    setOk(null);
    try {
      const r = await api.swapCandidates(scheduleId, sid, scope);
      setCands(r.candidates);
      setTarget(sid);
      if (r.candidates.length === 0)
        setOk("Không tìm thấy buổi nào để đổi trong phạm vi này.");
    } catch (e) {
      setCands([]);
      setError(e instanceof Error ? e.message : "Lỗi tìm ô đổi được");
    } finally {
      setBusy(false);
    }
  }

  async function doSwap(other: SwapCandidate) {
    if (!api || scheduleId === null || target === null) return;
    setBusy(true);
    setError(null);
    setOk(null);
    try {
      const r = await api.swapSessions(scheduleId, target, other.session_id);
      setOk(
        r.warnings.length
          ? "Đã đổi, nhưng lưu ý: " + r.warnings.join("; ")
          : "Đã đổi chỗ hai buổi.",
      );
      await findCandidates();
      await loadTray();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không đổi được");
    } finally {
      setBusy(false);
    }
  }

  async function pushToTray() {
    if (!api || scheduleId === null) return;
    const sid = Number(sessionId);
    if (!sid) {
      setError("Nhập mã buổi học cần gỡ.");
      return;
    }
    setBusy(true);
    setError(null);
    setOk(null);
    try {
      await api.pushToTray(scheduleId, sid);
      setOk("Đã gỡ buổi " + sid + " vào khay chờ.");
      setCands([]);
      await loadTray();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không gỡ được buổi này");
    } finally {
      setBusy(false);
    }
  }

  async function place(item: TrayItem) {
    if (!api || scheduleId === null) return;
    setBusy(true);
    setError(null);
    setOk(null);
    try {
      const r = await api.placeFromTray(
        scheduleId,
        item.session_id,
        placeDay,
        placePeriod,
      );
      setOk(
        r.warning
          ? "Đã xếp, nhưng lưu ý: " + r.warning
          : "Đã xếp " + item.module_code + " vào ô đã chọn.",
      );
      await loadTray();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không xếp được vào ô này");
    } finally {
      setBusy(false);
    }
  }

  if (!api) return <Empty>Cần đăng nhập để tinh chỉnh thời khoá biểu.</Empty>;

  const list = cands;
  const xanh = list.filter((c) => c.verdict === "green").length;

  return (
    <>
      <PageHeader
        title="Tinh chỉnh thủ công"
        subtitle="Xếp tự động không thay hết được con người. Chọn một buổi, hệ thống tô màu những chỗ đổi được; hoặc gỡ buổi ra khay chờ rồi tự xếp vào ô mong muốn."
      />

      {error && <Note tone="error">{error}</Note>}
      {ok && <Note tone="ok">{ok}</Note>}

      <Card title="Chọn lịch và buổi học">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Lịch">
            <select
              className={inputClass}
              value={scheduleId ?? ""}
              onChange={(e) => {
                setScheduleId(Number(e.target.value));
                setCands([]);
                setTarget(null);
              }}
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Mã buổi học">
            <input
              className={inputClass}
              placeholder="ví dụ 128"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
            />
          </Field>
          <Field label="Phạm vi tìm">
            <select
              className={inputClass}
              value={scope}
              onChange={(e) => setScope(e.target.value as "group" | "all")}
            >
              <option value="group">Cùng nhóm nghề (cách 1)</option>
              <option value="all">Toàn trường (cách 3)</option>
            </select>
          </Field>
          <div className="flex items-end gap-2">
            <Button variant="primary" onClick={findCandidates} disabled={busy}>
              Tìm ô đổi được
            </Button>
            <Button onClick={pushToTray} disabled={busy}>
              Gỡ vào khay
            </Button>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-3 text-[11.5px] text-foreground-2">
          {(Object.keys(VERDICT_INFO) as Verdict[]).map((v) => (
            <span key={v} className="flex items-center gap-1.5">
              <span
                className={
                  "inline-block h-3 w-3 rounded-sm " + VERDICT_INFO[v].swatch
                }
              />
              {VERDICT_INFO[v].label}
            </span>
          ))}
        </div>
      </Card>

      {list.length > 0 && (
        <>
          <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
            <Stat label="Ô xét được" value={list.length} tone="culture" />
            <Stat
              label="Đổi được ngay"
              value={xanh}
              tone={xanh ? "ok" : "warn"}
            />
            <Stat
              label="Bị chặn"
              value={list.filter((c) => c.verdict === "pink_dark").length}
              tone="muted"
            />
          </div>

          <Card title={"Ô đổi được với buổi " + target} flush>
            <Table
              head={
                <>
                  <th className="px-3 py-2">Vị trí</th>
                  <th className="px-3 py-2">Mô-đun</th>
                  <th className="px-3 py-2">Nhóm</th>
                  <th className="px-3 py-2">Giáo viên</th>
                  <th className="px-3 py-2">Phòng</th>
                  <th className="px-3 py-2">Đánh giá</th>
                  <th className="px-3 py-2"></th>
                </>
              }
            >
              {list.map((c) => (
                <tr key={c.session_id} className="border-b border-border-2">
                  <td className="px-3 py-2 whitespace-nowrap">
                    {(DAY_LABEL[c.day] ?? "Ngày " + c.day) +
                      " · tiết " +
                      (c.period + 1) +
                      (c.duration_slots > 1
                        ? "–" + (c.period + c.duration_slots)
                        : "")}
                  </td>
                  <td className="px-3 py-2">{c.module_code}</td>
                  <td className="px-3 py-2">{c.group_code}</td>
                  <td className="px-3 py-2">{c.teachers.join(", ")}</td>
                  <td className="px-3 py-2">{c.room}</td>
                  <td className="px-3 py-2">
                    <Pill tone={VERDICT_INFO[c.verdict].tone}>
                      {VERDICT_INFO[c.verdict].label}
                    </Pill>
                    <p className="mt-0.5 text-[10.5px] text-foreground-3">
                      {c.reason}
                    </p>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Button
                      size="sm"
                      disabled={busy || c.verdict === "pink_dark"}
                      onClick={() => doSwap(c)}
                    >
                      Đổi
                    </Button>
                  </td>
                </tr>
              ))}
            </Table>
          </Card>
        </>
      )}

      <Card
        title={"Khay tiết chờ xếp (" + tray.length + ")"}
        actions={
          <div className="flex flex-wrap items-end gap-2">
            <Field label="Ngày">
              <select
                className={inputClass}
                value={placeDay}
                onChange={(e) => setPlaceDay(Number(e.target.value))}
              >
                {DAY_LABEL.slice(0, 6).map((d, i) => (
                  <option key={d} value={i}>
                    {d}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Tiết bắt đầu">
              <select
                className={inputClass}
                value={placePeriod}
                onChange={(e) => setPlacePeriod(Number(e.target.value))}
              >
                {[0, 1, 2, 3, 4].map((p) => (
                  <option key={p} value={p}>
                    Tiết {p + 1}
                  </option>
                ))}
              </select>
            </Field>
          </div>
        }
        flush
      >
        {tray.length === 0 ? (
          <Empty>Khay trống — mọi buổi đều đã có tiết.</Empty>
        ) : (
          <Table
            head={
              <>
                <th className="px-3 py-2">Mô-đun</th>
                <th className="px-3 py-2">Nhóm</th>
                <th className="px-3 py-2 text-right">Số tiết</th>
                <th className="px-3 py-2">Giáo viên</th>
                <th className="px-3 py-2">Phòng</th>
                <th className="px-3 py-2"></th>
              </>
            }
          >
            {tray.map((t) => (
              <tr key={t.session_id} className="border-b border-border-2">
                <td className="px-3 py-2">
                  <span className="font-semibold">{t.module_code}</span>{" "}
                  <span className="text-foreground-2">{t.module_name}</span>
                </td>
                <td className="px-3 py-2">{t.group_code}</td>
                <td className="px-3 py-2 text-right">{t.duration_slots}</td>
                <td className="px-3 py-2">{t.teachers.join(", ")}</td>
                <td className="px-3 py-2">{t.room}</td>
                <td className="px-3 py-2 text-right">
                  <Button size="sm" disabled={busy} onClick={() => place(t)}>
                    Xếp vào ô đã chọn
                  </Button>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  );
}

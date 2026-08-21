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
import type { Campus, Resource, RoomUsage } from "@/lib/api-v2";

const TYPE_LABEL: Record<string, string> = {
  theory_room: "Phòng lý thuyết",
  workshop: "Xưởng",
  tool_set: "Bộ dụng cụ",
};

export default function PhongPage() {
  const { api } = useV2();
  const [rooms, setRooms] = useState<Resource[]>([]);
  const [usage, setUsage] = useState<RoomUsage[]>([]);
  const [campuses, setCampuses] = useState<Campus[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Resource | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    if (!api) return;
    setLoading(true);
    setError(null);
    try {
      const [r, u, c] = await Promise.all([
        api.listResources(),
        api.roomUsage(),
        api.listCampuses(),
      ]);
      setRooms(r);
      setUsage(u.rooms);
      setCampuses(c);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải dữ liệu phòng");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  const byCode = new Map(usage.map((u) => [u.code, u]));
  const visible = filter === "all" ? rooms : rooms.filter((r) => r.type === filter);
  const workshops = rooms.filter((r) => r.type === "workshop");
  const totalUnits = rooms.reduce((n, r) => n + (r.quantity || 1), 0);
  const busiest = usage.filter((u) => u.usage_pct >= 85);

  if (!api) return <Empty>Cần đăng nhập để xem danh sách phòng.</Empty>;

  return (
    <>
      <PageHeader
        title="Phòng & xưởng"
        subtitle="Phòng lý thuyết dùng chung giữa khối văn hoá và khối nghề. Xưởng là tài nguyên khan hiếm nhất, quyết định thứ tự xếp lịch."
        actions={
          <>
            <Button onClick={() => void load()} disabled={loading}>
              {loading ? "Đang tải…" : "↻ Tải lại"}
            </Button>
            <Button variant="primary" onClick={() => setCreating(true)}>
              + Thêm phòng
            </Button>
          </>
        }
      />

      {error && (
        <Note tone="error" icon="✕">
          {error}
        </Note>
      )}

      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Đầu mục phòng" value={rooms.length} hint={`${totalUnits} phòng thực`} />
        <Stat label="Xưởng" value={workshops.length} tone="vocational" />
        <Stat label="Cơ sở đào tạo" value={campuses.length} tone="culture" />
        <Stat
          label="Gần kín lịch"
          value={busiest.length}
          hint="dùng trên 85%"
          tone={busiest.length ? "warn" : "ok"}
        />
      </div>

      {busiest.length > 0 && (
        <Card title="Phòng gần kín lịch">
          {busiest.slice(0, 5).map((u) => (
            <Note key={u.code} tone="warn" icon="!">
              <b>{u.name}</b> ({u.code}) — dùng {u.periods_used}/{u.slots_available}{" "}
              tiết, <b>{u.usage_pct}%</b>. Còn rất ít chỗ để xếp thêm.
            </Note>
          ))}
        </Card>
      )}

      <Card
        title="Danh sách phòng"
        flush
        actions={
          <div className="flex gap-1">
            {[
              ["all", "Tất cả"],
              ["theory_room", "Lý thuyết"],
              ["workshop", "Xưởng"],
              ["tool_set", "Bộ dụng cụ"],
            ].map(([k, label]) => (
              <Button
                key={k}
                size="sm"
                variant={filter === k ? "primary" : "ghost"}
                onClick={() => setFilter(k)}
              >
                {label}
              </Button>
            ))}
          </div>
        }
      >
        <Table
          head={
            <>
              <th className="px-3 py-2">Mã phòng</th>
              <th className="px-3 py-2">Tên</th>
              <th className="px-3 py-2">Loại</th>
              <th className="px-3 py-2 text-right">Sức chứa</th>
              <th className="px-3 py-2 text-right">Số lượng</th>
              <th className="w-32 px-3 py-2">Suất dùng</th>
              <th className="px-3 py-2" />
            </>
          }
        >
          {visible.length === 0 && (
            <tr>
              <td colSpan={7}>
                <Empty>
                  {loading
                    ? "Đang tải…"
                    : "Chưa có phòng nào. Thêm thủ công hoặc nhập từ Excel."}
                </Empty>
              </td>
            </tr>
          )}
          {visible.map((r) => {
            const u = byCode.get(r.code);
            const pct = u?.usage_pct ?? 0;
            return (
              <tr key={r.id} className="border-b border-border last:border-0">
                <td className="px-3 py-2 font-mono text-[11.5px]">{r.code}</td>
                <td className="px-3 py-2">{r.name}</td>
                <td className="px-3 py-2">
                  <Pill tone={r.type === "workshop" ? "vocational" : "muted"}>
                    {TYPE_LABEL[r.type] ?? r.type}
                  </Pill>
                </td>
                <td className="tabular px-3 py-2 text-right font-mono">
                  {r.capacity || "—"}
                </td>
                <td className="tabular px-3 py-2 text-right font-mono">
                  {r.quantity}
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-head">
                      <i
                        className={`block h-full ${
                          pct > 88 ? "bg-destructive" : pct > 80 ? "bg-warn" : "bg-ok"
                        }`}
                        style={{ width: `${Math.min(100, pct)}%` }}
                      />
                    </div>
                    <span className="tabular font-mono text-[11px]">
                      {Math.round(pct)}%
                    </span>
                  </div>
                </td>
                <td className="px-3 py-2 text-right">
                  <Button size="sm" onClick={() => setEditing(r)}>
                    Sửa
                  </Button>
                </td>
              </tr>
            );
          })}
        </Table>
        <div className="border-t border-border bg-panel-2 px-4 py-2.5 text-[11.5px] text-foreground-2">
          Sức chứa <b>0</b> nghĩa là không khai giới hạn — dùng cho bộ dụng cụ.
          Buổi thực tập và buổi ngoài trường không tính vào suất sử dụng.
        </div>
      </Card>

      {campuses.length > 0 && (
        <Card title="Cơ sở đào tạo" flush>
          <Table
            head={
              <>
                <th className="px-3 py-2">Mã</th>
                <th className="px-3 py-2">Tên cơ sở</th>
                <th className="px-3 py-2">Địa chỉ</th>
                <th className="px-3 py-2 text-right">Di chuyển</th>
              </>
            }
          >
            {campuses.map((c) => (
              <tr key={c.id} className="border-b border-border last:border-0">
                <td className="px-3 py-2 font-mono text-[11.5px]">{c.code}</td>
                <td className="px-3 py-2 font-semibold">{c.name}</td>
                <td className="px-3 py-2 text-[12.5px] text-foreground-2">
                  {c.address || "—"}
                </td>
                <td className="tabular px-3 py-2 text-right font-mono">
                  {c.travel_minutes ? `${c.travel_minutes} phút` : "—"}
                </td>
              </tr>
            ))}
          </Table>
          <div className="border-t border-border bg-panel-2 px-4 py-2.5 text-[11.5px] text-foreground-2">
            Giáo viên dạy chéo hai cơ sở trong cùng ngày cần khoảng nghỉ đủ để di
            chuyển.
          </div>
        </Card>
      )}

      {(editing || creating) && (
        <RoomForm
          room={editing}
          onClose={() => {
            setEditing(null);
            setCreating(false);
          }}
          onSaved={() => {
            setEditing(null);
            setCreating(false);
            void load();
          }}
        />
      )}
    </>
  );
}

function RoomForm({
  room,
  onClose,
  onSaved,
}: {
  room: Resource | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { api } = useV2();
  const [f, setF] = useState({
    code: room?.code ?? "",
    name: room?.name ?? "",
    type: room?.type ?? "theory_room",
    capacity: room?.capacity ?? 0,
    quantity: room?.quantity ?? 1,
    available_quantity: room?.available_quantity ?? 1,
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const set = (k: string, v: unknown) => setF((p) => ({ ...p, [k]: v }));

  async function save() {
    if (!api) return;
    setBusy(true);
    setErr(null);
    try {
      if (room) await api.updateResource(room.id, f);
      else await api.createResource(f);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Lỗi lưu dữ liệu");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!api || !room) return;
    setBusy(true);
    try {
      await api.deleteResource(room.id);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Lỗi xoá");
      setBusy(false);
    }
  }

  return (
    <>
      <div className="fixed inset-0 z-50 bg-black/45" onClick={onClose} aria-hidden />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={room ? "Sửa phòng" : "Thêm phòng"}
        className="fixed inset-y-0 right-0 z-50 flex w-[min(420px,94vw)] flex-col border-l border-border-2 bg-panel"
      >
        <header className="flex items-start gap-2 border-b border-border px-4 py-3">
          <h2 className="text-base font-semibold">
            {room ? "Sửa phòng" : "Thêm phòng"}
          </h2>
          <button
            onClick={onClose}
            aria-label="Đóng"
            className="ml-auto text-xl leading-none text-foreground-3 hover:text-foreground"
          >
            ×
          </button>
        </header>

        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {err && (
            <Note tone="error" icon="✕">
              {err}
            </Note>
          )}
          <div className="grid grid-cols-2 gap-3">
            <Field label="Mã phòng">
              <input
                className={inputClass}
                value={f.code}
                onChange={(e) => set("code", e.target.value)}
                placeholder="A11-204"
              />
            </Field>
            <Field label="Loại">
              <select
                className={inputClass}
                value={f.type}
                onChange={(e) => set("type", e.target.value)}
              >
                {Object.entries(TYPE_LABEL).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <Field label="Tên phòng">
            <input
              className={inputClass}
              value={f.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="Xưởng điện tử"
            />
          </Field>
          <div className="grid grid-cols-3 gap-2">
            <Field label="Sức chứa">
              <input
                type="number"
                className={inputClass}
                value={f.capacity}
                onChange={(e) => set("capacity", Number(e.target.value))}
              />
            </Field>
            <Field label="Số lượng">
              <input
                type="number"
                className={inputClass}
                value={f.quantity}
                onChange={(e) => set("quantity", Number(e.target.value))}
              />
            </Field>
            <Field label="Còn dùng được">
              <input
                type="number"
                className={inputClass}
                value={f.available_quantity}
                onChange={(e) => set("available_quantity", Number(e.target.value))}
              />
            </Field>
          </div>
          {f.capacity === 0 && (
            <Note tone="muted" icon="◈">
              Sức chứa <b>0</b> nghĩa là không khai giới hạn — dùng cho bộ dụng cụ.
            </Note>
          )}
          {f.available_quantity > f.quantity && (
            <Note tone="warn" icon="!">
              Số còn dùng được ({f.available_quantity}) lớn hơn tổng số lượng (
              {f.quantity}).
            </Note>
          )}
        </div>

        <footer className="flex gap-2 border-t border-border px-4 py-3">
          <Button variant="primary" onClick={() => void save()} disabled={busy}>
            {busy ? "Đang lưu…" : "Lưu"}
          </Button>
          {room && (
            <Button
              onClick={() => void remove()}
              disabled={busy}
              className="!border-destructive !text-destructive"
            >
              Xoá
            </Button>
          )}
          <Button variant="ghost" onClick={onClose}>
            Huỷ
          </Button>
        </footer>
      </aside>
    </>
  );
}

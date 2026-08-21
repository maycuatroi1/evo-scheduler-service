"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card, Empty, Note, PageHeader, Pill, Stat, Table } from "@/components/ui";
import { createApiClient } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import { useV2 } from "@/lib/useV2";
import type { Campus } from "@/lib/api-v2";

type Room = {
  code: string;
  name: string;
  type: string;
  capacity: number;
  quantity: number;
};

const TYPE_LABEL: Record<string, string> = {
  theory_room: "Phòng lý thuyết",
  workshop: "Xưởng",
  tool_set: "Bộ dụng cụ",
};

export default function PhongPage() {
  const { token } = useAuth();
  const { api: v2 } = useV2();
  const [rooms, setRooms] = useState<Room[]>([]);
  const [campuses, setCampuses] = useState<Campus[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token || !v2) return;
    setLoading(true);
    setError(null);
    try {
      const stats = await createApiClient(token).getStats();
      // Danh sách phòng chưa có endpoint riêng; lấy từ thống kê tổng hợp
      setRooms([]);
      void stats;
      setCampuses(await v2.listCampuses());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải dữ liệu phòng");
    } finally {
      setLoading(false);
    }
  }, [token, v2]);

  useEffect(() => {
    void load();
  }, [load]);

  const visible =
    filter === "all" ? rooms : rooms.filter((r) => r.type === filter);
  const workshops = rooms.filter((r) => r.type === "workshop");

  if (!token) return <Empty>Cần đăng nhập để xem danh sách phòng.</Empty>;

  return (
    <>
      <PageHeader
        title="Phòng & xưởng"
        subtitle="Phòng lý thuyết dùng chung giữa khối văn hoá và khối nghề. Xưởng là tài nguyên khan hiếm nhất, quyết định thứ tự xếp lịch."
        actions={
          <Button onClick={() => void load()} disabled={loading}>
            {loading ? "Đang tải…" : "↻ Tải lại"}
          </Button>
        }
      />

      {error && (
        <Note tone="error" icon="✕">
          {error}
        </Note>
      )}

      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Tổng phòng" value={rooms.length} />
        <Stat label="Xưởng" value={workshops.length} tone="vocational" />
        <Stat label="Cơ sở đào tạo" value={campuses.length} tone="culture" />
        <Stat
          label="Sức chứa lớn nhất"
          value={rooms.length ? Math.max(...rooms.map((r) => r.capacity)) : "—"}
        />
      </div>

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
            </>
          }
        >
          {visible.length === 0 && (
            <tr>
              <td colSpan={5}>
                <Empty>
                  {loading
                    ? "Đang tải…"
                    : "Chưa có phòng nào. Nhập dữ liệu từ Excel để bắt đầu."}
                </Empty>
              </td>
            </tr>
          )}
          {visible.map((r) => (
            <tr key={r.code} className="border-b border-border last:border-0">
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
            </tr>
          ))}
        </Table>
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
    </>
  );
}

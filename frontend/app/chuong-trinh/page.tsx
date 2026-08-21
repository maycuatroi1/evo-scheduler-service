"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Card,
  Empty,
  Note,
  PageHeader,
  Pill,
  Stat,
  Table,
} from "@/components/ui";
import { useV2 } from "@/lib/useV2";
import type { ProgramRow } from "@/lib/api-v2";

const STATUS: Record<
  ProgramRow["status"],
  { label: string; tone: "ok" | "warn" | "muted" }
> = {
  dat: { label: "Đạt chuẩn", tone: "ok" },
  thieu_thuc_hanh: { label: "Thiếu thực hành", tone: "warn" },
  thua_thuc_hanh: { label: "Thừa thực hành", tone: "warn" },
  chua_khai_gio: { label: "Chưa khai giờ", tone: "muted" },
};

/** Thanh tỉ lệ thực hành, có vạch mốc khoảng cho phép. */
function RatioBar({ row }: { row: ProgramRow }) {
  const lo = row.min_pct ?? 0;
  const hi = row.max_pct ?? 100;
  const ok = row.status === "dat";
  return (
    <div className="min-w-[140px]">
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-panel-2">
        <div
          className="absolute inset-y-0 bg-ok/20"
          style={{ left: lo + "%", width: Math.max(0, hi - lo) + "%" }}
        />
        <div
          className={
            "absolute inset-y-0 left-0 rounded-full " +
            (ok ? "bg-ok" : "bg-warn")
          }
          style={{ width: Math.min(100, row.practice_pct) + "%" }}
        />
      </div>
      <p className="mt-1 text-[10.5px] text-foreground-3">
        {row.total_hours > 0
          ? "TH " + row.practice_pct + "% · cho phép " + lo + "–" + hi + "%"
          : "chưa có dữ liệu giờ"}
      </p>
    </div>
  );
}

export default function ChuongTrinhPage() {
  const { api } = useV2();
  const [rows, setRows] = useState<ProgramRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!api) return;
    setLoading(true);
    setError(null);
    try {
      const r = await api.programReport();
      setRows(r.programs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải báo cáo chương trình");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!api) return <Empty>Cần đăng nhập để xem chương trình đào tạo.</Empty>;

  const lech = rows.filter(
    (r) => r.status === "thieu_thuc_hanh" || r.status === "thua_thuc_hanh",
  );
  const chuaKhai = rows.filter((r) => r.status === "chua_khai_gio");
  const tongHS = rows.reduce((n, r) => n + r.student_count, 0);
  const tongGio = rows.reduce((n, r) => n + r.total_hours, 0);

  return (
    <>
      <PageHeader
        title="Chương trình đào tạo"
        subtitle="Ba chương trình dùng chung giáo viên và xưởng nên được xếp tuần tự: cao đẳng, rồi trung cấp, rồi trung cấp song bằng. Bảng dưới đối chiếu tỉ lệ thực hành với ngưỡng quy định."
      />

      {error && <Note tone="error">{error}</Note>}

      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Số chương trình" value={rows.length} tone="culture" />
        <Stat label="Tổng học sinh" value={tongHS} tone="culture" />
        <Stat label="Tổng giờ đã khai" value={tongGio} tone="vocational" />
        <Stat
          label="Lệch chuẩn"
          value={lech.length}
          tone={lech.length ? "warn" : "ok"}
          hint="Tỉ lệ thực hành ngoài khoảng cho phép"
        />
      </div>

      {lech.length > 0 && (
        <Note tone="warn">
          {lech.map((r) => r.label).join(", ")} có tỉ lệ thực hành nằm ngoài
          khoảng quy định. Điều chỉnh số giờ ở màn hình Mô-đun.
        </Note>
      )}

      {chuaKhai.length > 0 && (
        <Note tone="muted">
          {chuaKhai.map((r) => r.label).join(", ")} chưa khai giờ mô-đun nên
          chưa đối chiếu được tỉ lệ.
        </Note>
      )}

      <Card title="Tổng hợp theo chương trình" flush>
        {loading ? (
          <Empty>Đang tải...</Empty>
        ) : rows.length === 0 ? (
          <Empty>
            Chưa có nhóm nghề nào. Thêm ở màn hình Lớp &amp; nhóm nghề.
          </Empty>
        ) : (
          <Table
            head={
              <>
                <th className="px-3 py-2">Chương trình</th>
                <th className="px-3 py-2 text-right">Nhóm</th>
                <th className="px-3 py-2 text-right">Học sinh</th>
                <th className="px-3 py-2 text-right">Mô-đun</th>
                <th className="px-3 py-2 text-right">Giờ LT</th>
                <th className="px-3 py-2 text-right">Giờ TH</th>
                <th className="px-3 py-2">Tỉ lệ thực hành</th>
                <th className="px-3 py-2">Trạng thái</th>
              </>
            }
          >
            {rows.map((r) => (
              <tr key={r.program} className="border-b border-border-2">
                <td className="px-3 py-2 font-semibold">{r.label}</td>
                <td className="px-3 py-2 text-right">{r.group_count}</td>
                <td className="px-3 py-2 text-right">{r.student_count}</td>
                <td className="px-3 py-2 text-right">{r.module_count}</td>
                <td className="px-3 py-2 text-right">{r.theory_hours}</td>
                <td className="px-3 py-2 text-right">{r.practice_hours}</td>
                <td className="px-3 py-2">
                  <RatioBar row={r} />
                </td>
                <td className="px-3 py-2">
                  <Pill tone={STATUS[r.status].tone}>
                    {STATUS[r.status].label}
                  </Pill>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <Note tone="muted">
        Ngưỡng tỉ lệ theo TT 01/2024: cao đẳng thực hành 50–70%, trung cấp
        55–75%. Thông tư đang trong diện ban hành lại nên ngưỡng để ở cấu hình
        đơn vị, không cố định trong mã nguồn.
      </Note>
    </>
  );
}

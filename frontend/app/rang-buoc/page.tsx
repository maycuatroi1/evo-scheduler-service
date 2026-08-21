"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  Empty,
  Note,
  PageHeader,
  Pill,
  Table,
  inputClass,
} from "@/components/ui";
import { PRIORITY_LABEL, type Rule } from "@/lib/api-v2";
import { useV2 } from "@/lib/useV2";

/* Ràng buộc cứng luôn áp, không khai báo được — liệt kê để người dùng biết
   bộ giải đang bảo đảm những gì. */
const HARD_RULES: [string, string][] = [
  ["Giáo viên không dạy hai buổi cùng lúc", "teacher_no_overlap"],
  ["Lớp không học hai buổi cùng lúc", "student_no_overlap"],
  ["Nhóm cùng lớp văn hoá không trùng giờ", "group_same_class"],
  ["Ca văn hoá theo khối, ca nghề là phần bù", "shift_by_grade"],
  ["Trần sĩ số theo loại buổi (LT 35 · TH 18 · độc hại 10)", "capacity_by_type"],
  ["Buổi ngoài trường không chiếm phòng", "offsite_no_room"],
  ["Không vượt sức chứa xưởng, bộ dụng cụ", "shared_resource_pool"],
  ["Thực hành phải vào xưởng đúng loại", "resource_requirement"],
  ["Buổi nhiều tiết liền mạch trong ngày", "valid_starts"],
];

const RULE_LABEL: Record<string, string> = {
  unavailability: "Không dạy vào thời điểm đã khai",
  preference: "Nguyện vọng thời điểm",
  distribution: "San đều tải giữa giáo viên",
  adjacency: "Các buổi phải liền kề nhau",
  exclusion: "Các buổi loại trừ nhau",
  quota_limit: "Không vượt định mức giờ chuẩn",
  capacity_limit: "Sĩ số không vượt sức chứa phòng",
  resource_requirement: "Loại phòng phù hợp với loại buổi",
  group_same_class: "Nhóm cùng lớp văn hoá không trùng giờ",
  shift_by_grade: "Ca học theo khối",
  capacity_by_type: "Trần sĩ số theo loại buổi",
  offsite_no_room: "Buổi ngoài trường không chiếm phòng",
};

export default function RangBuocPage() {
  const { api } = useV2();
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"hard" | "soft">("soft");

  const load = useCallback(async () => {
    if (!api) return;
    setLoading(true);
    setError(null);
    try {
      setRules(await api.listRules());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải ràng buộc");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  async function setPriority(r: Rule, priority: string, weight?: number) {
    if (!api) return;
    try {
      const updated = await api.setPriority(r.id, priority, weight);
      setRules((p) => p.map((x) => (x.id === r.id ? updated : x)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi đổi độ ưu tiên");
    }
  }

  if (!api) return <Empty>Cần đăng nhập để xem ràng buộc.</Empty>;

  return (
    <>
      <PageHeader
        title="Ràng buộc xếp lịch"
        subtitle="Ràng buộc cứng luôn được bảo đảm. Ràng buộc mềm có độ ưu tiên: cao thì bộ giải cố giữ bằng mọi giá, thấp thì bỏ được khi bí."
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

      <div className="mb-4 flex gap-1">
        <Button
          variant={tab === "soft" ? "primary" : "ghost"}
          onClick={() => setTab("soft")}
        >
          Ràng buộc khai báo ({rules.length})
        </Button>
        <Button
          variant={tab === "hard" ? "primary" : "ghost"}
          onClick={() => setTab("hard")}
        >
          Ràng buộc cứng ({HARD_RULES.length})
        </Button>
      </div>

      {tab === "hard" ? (
        <Card title="Ràng buộc cứng — luôn áp dụng" flush>
          <Table
            head={
              <>
                <th className="px-3 py-2">Nội dung</th>
                <th className="px-3 py-2 text-right">Mã trong bộ giải</th>
              </>
            }
          >
            {HARD_RULES.map(([label, code]) => (
              <tr key={code} className="border-b border-border last:border-0">
                <td className="px-3 py-2">{label}</td>
                <td className="px-3 py-2 text-right">
                  <span className="rounded border border-border bg-head px-1.5 py-px font-mono text-[10.5px] text-foreground-2">
                    {code}
                  </span>
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      ) : (
        <Card title="Độ ưu tiên và trọng số" flush>
          <Table
            head={
              <>
                <th className="w-10 px-3 py-2 text-right">#</th>
                <th className="px-3 py-2">Ràng buộc</th>
                <th className="w-36 px-3 py-2">Độ ưu tiên</th>
                <th className="w-24 px-3 py-2">Trọng số</th>
                <th className="w-28 px-3 py-2 text-right">Hiệu dụng</th>
              </>
            }
          >
            {rules.length === 0 && (
              <tr>
                <td colSpan={5}>
                  <Empty>
                    {loading
                      ? "Đang tải…"
                      : "Chưa khai báo ràng buộc nào. Bộ giải vẫn áp đủ các ràng buộc cứng."}
                  </Empty>
                </td>
              </tr>
            )}
            {rules.map((r, i) => (
              <tr key={r.id} className="border-b border-border last:border-0">
                <td className="tabular px-3 py-2 text-right font-mono text-foreground-3">
                  {i + 1}
                </td>
                <td className="px-3 py-2">
                  {RULE_LABEL[r.type] ?? r.type}
                  <div className="font-mono text-[10.5px] text-foreground-3">
                    {r.type}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <select
                    className={inputClass + " w-full"}
                    value={r.priority}
                    onChange={(e) => void setPriority(r, e.target.value)}
                  >
                    {Object.entries(PRIORITY_LABEL).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-2">
                  <select
                    className={inputClass + " w-full"}
                    value={r.weight}
                    onChange={(e) =>
                      void setPriority(r, r.priority, Number(e.target.value))
                    }
                  >
                    {[1, 2, 3, 4, 5].map((w) => (
                      <option key={w} value={w}>
                        {w}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-2 text-right">
                  <Pill
                    tone={
                      r.priority === "high"
                        ? "error"
                        : r.priority === "medium"
                          ? "warn"
                          : "muted"
                    }
                  >
                    {r.effective_weight}
                  </Pill>
                </td>
              </tr>
            ))}
          </Table>
          <div className="border-t border-border bg-panel-2 px-4 py-2.5 text-[11.5px] text-foreground-2">
            Trọng số hiệu dụng = trọng số × hệ số ưu tiên (cao ×5, trung bình ×2,
            thấp ×1). Con số này quyết định mức phạt khi vi phạm.
          </div>
        </Card>
      )}
    </>
  );
}

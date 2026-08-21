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
import type { InheritDiff, Version } from "@/lib/api-v2";
import { useV2 } from "@/lib/useV2";

const KEEP_LEVELS: [string, string][] = [
  ["max", "Tối đa — chỉ xếp lại giáo viên có thay đổi"],
  ["vua", "Vừa — cho phép dịch tiết lân cận"],
  ["it", "Ít — dùng lịch cũ làm gợi ý"],
];

export default function KeThuaPage() {
  const { api } = useV2();
  const [versions, setVersions] = useState<Version[]>([]);
  const [target, setTarget] = useState<number | null>(null);
  const [base, setBase] = useState<number | null>(null);
  const [keep, setKeep] = useState("max");
  const [diff, setDiff] = useState<InheritDiff | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!api) return;
    try {
      const r = await api.versions();
      setVersions(r.versions);
      if (r.versions.length && target === null) setTarget(r.versions[0].id);
      if (r.versions.length > 1 && base === null) setBase(r.versions[1].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải phiên bản");
    }
    // chỉ chạy khi api đổi; target/base chỉ dùng để đặt giá trị mặc định lần đầu
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  async function scan() {
    if (!api || target === null || base === null) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setDiff(await api.inheritDiff(target, base));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi dò thay đổi");
    } finally {
      setBusy(false);
    }
  }

  async function apply() {
    if (!api || target === null || base === null) return;
    setBusy(true);
    setError(null);
    try {
      const r = await api.inherit(target, base, keep);
      setResult(
        `Đã sao chép ${r.copied} buổi từ lịch gốc; ${r.to_resolve} buổi cần xếp lại.`
      );
      void load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi kế thừa");
    } finally {
      setBusy(false);
    }
  }

  const label = (v: Version) =>
    `#${v.id} · ${v.name} · ${v.is_manual_edit ? "đã tinh chỉnh" : "bản gốc"}`;

  if (!api) return <Empty>Cần đăng nhập để dùng chức năng kế thừa.</Empty>;

  return (
    <>
      <PageHeader
        title="Kế thừa lịch cũ"
        subtitle="Khi sang học kỳ mới hoặc chỉ thay đổi phân công vài giáo viên, không cần xếp lại từ đầu. Hệ thống dò xem ai có thay đổi rồi chỉ xếp lại phần của họ."
      />

      {error && (
        <Note tone="error" icon="✕">
          {error}
        </Note>
      )}

      <Card title="Chọn phiên bản để kế thừa">
        <div className="flex flex-wrap items-end gap-3">
          <Field label="Lịch cần xếp">
            <select
              className={inputClass + " min-w-56"}
              value={target ?? ""}
              onChange={(e) => setTarget(Number(e.target.value))}
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {label(v)}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Phiên bản gốc">
            <select
              className={inputClass + " min-w-56"}
              value={base ?? ""}
              onChange={(e) => setBase(Number(e.target.value))}
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {label(v)}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Mức giữ nguyên">
            <select
              className={inputClass + " min-w-64"}
              value={keep}
              onChange={(e) => setKeep(e.target.value)}
            >
              {KEEP_LEVELS.map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </Field>
          <Button onClick={() => void scan()} disabled={busy || target === base}>
            {busy ? "Đang dò…" : "Dò thay đổi"}
          </Button>
          <Button
            variant="primary"
            onClick={() => void apply()}
            disabled={busy || !diff}
          >
            Kế thừa
          </Button>
        </div>

        {target !== null && target === base && (
          <Note tone="warn" icon="!">
            Lịch cần xếp và phiên bản gốc đang là một. Chọn hai phiên bản khác
            nhau.
          </Note>
        )}
        {result && (
          <Note tone="ok" icon="✓">
            {result}
          </Note>
        )}
      </Card>

      {diff && (
        <>
          <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat
              label="Giữ nguyên"
              value={`${diff.keep_pct}%`}
              hint="ước tính lịch cũ"
              tone="ok"
            />
            <Stat
              label="GV có thay đổi"
              value={diff.changed.length}
              tone={diff.changed.length ? "warn" : "ok"}
            />
            <Stat label="GV giữ nguyên" value={diff.unchanged_count} />
            <Stat label="Tổng giáo viên" value={diff.total_teachers} />
          </div>

          <Card title="Giáo viên có thay đổi phân công" flush>
            <Table
              head={
                <>
                  <th className="px-3 py-2">Giáo viên</th>
                  <th className="px-3 py-2">Thay đổi</th>
                  <th className="px-3 py-2 text-right">Mô-đun cũ</th>
                  <th className="px-3 py-2 text-right">Mô-đun mới</th>
                  <th className="px-3 py-2">Xử lý</th>
                </>
              }
            >
              {diff.changed.length === 0 && (
                <tr>
                  <td colSpan={5}>
                    <Empty>
                      Không giáo viên nào đổi phân công — kế thừa được toàn bộ.
                    </Empty>
                  </td>
                </tr>
              )}
              {diff.changed.map((c) => (
                <tr
                  key={c.teacher_code}
                  className="border-b border-border bg-warn-bg last:border-0"
                >
                  <td className="px-3 py-2">
                    <b>{c.teacher_name || c.teacher_code}</b>
                    <div className="font-mono text-[10.5px] text-foreground-3">
                      {c.teacher_code}
                    </div>
                  </td>
                  <td className="px-3 py-2 text-[12.5px]">
                    {c.added_modules.length > 0 && (
                      <div className="text-ok">
                        + nhận thêm: {c.added_modules.join(", ")}
                      </div>
                    )}
                    {c.removed_modules.length > 0 && (
                      <div className="text-destructive">
                        − chuyển đi: {c.removed_modules.join(", ")}
                      </div>
                    )}
                  </td>
                  <td className="tabular px-3 py-2 text-right font-mono">
                    {c.old_count}
                  </td>
                  <td className="tabular px-3 py-2 text-right font-mono">
                    {c.new_count}
                  </td>
                  <td className="px-3 py-2">
                    <Pill tone="warn">Xếp lại</Pill>
                  </td>
                </tr>
              ))}
            </Table>
            <div className="border-t border-border bg-panel-2 px-4 py-2.5 text-[11.5px] text-foreground-2">
              Chỉ những dòng trên được xếp lại. {diff.unchanged_count} giáo viên
              còn lại giữ nguyên vị trí tiết.
            </div>
          </Card>
        </>
      )}

      <Card title="Lịch sử phiên bản" flush>
        <Table
          head={
            <>
              <th className="w-20 px-3 py-2 text-right">Phiên bản</th>
              <th className="px-3 py-2">Tên</th>
              <th className="px-3 py-2">Loại</th>
              <th className="px-3 py-2">Trạng thái</th>
              <th className="px-3 py-2 text-right">Chưa xếp</th>
              <th className="px-3 py-2">Kế thừa từ</th>
            </>
          }
        >
          {versions.length === 0 && (
            <tr>
              <td colSpan={6}>
                <Empty>Chưa có phiên bản nào.</Empty>
              </td>
            </tr>
          )}
          {versions.map((v) => (
            <tr key={v.id} className="border-b border-border last:border-0">
              <td className="tabular px-3 py-2 text-right font-mono">#{v.id}</td>
              <td className="px-3 py-2">{v.name}</td>
              <td className="px-3 py-2">
                <Pill tone={v.is_manual_edit ? "culture" : "muted"}>
                  {v.is_manual_edit ? "Đã tinh chỉnh" : "Bản gốc"}
                </Pill>
              </td>
              <td className="px-3 py-2">
                <Pill
                  tone={
                    v.status === "published"
                      ? "ok"
                      : v.status === "failed"
                        ? "error"
                        : "muted"
                  }
                >
                  {v.status}
                </Pill>
              </td>
              <td className="tabular px-3 py-2 text-right font-mono">
                {v.unplaced_count || "—"}
              </td>
              <td className="px-3 py-2 font-mono text-[11.5px]">
                {v.inherited_from ? `#${v.inherited_from}` : "—"}
              </td>
            </tr>
          ))}
        </Table>
      </Card>
    </>
  );
}

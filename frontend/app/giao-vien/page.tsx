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
import type { Department, TeacherFull, WorkloadRow } from "@/lib/api-v2";
import { useV2 } from "@/lib/useV2";

export default function GiaoVienPage() {
  const { api } = useV2();
  const [teachers, setTeachers] = useState<TeacherFull[]>([]);
  const [workload, setWorkload] = useState<WorkloadRow[]>([]);
  const [depts, setDepts] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<TeacherFull | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    if (!api) return;
    setLoading(true);
    setError(null);
    try {
      const [t, w, d] = await Promise.all([
        api.listTeachers(),
        api.workload(),
        api.listDepartments(),
      ]);
      setTeachers(t);
      setWorkload(w.teachers);
      setDepts(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải dữ liệu");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  const byCode = new Map(workload.map((w) => [w.code, w]));
  const over = workload.filter((w) => w.over > 0);
  const deptName = (id: number | null) =>
    depts.find((d) => d.id === id)?.name ?? "—";

  if (!api) return <Empty>Cần đăng nhập để xem danh sách giáo viên.</Empty>;

  return (
    <>
      <PageHeader
        title="Giáo viên"
        subtitle="Tải giảng dạy quy đổi giờ chuẩn: 45 phút lý thuyết = 1 giờ chuẩn, 60 phút thực hành = 1 giờ chuẩn nên tiết thực hành quy đổi 0,75. Buổi thực tập không tính vào định mức."
        actions={
          <>
            <Button onClick={() => void load()} disabled={loading}>
              {loading ? "Đang tải…" : "↻ Tải lại"}
            </Button>
            <Button variant="primary" onClick={() => setCreating(true)}>
              + Thêm giáo viên
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
        <Stat label="Tổng giáo viên" value={teachers.length} />
        <Stat
          label="Khối nghề"
          value={teachers.filter((t) => t.blocks?.includes("vocational")).length}
          tone="vocational"
        />
        <Stat
          label="Khối văn hoá"
          value={teachers.filter((t) => t.blocks?.includes("culture")).length}
          tone="culture"
        />
        <Stat
          label="Vượt định mức"
          value={over.length}
          tone={over.length ? "error" : "ok"}
        />
      </div>

      {over.length > 0 && (
        <Card title="Vượt định mức giờ chuẩn">
          {over.slice(0, 5).map((w) => (
            <Note key={w.code} tone="error" icon="↑">
              <b>{w.name}</b> — {w.standard_hours} giờ chuẩn, định mức {w.quota}.
              Vượt <b>{w.over} giờ</b>.
              <div className="mt-1 border-t border-dashed border-current pt-1 text-[12px] opacity-90">
                Chuyển bớt mô-đun sang giáo viên khác cùng bộ môn, hoặc tính giờ
                vượt theo quy định.
              </div>
            </Note>
          ))}
        </Card>
      )}

      <Card title="Danh sách giáo viên" flush>
        <Table
          head={
            <>
              <th className="px-3 py-2">Mã</th>
              <th className="px-3 py-2">Họ tên</th>
              <th className="px-3 py-2">Khoa</th>
              <th className="px-3 py-2 text-right">Tiết LT</th>
              <th className="px-3 py-2 text-right">Tiết TH</th>
              <th className="px-3 py-2 text-right">Giờ chuẩn</th>
              <th className="w-32 px-3 py-2">So định mức</th>
              <th className="px-3 py-2" />
            </>
          }
        >
          {teachers.length === 0 && (
            <tr>
              <td colSpan={8}>
                <Empty>
                  {loading ? "Đang tải…" : "Chưa có giáo viên nào."}
                </Empty>
              </td>
            </tr>
          )}
          {teachers.map((t) => {
            const w = byCode.get(t.code);
            const pct = w?.usage_pct ?? 0;
            const isOver = (w?.over ?? 0) > 0;
            return (
              <tr
                key={t.id}
                className={`border-b border-border last:border-0 ${
                  isOver ? "bg-destructive-bg" : ""
                }`}
              >
                <td className="px-3 py-2 font-mono text-[11.5px]">{t.code}</td>
                <td className="px-3 py-2">
                  <b>{t.name}</b>
                  {t.email && (
                    <div className="text-[11px] text-foreground-3">{t.email}</div>
                  )}
                </td>
                <td className="px-3 py-2 text-[12px]">
                  {deptName(t.department_id)}
                </td>
                <td className="tabular px-3 py-2 text-right font-mono">
                  {w?.theory_periods ?? 0}
                </td>
                <td className="tabular px-3 py-2 text-right font-mono">
                  {w?.practice_periods ?? 0}
                </td>
                <td className="tabular px-3 py-2 text-right font-mono font-semibold">
                  {w?.standard_hours ?? 0}
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-head">
                      <i
                        className={`block h-full ${
                          isOver
                            ? "bg-destructive"
                            : pct > 85
                              ? "bg-warn"
                              : "bg-ok"
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
                  <Button size="sm" onClick={() => setEditing(t)}>
                    Sửa
                  </Button>
                </td>
              </tr>
            );
          })}
        </Table>
      </Card>

      {(editing || creating) && (
        <TeacherForm
          teacher={editing}
          depts={depts}
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

function TeacherForm({
  teacher,
  depts,
  onClose,
  onSaved,
}: {
  teacher: TeacherFull | null;
  depts: Department[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const { api } = useV2();
  const [f, setF] = useState({
    code: teacher?.code ?? "",
    name: teacher?.name ?? "",
    moet_code: teacher?.moet_code ?? "",
    email: teacher?.email ?? "",
    department_id: teacher?.department_id ?? null,
    quota_standard_hours: teacher?.quota_standard_hours ?? 550,
    max_periods_per_session: teacher?.max_periods_per_session ?? null,
    min_periods_per_session: teacher?.min_periods_per_session ?? null,
    days_off_per_week: teacher?.days_off_per_week ?? null,
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const set = (k: string, v: unknown) => setF((p) => ({ ...p, [k]: v }));
  const num = (v: string) => (v === "" ? null : Number(v));

  async function save() {
    if (!api) return;
    setBusy(true);
    setErr(null);
    try {
      if (teacher) await api.updateTeacher(teacher.id, f);
      else await api.createTeacher(f);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Lỗi lưu dữ liệu");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!api || !teacher) return;
    setBusy(true);
    try {
      await api.deleteTeacher(teacher.id);
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
        aria-label={teacher ? "Sửa giáo viên" : "Thêm giáo viên"}
        className="fixed inset-y-0 right-0 z-50 flex w-[min(420px,94vw)] flex-col border-l border-border-2 bg-panel"
      >
        <header className="flex items-start gap-2 border-b border-border px-4 py-3">
          <h2 className="text-base font-semibold">
            {teacher ? "Sửa giáo viên" : "Thêm giáo viên"}
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
          <Field label="Họ tên">
            <input
              className={inputClass}
              value={f.name}
              onChange={(e) => set("name", e.target.value)}
            />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Mã giáo viên">
              <input
                className={inputClass}
                value={f.code}
                onChange={(e) => set("code", e.target.value)}
                placeholder="GV073"
              />
            </Field>
            <Field label="Mã Bộ GD&ĐT">
              <input
                className={inputClass}
                value={f.moet_code}
                onChange={(e) => set("moet_code", e.target.value)}
                placeholder="không bắt buộc"
              />
            </Field>
          </div>
          <Field label="Email">
            <input
              className={inputClass}
              value={f.email}
              onChange={(e) => set("email", e.target.value)}
            />
          </Field>
          <Field label="Khoa / tổ bộ môn">
            <select
              className={inputClass}
              value={f.department_id ?? ""}
              onChange={(e) => set("department_id", num(e.target.value))}
            >
              <option value="">— Chưa gán —</option>
              {depts.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Định mức giờ chuẩn / năm">
            <input
              type="number"
              className={inputClass}
              value={f.quota_standard_hours ?? ""}
              onChange={(e) => set("quota_standard_hours", num(e.target.value))}
              placeholder="550"
            />
          </Field>

          <p className="pt-1 text-[10.5px] uppercase tracking-wider text-foreground-3">
            Ràng buộc cá nhân — để trống nghĩa là không áp
          </p>
          <div className="grid grid-cols-3 gap-2">
            <Field label="Tối thiểu tiết/buổi">
              <input
                type="number"
                className={inputClass}
                value={f.min_periods_per_session ?? ""}
                onChange={(e) =>
                  set("min_periods_per_session", num(e.target.value))
                }
                placeholder="2"
              />
            </Field>
            <Field label="Tối đa tiết/buổi">
              <input
                type="number"
                className={inputClass}
                value={f.max_periods_per_session ?? ""}
                onChange={(e) =>
                  set("max_periods_per_session", num(e.target.value))
                }
                placeholder="4"
              />
            </Field>
            <Field label="Ngày nghỉ/tuần">
              <input
                type="number"
                className={inputClass}
                value={f.days_off_per_week ?? ""}
                onChange={(e) => set("days_off_per_week", num(e.target.value))}
                placeholder="1"
              />
            </Field>
          </div>
        </div>

        <footer className="flex gap-2 border-t border-border px-4 py-3">
          <Button variant="primary" onClick={() => void save()} disabled={busy}>
            {busy ? "Đang lưu…" : "Lưu"}
          </Button>
          {teacher && (
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

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
import type { Group, Module } from "@/lib/api-v2";

type Draft = {
  code: string;
  name: string;
  theory_hours: number;
  practice_hours: number;
  student_group_id: number | null;
};

const EMPTY: Draft = {
  code: "",
  name: "",
  theory_hours: 0,
  practice_hours: 0,
  student_group_id: null,
};

export default function ModunPage() {
  const { api } = useV2();
  const [modules, setModules] = useState<Module[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [q, setQ] = useState("");
  const [groupFilter, setGroupFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!api) return;
    setLoading(true);
    setError(null);
    try {
      const [m, g] = await Promise.all([api.listModules(), api.listGroups()]);
      setModules(m);
      setGroups(g);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải danh sách mô-đun");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  async function save() {
    if (!api || !draft) return;
    if (!draft.code.trim() || !draft.name.trim()) {
      setError("Mã và tên mô-đun không được để trống.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (editingId != null) await api.updateModule(editingId, draft);
      else await api.createModule(draft);
      setDraft(null);
      setEditingId(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi lưu mô-đun");
    } finally {
      setSaving(false);
    }
  }

  async function remove(m: Module) {
    if (!api) return;
    if (!window.confirm("Xoá mô-đun " + m.code + "?")) return;
    setError(null);
    try {
      await api.deleteModule(m.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi xoá mô-đun");
    }
  }

  if (!api) return <Empty>Cần đăng nhập để xem danh sách mô-đun.</Empty>;

  const visible = modules.filter((m) => {
    if (groupFilter !== "all" && m.group_code !== groupFilter) return false;
    const needle = q.trim().toLowerCase();
    if (!needle) return true;
    return (
      m.code.toLowerCase().includes(needle) ||
      m.name.toLowerCase().includes(needle)
    );
  });
  const totalLT = modules.reduce((n, m) => n + m.theory_hours, 0);
  const totalTH = modules.reduce((n, m) => n + m.practice_hours, 0);
  const chuaGan = modules.filter((m) => !m.group_code).length;
  const chuaSinhBuoi = modules.filter(
    (m) => m.total_hours > 0 && m.session_count === 0,
  ).length;

  return (
    <>
      <PageHeader
        title="Mô-đun"
        subtitle="Khai số giờ lý thuyết và thực hành của từng mô-đun. Số giờ ở đây là căn cứ để sinh buổi học và để đối chiếu tỉ lệ LT/TH của chương trình."
        actions={
          <Button
            variant="primary"
            onClick={() => {
              setDraft({ ...EMPTY });
              setEditingId(null);
            }}
          >
            + Thêm mô-đun
          </Button>
        }
      />

      {error && <Note tone="error">{error}</Note>}

      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Số mô-đun" value={modules.length} tone="culture" />
        <Stat label="Tổng giờ LT" value={totalLT} tone="culture" />
        <Stat label="Tổng giờ TH" value={totalTH} tone="vocational" />
        <Stat
          label="Chưa sinh buổi"
          value={chuaSinhBuoi}
          tone={chuaSinhBuoi ? "warn" : "ok"}
          hint="Đã khai giờ nhưng chưa có buổi học nào"
        />
      </div>

      {chuaGan > 0 && (
        <Note tone="warn">
          {chuaGan} mô-đun chưa gán nhóm nghề nên không được tính vào báo cáo
          chương trình đào tạo.
        </Note>
      )}

      {draft && (
        <Card title={editingId != null ? "Sửa mô-đun" : "Thêm mô-đun"}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Field label="Mã mô-đun">
              <input
                className={inputClass}
                value={draft.code}
                onChange={(e) => setDraft({ ...draft, code: e.target.value })}
              />
            </Field>
            <Field label="Tên mô-đun">
              <input
                className={inputClass}
                value={draft.name}
                onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              />
            </Field>
            <Field label="Giờ lý thuyết">
              <input
                type="number"
                min={0}
                className={inputClass}
                value={draft.theory_hours}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    theory_hours: Number(e.target.value) || 0,
                  })
                }
              />
            </Field>
            <Field label="Giờ thực hành">
              <input
                type="number"
                min={0}
                className={inputClass}
                value={draft.practice_hours}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    practice_hours: Number(e.target.value) || 0,
                  })
                }
              />
            </Field>
            <Field label="Nhóm nghề">
              <select
                className={inputClass}
                value={draft.student_group_id ?? ""}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    student_group_id: e.target.value
                      ? Number(e.target.value)
                      : null,
                  })
                }
              >
                <option value="">(chưa gán)</option>
                {groups.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.code}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <div className="mt-3 flex gap-2">
            <Button variant="primary" onClick={save} disabled={saving}>
              {saving ? "Đang lưu..." : "Lưu"}
            </Button>
            <Button
              onClick={() => {
                setDraft(null);
                setEditingId(null);
              }}
            >
              Huỷ
            </Button>
          </div>
        </Card>
      )}

      <Card
        title={"Danh sách mô-đun (" + visible.length + "/" + modules.length + ")"}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <input
              className={inputClass}
              placeholder="Tìm mã hoặc tên..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <select
              className={inputClass}
              value={groupFilter}
              onChange={(e) => setGroupFilter(e.target.value)}
            >
              <option value="all">Tất cả nhóm nghề</option>
              {groups.map((g) => (
                <option key={g.id} value={g.code}>
                  {g.code}
                </option>
              ))}
            </select>
          </div>
        }
        flush
      >
        {loading ? (
          <Empty>Đang tải...</Empty>
        ) : visible.length === 0 ? (
          <Empty>Chưa có mô-đun nào khớp bộ lọc.</Empty>
        ) : (
          <Table
            head={
              <>
                <th className="px-3 py-2">Mã</th>
                <th className="px-3 py-2">Tên mô-đun</th>
                <th className="px-3 py-2">Nhóm nghề</th>
                <th className="px-3 py-2 text-right">Giờ LT</th>
                <th className="px-3 py-2 text-right">Giờ TH</th>
                <th className="px-3 py-2 text-right">Tổng</th>
                <th className="px-3 py-2 text-right">Buổi đã sinh</th>
                <th className="px-3 py-2"></th>
              </>
            }
          >
            {visible.map((m) => (
              <tr key={m.id} className="border-b border-border-2">
                <td className="px-3 py-2 font-semibold">{m.code}</td>
                <td className="px-3 py-2">{m.name}</td>
                <td className="px-3 py-2">
                  {m.group_code ? (
                    <Pill tone="vocational">{m.group_code}</Pill>
                  ) : (
                    <Pill tone="warn">chưa gán</Pill>
                  )}
                </td>
                <td className="px-3 py-2 text-right">{m.theory_hours}</td>
                <td className="px-3 py-2 text-right">{m.practice_hours}</td>
                <td className="px-3 py-2 text-right font-semibold">
                  {m.total_hours}
                </td>
                <td className="px-3 py-2 text-right">
                  {m.session_count === 0 && m.total_hours > 0 ? (
                    <Pill tone="warn">0</Pill>
                  ) : (
                    m.session_count
                  )}
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap">
                  <Button
                    size="sm"
                    onClick={() => {
                      setDraft({
                        code: m.code,
                        name: m.name,
                        theory_hours: m.theory_hours,
                        practice_hours: m.practice_hours,
                        student_group_id: m.student_group_id,
                      });
                      setEditingId(m.id);
                    }}
                  >
                    Sửa
                  </Button>{" "}
                  <Button size="sm" onClick={() => remove(m)}>
                    Xoá
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

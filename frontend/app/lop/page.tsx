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
import { SHIFT_LABEL, type Group, type Homeroom } from "@/lib/api-v2";
import { useV2 } from "@/lib/useV2";

type Tab = "all" | "split" | "merged";

export default function LopPage() {
  const { api } = useV2();
  const [homerooms, setHomerooms] = useState<Homeroom[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [tab, setTab] = useState<Tab>("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Group | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    if (!api) return;
    setLoading(true);
    setError(null);
    try {
      const [h, g] = await Promise.all([api.listHomerooms(), api.listGroups()]);
      setHomerooms(h);
      setGroups(g);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải dữ liệu");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  // Lớp văn hoá xuất hiện ở nhiều nhóm nghề — dữ liệu thật: 11A3 tách 3 nhóm
  const splitClasses = homerooms.filter((h) => h.group_count > 1);
  // Nhóm nghề gộp nhiều lớp — dữ liệu thật: 12A1 + 12A4 thành 44 HS
  const mergedGroups = groups.filter((g) => g.homeroom_codes.length > 1);

  const visible =
    tab === "split"
      ? groups.filter((g) =>
          g.homeroom_codes.some((c) =>
            splitClasses.some((h) => h.code === c)
          )
        )
      : tab === "merged"
        ? mergedGroups
        : groups;

  const totalStudents = groups.reduce((n, g) => n + g.size, 0);
  const overCap = groups.filter((g) => g.practice_batches > 1);

  if (!api) return <Empty>Cần đăng nhập để xem dữ liệu lớp.</Empty>;

  return (
    <>
      <PageHeader
        title="Lớp & nhóm nghề"
        subtitle="Học sinh hệ 9+ sinh hoạt theo lớp văn hoá nhưng học nghề theo nhóm nghề. Một lớp có thể tách nhiều nhóm, và nhiều lớp có thể gộp chung một nhóm."
        actions={
          <>
            <Button onClick={() => void load()} disabled={loading}>
              {loading ? "Đang tải…" : "↻ Tải lại"}
            </Button>
            <Button variant="primary" onClick={() => setCreating(true)}>
              + Thêm nhóm nghề
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
        <Stat label="Lớp văn hoá" value={homerooms.length} tone="culture" />
        <Stat label="Nhóm nghề" value={groups.length} tone="vocational" />
        <Stat label="Tổng học sinh" value={totalStudents} hint="theo nhóm nghề" />
        <Stat
          label="Cần chia ca TH"
          value={overCap.length}
          hint="vượt trần sĩ số"
          tone={overCap.length ? "warn" : "ok"}
        />
      </div>

      {splitClasses.length > 0 && (
        <Card title="Lớp tách nhiều nhóm nghề">
          {splitClasses.map((h) => {
            const gs = groups.filter((g) => g.homeroom_codes.includes(h.code));
            const total = gs.reduce((n, g) => n + g.size, 0);
            return (
              <Note key={h.id} tone="warn" icon="⚯">
                <b>Lớp {h.code}</b> tách <b>{gs.length} nhóm nghề</b>, tổng{" "}
                <b>{total} học sinh</b>:{" "}
                {gs.map((g) => `${g.name} (${g.size})`).join(" · ")}
                <div className="mt-1 border-t border-dashed border-current pt-1 text-[12px] opacity-90">
                  Khi bất kỳ nhóm nào đang học, cả lớp {h.code} không thể có tiết
                  văn hoá; hai nhóm cùng lớp cũng không được trùng giờ nhau.
                </div>
              </Note>
            );
          })}
        </Card>
      )}

      {mergedGroups.length > 0 && (
        <Card title="Nhiều lớp gộp một nhóm nghề">
          {mergedGroups.map((g) => (
            <Note key={g.id} tone="culture" icon="⊕">
              <b>{g.name}</b> gộp {g.homeroom_codes.length} lớp:{" "}
              {g.homeroom_codes.join(" + ")} — tổng <b>{g.size} học sinh</b>
              {g.practice_batches > 1 && (
                <div className="mt-1 border-t border-dashed border-current pt-1 text-[12px] opacity-90">
                  Vượt trần thực hành nên phải chia {g.practice_batches} ca.
                </div>
              )}
            </Note>
          ))}
        </Card>
      )}

      <Card
        title="Danh sách nhóm nghề"
        flush
        actions={
          <div className="flex gap-1">
            {(
              [
                ["all", `Tất cả (${groups.length})`],
                ["split", `Từ lớp tách (${splitClasses.length})`],
                ["merged", `Nhóm gộp (${mergedGroups.length})`],
              ] as [Tab, string][]
            ).map(([k, label]) => (
              <Button
                key={k}
                size="sm"
                variant={tab === k ? "primary" : "ghost"}
                onClick={() => setTab(k)}
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
              <th className="px-3 py-2">Nhóm nghề</th>
              <th className="px-3 py-2">Lớp văn hoá</th>
              <th className="px-3 py-2 text-right">Sĩ số</th>
              <th className="px-3 py-2 text-right">Ca thực hành</th>
              <th className="px-3 py-2">Trạng thái</th>
              <th className="px-3 py-2" />
            </>
          }
        >
          {visible.length === 0 && (
            <tr>
              <td colSpan={6}>
                <Empty>
                  {loading ? "Đang tải…" : "Chưa có nhóm nghề nào."}
                </Empty>
              </td>
            </tr>
          )}
          {visible.map((g) => (
            <tr key={g.id} className="border-b border-border last:border-0">
              <td className="px-3 py-2">
                <b>{g.name}</b>
                <div className="font-mono text-[10.5px] text-foreground-3">
                  {g.code}
                </div>
              </td>
              <td className="px-3 py-2">
                {g.homeroom_codes.length ? (
                  <span className="flex flex-wrap gap-1">
                    {g.homeroom_codes.map((c) => (
                      <span
                        key={c}
                        className="rounded border border-border bg-head px-1.5 py-px font-mono text-[10.5px]"
                      >
                        {c}
                      </span>
                    ))}
                  </span>
                ) : (
                  <span className="text-foreground-3">—</span>
                )}
              </td>
              <td className="tabular px-3 py-2 text-right font-mono">{g.size}</td>
              <td className="tabular px-3 py-2 text-right font-mono">
                {g.practice_batches}
              </td>
              <td className="px-3 py-2">
                {g.practice_batches > 1 ? (
                  <Pill tone="warn">
                    Chia {g.practice_batches} ca
                    {g.hazardous ? " · trần 10" : " · trần 18"}
                  </Pill>
                ) : (
                  <Pill tone="ok">Đủ trần</Pill>
                )}
              </td>
              <td className="px-3 py-2 text-right">
                <Button size="sm" onClick={() => setEditing(g)}>
                  Sửa
                </Button>
              </td>
            </tr>
          ))}
        </Table>
      </Card>

      <Card title="Lớp văn hoá" flush>
        <Table
          head={
            <>
              <th className="px-3 py-2">Mã lớp</th>
              <th className="px-3 py-2 text-right">Khối</th>
              <th className="px-3 py-2 text-right">Sĩ số</th>
              <th className="px-3 py-2">Ca văn hoá</th>
              <th className="px-3 py-2">Ca học nghề</th>
              <th className="px-3 py-2 text-right">Số nhóm</th>
            </>
          }
        >
          {homerooms.length === 0 && (
            <tr>
              <td colSpan={6}>
                <Empty>Chưa có lớp văn hoá nào.</Empty>
              </td>
            </tr>
          )}
          {homerooms.map((h) => (
            <tr key={h.id} className="border-b border-border last:border-0">
              <td className="px-3 py-2 font-semibold">{h.code}</td>
              <td className="tabular px-3 py-2 text-right font-mono">
                {h.grade ?? "—"}
              </td>
              <td className="tabular px-3 py-2 text-right font-mono">{h.size}</td>
              <td className="px-3 py-2">
                <Pill tone="culture">{SHIFT_LABEL[h.culture_shift]}</Pill>
              </td>
              <td className="px-3 py-2">
                <Pill tone="vocational">{SHIFT_LABEL[h.vocational_shift]}</Pill>
              </td>
              <td className="tabular px-3 py-2 text-right font-mono">
                {h.group_count > 1 ? (
                  <span className="text-warn">⚯ {h.group_count}</span>
                ) : (
                  h.group_count
                )}
              </td>
            </tr>
          ))}
        </Table>
      </Card>

      {(editing || creating) && (
        <GroupForm
          group={editing}
          homerooms={homerooms}
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

function GroupForm({
  group,
  homerooms,
  onClose,
  onSaved,
}: {
  group: Group | null;
  homerooms: Homeroom[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const { api } = useV2();
  const [code, setCode] = useState(group?.code ?? "");
  const [name, setName] = useState(group?.name ?? "");
  const [size, setSize] = useState(group?.size ?? 0);
  const [hazardous, setHazardous] = useState(group?.hazardous ?? false);
  const [picked, setPicked] = useState<number[]>(
    homerooms.filter((h) => group?.homeroom_codes.includes(h.code)).map((h) => h.id)
  );
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const cap = hazardous ? 10 : 18;
  const batches = size > 0 ? Math.ceil(size / cap) : 1;

  async function save() {
    if (!api) return;
    setBusy(true);
    setErr(null);
    try {
      const body = {
        code,
        name,
        size: Number(size) || 0,
        hazardous,
        homeroom_ids: picked,
      };
      if (group) await api.updateGroup(group.id, body);
      else await api.createGroup(body);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Lỗi lưu dữ liệu");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!api || !group) return;
    setBusy(true);
    try {
      await api.deleteGroup(group.id);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Lỗi xoá");
      setBusy(false);
    }
  }

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/45"
        onClick={onClose}
        aria-hidden
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={group ? "Sửa nhóm nghề" : "Thêm nhóm nghề"}
        className="fixed inset-y-0 right-0 z-50 flex w-[min(420px,94vw)] flex-col border-l border-border-2 bg-panel"
      >
        <header className="flex items-start gap-2 border-b border-border px-4 py-3">
          <div>
            <h2 className="text-base font-semibold">
              {group ? "Sửa nhóm nghề" : "Thêm nhóm nghề"}
            </h2>
            <p className="text-[11.5px] text-foreground-3">
              Chọn các lớp văn hoá góp học sinh vào nhóm này
            </p>
          </div>
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
            <Field label="Mã nhóm">
              <input
                className={inputClass}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="G15"
              />
            </Field>
            <Field label="Sĩ số">
              <input
                type="number"
                className={inputClass}
                value={size}
                onChange={(e) => setSize(Number(e.target.value))}
              />
            </Field>
          </div>
          <Field label="Tên nghề">
            <input
              className={inputClass}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="CNKT Điều khiển tự động"
            />
          </Field>

          <label className="flex items-center gap-2 text-[13px]">
            <input
              type="checkbox"
              checked={hazardous}
              onChange={(e) => setHazardous(e.target.checked)}
            />
            Nghề nặng nhọc, độc hại (trần thực hành 10 thay vì 18)
          </label>

          <Note tone={batches > 1 ? "warn" : "ok"} icon={batches > 1 ? "!" : "✓"}>
            {batches > 1 ? (
              <>
                Sĩ số {size} vượt trần {cap} — mỗi mô-đun thực hành phải chia{" "}
                <b>{batches} ca</b>, cần {batches} lượt xưởng và giáo viên.
              </>
            ) : (
              <>Sĩ số {size} nằm trong trần {cap}, học nguyên ca.</>
            )}
          </Note>

          <div>
            <p className="mb-1.5 text-[10.5px] uppercase tracking-wider text-foreground-3">
              Lớp văn hoá ({picked.length} đã chọn)
            </p>
            <div className="max-h-52 space-y-1 overflow-y-auto rounded-md border border-border p-2">
              {homerooms.length === 0 && (
                <p className="text-[12.5px] text-foreground-3">
                  Chưa có lớp văn hoá nào.
                </p>
              )}
              {homerooms.map((h) => (
                <label
                  key={h.id}
                  className="flex items-center gap-2 text-[13px]"
                >
                  <input
                    type="checkbox"
                    checked={picked.includes(h.id)}
                    onChange={(e) =>
                      setPicked((p) =>
                        e.target.checked
                          ? [...p, h.id]
                          : p.filter((x) => x !== h.id)
                      )
                    }
                  />
                  <span className="font-mono">{h.code}</span>
                  <span className="text-foreground-3">
                    {h.grade ? `khối ${h.grade}` : ""} · {h.size} HS ·{" "}
                    {SHIFT_LABEL[h.culture_shift]}
                  </span>
                </label>
              ))}
            </div>
            {picked.length > 1 && (
              <p className="mt-1.5 text-[12px] text-culture">
                ⊕ Nhóm gộp nhiều lớp — khi nhóm học, mọi lớp thành viên đều bị
                chặn.
              </p>
            )}
          </div>
        </div>

        <footer className="flex gap-2 border-t border-border px-4 py-3">
          <Button variant="primary" onClick={() => void save()} disabled={busy}>
            {busy ? "Đang lưu…" : "Lưu"}
          </Button>
          {group && (
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

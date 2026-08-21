"use client";

import { useState } from "react";
import { Card, Note, PageHeader, Button } from "@/components/ui";
import { FeasibilityPanel } from "@/components/constraints/FeasibilityPanel";
import { SolverProgress } from "@/components/constraints/SolverProgress";
import { ScheduleSelector } from "@/components/ScheduleSelector";

/* Năm bước là một quy trình tuần tự, phụ thuộc nhau: phải ghim xong mới
   kiểm tra đúng năng lực còn lại, phải hết lỗi chặn mới chạy được bộ giải,
   phải có kết quả mới tinh chỉnh. Gộp vào một trang có thanh tiến trình để
   người dùng thấy mình đang ở đâu. */
const STEPS = [
  { key: "plan", n: 1, title: "Kế hoạch xếp", hint: "Thứ tự các lớp sẽ xếp" },
  { key: "pin", n: 2, title: "Xếp trước môn", hint: "Ghim tiết cố định" },
  { key: "check", n: 3, title: "Kiểm tra khả thi", hint: "Bắt lỗi trước khi chạy" },
  { key: "solve", n: 4, title: "Xếp lịch tự động", hint: "Bộ giải CP-SAT" },
  { key: "tune", n: 5, title: "Tinh chỉnh tay", hint: "Sửa thủ công" },
] as const;

/* Trung cấp và cao đẳng học nghề toàn thời gian nên cần xưởng nhiều nhất,
   phải giành xưởng trước hệ song bằng. */
const PLAN = [
  {
    n: 0,
    title: "Ghim cố định",
    desc: "Chào cờ thứ Hai tiết 1, tuần thực tập cao đẳng, tiết sinh hoạt",
    locked: "—",
    res: "Không chiếm xưởng",
  },
  {
    n: 1,
    title: "Trung cấp thường + Cao đẳng",
    desc: "Học nghề toàn thời gian nên cần xưởng nhiều nhất, giành xưởng trước",
    locked: "Lớp 0",
    res: "11 xưởng · 5 phòng máy",
  },
  {
    n: 2,
    title: "Văn hoá theo khối",
    desc: "Khối 10 sáng · khối 11 chiều · khối 12 cả ngày. Phòng cố định theo lớp",
    locked: "Lớp 0, 1",
    res: "31 phòng văn hoá",
  },
  {
    n: 3,
    title: "Nghề hệ song bằng 9+",
    desc: "Nhận ca bù của văn hoá, chia ca theo trần 18, dùng xưởng còn lại",
    locked: "Lớp 0, 1, 2",
    res: "Xưởng còn trống",
  },
];

export default function XepLichPage() {
  const [step, setStep] = useState(0);
  const [scheduleId, setScheduleId] = useState<number | null>(null);
  const [reload, setReload] = useState(0);
  const cur = STEPS[step];

  return (
    <>
      <PageHeader
        title="Xếp thời khoá biểu"
        subtitle="Quy trình năm bước. Bấm thẳng vào bước bất kỳ trên thanh, hoặc dùng nút chuyển bước."
      />

      <nav
        aria-label="Các bước xếp lịch"
        className="mb-4 flex overflow-x-auto rounded-lg border border-border bg-panel shadow-[var(--shadow)]"
      >
        {STEPS.map((s, i) => {
          const active = i === step;
          const done = i < step;
          return (
            <button
              key={s.key}
              onClick={() => setStep(i)}
              aria-current={active ? "step" : undefined}
              className={`flex min-w-[150px] flex-1 items-center gap-2.5 border-b-[3px] px-3.5 py-2.5 text-left transition-colors ${
                active
                  ? "border-b-vocational bg-vocational-bg"
                  : "border-b-transparent hover:bg-panel-2"
              } ${i < STEPS.length - 1 ? "border-r border-r-border" : ""}`}
            >
              <span
                className={`grid h-6 w-6 flex-none place-items-center rounded-full border font-mono text-[11px] font-semibold ${
                  active
                    ? "border-vocational bg-vocational text-white"
                    : done
                      ? "border-ok bg-ok text-white"
                      : "border-border-2 text-foreground-3"
                }`}
              >
                {done ? "✓" : s.n}
              </span>
              <span className="min-w-0">
                <b
                  className={`block whitespace-nowrap text-[13px] font-semibold ${
                    active ? "text-vocational" : ""
                  }`}
                >
                  {s.title}
                </b>
                <span className="block truncate text-[11px] text-foreground-3">
                  {s.hint}
                </span>
              </span>
            </button>
          );
        })}
      </nav>

      <Card title="Chọn phương án thời khoá biểu">
        <ScheduleSelector value={scheduleId} onChange={setScheduleId} />
      </Card>

      {cur.key === "plan" && (
        <Card title="Thứ tự xếp lịch" flush>
          <div className="p-4">
            <p className="mb-3 text-[13px] text-foreground-2">
              Không xếp cả trường trong một lần giải: giáo viên và xưởng dùng
              chung giữa các chương trình, xếp song song sẽ tranh nhau. Xong lớp
              nào thì <b>khoá lại</b> làm ràng buộc cho lớp sau.
            </p>
            {PLAN.map((p) => (
              <div
                key={p.n}
                className="mb-2 rounded-md border border-border-2 bg-panel-2 p-3 last:mb-0"
              >
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className="font-display text-[19px] font-bold text-vocational">
                    {p.n}
                  </span>
                  <b className="text-[13.5px]">{p.title}</b>
                </div>
                <p className="mt-1 pl-8 text-[12.5px] text-foreground-2">
                  {p.desc}
                </p>
                <div className="mt-1 flex flex-wrap gap-4 pl-8 text-[11.5px] text-foreground-3">
                  <span>
                    Bị khoá bởi: <b className="text-foreground-2">{p.locked}</b>
                  </span>
                  <span>
                    Tài nguyên: <b className="text-foreground-2">{p.res}</b>
                  </span>
                </div>
              </div>
            ))}
          </div>
          <div className="border-t border-border bg-panel-2 px-4 py-2.5 text-[11.5px] text-foreground-2">
            <b>Nguyên tắc:</b> nhóm tranh tài nguyên khan hiếm nhất xếp trước.
            Xưởng là nút thắt của trường, nên trung cấp và cao đẳng phải giành
            xưởng trước hệ song bằng.
          </div>
        </Card>
      )}

      {cur.key === "pin" && (
        <Card title="Ghim tiết cố định">
          <Note tone="muted" icon="📌">
            Những tiết cố định hằng tuần được ghim vào ô cụ thể trước, bộ giải
            giữ nguyên và xếp phần còn lại xung quanh.
            <div className="mt-1.5 border-t border-dashed border-current pt-1.5 text-[12px] opacity-90">
              Chào cờ thứ Hai 7h25 là sự kiện chặn toàn trường — bắt buộc ghim
              trước khi chạy.
            </div>
          </Note>
          <p className="mt-3 text-[13px] text-foreground-2">
            Ghim từng buổi ngay trên lưới thời khoá biểu: mở buổi cần ghim rồi
            chọn <b>Khoá tiết</b>.
          </p>
        </Card>
      )}

      {cur.key === "check" && (
        <>
          <Note tone="muted" icon="⚑">
            <b className="font-mono text-destructive">✕ Lỗi</b> phải sửa trước khi
            xếp — còn lỗi thì chắc chắn không ra được lịch.{" "}
            <b className="font-mono text-warn">! Cảnh báo</b> vẫn xếp được nhưng
            lịch sẽ kém.
          </Note>
          <FeasibilityPanel scheduleId={scheduleId} reloadToken={reload} />
        </>
      )}

      {cur.key === "solve" && (
        <>
          <Note tone="muted" icon="▶">
            Thường mất 2–10 phút. Có thể bấm <b>Dừng</b> bất cứ lúc nào — phương
            án đã tìm được vẫn giữ nguyên.
          </Note>
          <SolverProgress
            scheduleId={scheduleId}
            onSolved={() => setReload((n) => n + 1)}
          />
        </>
      )}

      {cur.key === "tune" && (
        <Card title="Tinh chỉnh thủ công">
          <Note tone="muted" icon="✋">
            Bốn phương pháp: đổi trực tiếp giữa hai giáo viên cùng nhóm, đổi qua
            giáo viên trung gian, đổi giữa hai hàng giáo viên, và xếp tay từ khay
            chờ.
          </Note>
          <p className="mt-3 text-[13px] text-foreground-2">
            Sang <b>Thời khoá biểu</b> để kéo thả tiết. Mọi thay đổi được lưu tự
            động và có thể hoàn tác.
          </p>
        </Card>
      )}

      <div className="mt-4 flex items-center gap-3 rounded-lg border border-border bg-panel px-4 py-3 shadow-[var(--shadow)]">
        <Button onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>
          ← Bước trước
        </Button>
        <span className="flex-1 text-center text-[12.5px] text-foreground-3">
          Bước {step + 1} / {STEPS.length} · {cur.title}
        </span>
        <Button
          variant="primary"
          onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}
          disabled={step === STEPS.length - 1}
        >
          Bước tiếp →
        </Button>
      </div>
    </>
  );
}

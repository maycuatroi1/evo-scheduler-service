"use client";

import { useMemo, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import {
  createApiClient,
  exportBlob,
  type CommitResult,
  type UploadSummary,
} from "@/lib/api";

const steps = [
  { id: 1, label: "Tải lên" },
  { id: 2, label: "Kiểm tra" },
  { id: 3, label: "Xác nhận" },
];

const severityBadge: Record<string, string> = {
  error: "bg-destructive/15 text-destructive",
  warning: "bg-warn-bg text-warn",
};

const severityLabel: Record<string, string> = {
  error: "lỗi",
  warning: "cảnh báo",
};

export function ImportWizard() {
  const { token } = useAuth();
  const api = useMemo(() => createApiClient(token), [token]);
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [summary, setSummary] = useState<UploadSummary | null>(null);
  const [commit, setCommit] = useState<CommitResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  const errorCount = summary?.errors_count ?? 0;
  const warningCount = summary?.warnings_count ?? 0;

  async function handleUpload(f: File) {
    setFile(f);
    setBusy(true);
    setError(null);
    setSummary(null);
    setCommit(null);
    try {
      const s = await api.uploadFile(f);
      setSummary(s);
      setStep(2);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không đọc được file");
    } finally {
      setBusy(false);
    }
  }

  async function handleCommit() {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const c = await api.commitFile(file);
      setCommit(c);
      setStep(3);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Commit thất bại");
    } finally {
      setBusy(false);
    }
  }

  async function handleTemplate() {
    setDownloading(true);
    setError(null);
    try {
      await exportBlob(api.templateUrl(), token, "import_template.xlsx");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không tải được mẫu");
    } finally {
      setDownloading(false);
    }
  }

  function handleReset() {
    setFile(null);
    setSummary(null);
    setCommit(null);
    setError(null);
    setStep(1);
  }

  if (!token) {
    return (
      <p className="text-sm text-foreground/60">
        Cần dán JWT token ở thanh trên cùng trước khi import.
      </p>
    );
  }

  if (commit) {
    const total = Object.values(commit.created).reduce((a, b) => a + b, 0);
    return (
      <div className="rounded-lg border border-accent/40 bg-accent/5 p-8 text-center">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-accent text-white">
          ✓
        </div>
        <h3 className="text-lg font-bold text-foreground">Import thành công</h3>
        <p className="mt-1 text-sm text-foreground/70">
          Đã ghi {total} bản ghi vào cơ sở dữ liệu.
        </p>
        <dl className="mx-auto mt-4 grid max-w-md grid-cols-2 gap-2 text-xs">
          {Object.entries(commit.created).map(([k, v]) => (
            <div
              key={k}
              className="rounded-md border border-border bg-background p-2"
            >
              <dt className="text-foreground/50">{k}</dt>
              <dd className="text-sm font-bold text-foreground">{v}</dd>
            </div>
          ))}
        </dl>
        <button
          type="button"
          onClick={handleReset}
          className="mt-4 rounded-md border border-border bg-panel px-4 py-2 text-sm font-semibold text-foreground hover:bg-border"
        >
          Import file khác
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ol className="flex items-center gap-2">
        {steps.map((s, idx) => {
          const isCurrent = s.id === step;
          const isDone = s.id < step;
          return (
            <li key={s.id} className="flex flex-1 items-center gap-2">
              <span
                className={
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold " +
                  (isCurrent
                    ? "bg-primary text-white"
                    : isDone
                      ? "bg-accent text-white"
                      : "border border-border bg-panel text-foreground/50")
                }
              >
                {isDone ? "✓" : s.id}
              </span>
              <span
                className={
                  "text-sm font-medium " +
                  (isCurrent ? "text-foreground" : "text-foreground/50")
                }
              >
                {s.label}
              </span>
              {idx < steps.length - 1 && (
                <span className="ml-2 hidden h-px flex-1 bg-border sm:block" />
              )}
            </li>
          );
        })}
      </ol>

      {step === 1 && (
        <section className="rounded-lg border border-border bg-panel p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">
              Tải lên file Excel
            </h3>
            <button
              type="button"
              onClick={handleTemplate}
              disabled={downloading}
              className="rounded-md border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-primary/10 disabled:opacity-50"
            >
              {downloading ? "Đang tải..." : "Tải file mẫu"}
            </button>
          </div>
          <p className="mt-1 text-xs text-foreground/60">
            Chấp nhận .xlsx. Dữ liệu sẽ gửi lên backend để kiểm tra.
          </p>
          <label
            htmlFor="file-input"
            className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed border-border bg-background px-6 py-10 text-center hover:border-primary"
          >
            <span className="text-2xl">📁</span>
            <span className="text-sm font-medium text-foreground">
              {file ? file.name : "Bấm để chọn file"}
            </span>
            <span className="text-xs text-foreground/50">
              {busy ? "Đang tải lên..." : "Chọn file .xlsx hợp lệ"}
            </span>
          </label>
          <input
            id="file-input"
            type="file"
            accept=".xlsx"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleUpload(f);
            }}
          />
        </section>
      )}

      {step === 2 && summary && (
        <section className="rounded-lg border border-border bg-panel p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">
              Kết quả kiểm tra
            </h3>
            <div className="flex gap-2 text-xs">
              <span
                className={
                  "rounded px-2 py-0.5 font-medium " + severityBadge.error
                }
              >
                {errorCount} lỗi
              </span>
              <span
                className={
                  "rounded px-2 py-0.5 font-medium " + severityBadge.warning
                }
              >
                {warningCount} cảnh báo
              </span>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
            {Object.entries(summary.row_counts).map(([sheet, count]) => (
              <div
                key={sheet}
                className="rounded-md border border-border bg-background p-2"
              >
                <p className="text-[11px] text-foreground/50">{sheet}</p>
                <p className="text-lg font-bold text-foreground">{count}</p>
              </div>
            ))}
          </div>

          {summary.issues.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-background text-foreground/60">
                    <th className="px-2 py-2 font-medium">Sheet</th>
                    <th className="px-2 py-2 font-medium">Dòng</th>
                    <th className="px-2 py-2 font-medium">Cột</th>
                    <th className="px-2 py-2 font-medium">Nội dung</th>
                    <th className="px-2 py-2 font-medium">Mức</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.issues.map((i, idx) => (
                    <tr key={idx} className="border-b border-border">
                      <td className="px-2 py-2 font-medium text-foreground">
                        {i.sheet}
                      </td>
                      <td className="px-2 py-2 text-foreground/70">{i.row}</td>
                      <td className="px-2 py-2 font-mono text-foreground/70">
                        {i.field}
                      </td>
                      <td className="px-2 py-2 text-foreground">{i.error}</td>
                      <td className="px-2 py-2">
                        <span
                          className={
                            "rounded px-1.5 py-0.5 font-medium capitalize " +
                            severityBadge[i.severity]
                          }
                        >
                          {severityLabel[i.severity]}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {errorCount > 0 ? (
            <p className="mt-3 text-xs font-medium text-destructive">
              Có {errorCount} lỗi, không thể commit. Sửa file rồi tải lại.
            </p>
          ) : (
            <p className="mt-3 text-xs text-accent">
              Không có lỗi, sẵn sàng commit vào cơ sở dữ liệu.
            </p>
          )}
        </section>
      )}

      {step === 3 && (
        <section className="rounded-lg border border-border bg-panel p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground">
            Xác nhận commit
          </h3>
          <p className="mt-1 text-xs text-foreground/60">
            File <span className="font-medium">{file?.name}</span> sẽ được ghi
            vào cơ sở dữ liệu của tenant.
          </p>
          <button
            type="button"
            onClick={handleCommit}
            disabled={busy}
            className="mt-4 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
          >
            {busy ? "Đang commit..." : "Commit import"}
          </button>
        </section>
      )}

      {error && (
        <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs font-medium text-destructive">
          {error}
        </p>
      )}

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={handleReset}
          disabled={busy}
          className="rounded-md border border-border bg-panel px-4 py-2 text-sm font-semibold text-foreground hover:bg-border disabled:opacity-40"
        >
          Làm lại
        </button>
        {step === 2 && (
          <button
            type="button"
            onClick={() => setStep(3)}
            disabled={errorCount > 0}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Tiếp theo
          </button>
        )}
      </div>
    </div>
  );
}

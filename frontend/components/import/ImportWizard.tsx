"use client";

import { useMemo, useState } from "react";
import { mappings, sheets, validationIssues } from "@/lib/mock/import";

const steps = [
  { id: 1, label: "Upload" },
  { id: 2, label: "Mapping" },
  { id: 3, label: "Validation" },
  { id: 4, label: "Commit" },
];

const severityBadge: Record<string, string> = {
  error: "bg-destructive/15 text-destructive",
  warning: "bg-amber-500/15 text-amber-700",
};

export function ImportWizard() {
  const [step, setStep] = useState(1);
  const [fileName, setFileName] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const errorCount = useMemo(
    () => validationIssues.filter((i) => i.severity === "error").length,
    [],
  );
  const warningCount = useMemo(
    () => validationIssues.filter((i) => i.severity === "warning").length,
    [],
  );

  const canAdvance = step !== 1 || fileName !== null;

  function handleNext() {
    if (!canAdvance) return;
    if (step < 4) setStep(step + 1);
  }
  function handleBack() {
    if (step > 1) setStep(step - 1);
  }
  function handleConfirm() {
    setDone(true);
  }
  function handleReset() {
    setDone(false);
    setFileName(null);
    setStep(1);
  }

  if (done) {
    return (
      <div className="rounded-lg border border-accent/40 bg-accent/5 p-8 text-center">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-accent text-white">
          ✓
        </div>
        <h3 className="text-lg font-bold text-foreground">Import committed</h3>
        <p className="mt-1 text-sm text-foreground/70">
          {sheets.length} sheets, {validationIssues.filter((i) => i.severity !== "error").length} rows committed, {errorCount} rows skipped.
        </p>
        <button
          type="button"
          onClick={handleReset}
          className="mt-4 rounded-md border border-border bg-white px-4 py-2 text-sm font-semibold text-foreground hover:bg-border dark:bg-slate-900"
        >
          Start a new import
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
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                  isCurrent
                    ? "bg-primary text-white"
                    : isDone
                      ? "bg-accent text-white"
                      : "border border-border bg-white text-foreground/50 dark:bg-slate-900"
                }`}
              >
                {isDone ? "✓" : s.id}
              </span>
              <span
                className={`text-sm font-medium ${isCurrent ? "text-foreground" : "text-foreground/50"}`}
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
        <section className="rounded-lg border border-border bg-white p-6 shadow-sm dark:bg-slate-900">
          <h3 className="text-sm font-semibold text-foreground">Upload Excel file</h3>
          <p className="mt-1 text-xs text-foreground/60">
            Accepts .xlsx, .xls, or .csv. No data is sent to the server in this prototype.
          </p>
          <label
            htmlFor="file-input"
            className="mt-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed border-border bg-background px-6 py-10 text-center hover:border-primary"
          >
            <span className="text-2xl">📁</span>
            <span className="text-sm font-medium text-foreground">
              {fileName ? fileName : "Click to choose a file"}
            </span>
            <span className="text-xs text-foreground/50">
              Mock upload: any file advances the wizard
            </span>
          </label>
          <input
            id="file-input"
            type="file"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              setFileName(f ? f.name : null);
            }}
          />
        </section>
      )}

      {step === 2 && (
        <section className="rounded-lg border border-border bg-white p-6 shadow-sm dark:bg-slate-900">
          <h3 className="text-sm font-semibold text-foreground">Column mapping</h3>
          <p className="mt-1 text-xs text-foreground/60">
            Headers auto-detected from <span className="font-medium">{fileName ?? "the uploaded file"}</span>. Review the matches before validation.
          </p>
          <div className="mt-4 space-y-4">
            {mappings.map((m) => (
              <div key={m.sheetId} className="rounded-md border border-border">
                <div className="flex items-center justify-between border-b border-border bg-background px-3 py-2">
                  <span className="text-sm font-semibold text-foreground">{m.sheetName}</span>
                  <span className="text-xs text-foreground/50">{m.detected.length} columns</span>
                </div>
                <ul className="divide-y divide-border">
                  {m.detected.map((d) => (
                    <li
                      key={`${m.sheetId}-${d.source}`}
                      className="grid grid-cols-12 items-center gap-2 px-3 py-2 text-xs"
                    >
                      <span className="col-span-4 truncate font-mono text-foreground/70">
                        {d.source}
                      </span>
                      <span className="col-span-1 text-center text-foreground/40">→</span>
                      <span className="col-span-4 truncate font-medium text-foreground">
                        {d.target}
                      </span>
                      <span className="col-span-3 text-right">
                        <span
                          className={`rounded px-1.5 py-0.5 ${
                            d.confidence >= 0.85
                              ? "bg-accent/15 text-accent"
                              : "bg-amber-500/15 text-amber-700"
                          }`}
                        >
                          {Math.round(d.confidence * 100)}%
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {step === 3 && (
        <section className="rounded-lg border border-border bg-white p-6 shadow-sm dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">Validation preview</h3>
            <div className="flex gap-2 text-xs">
              <span className={`rounded px-2 py-0.5 font-medium ${severityBadge.error}`}>
                {errorCount} errors
              </span>
              <span className={`rounded px-2 py-0.5 font-medium ${severityBadge.warning}`}>
                {warningCount} warnings
              </span>
            </div>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-border bg-background text-foreground/60">
                  <th className="px-2 py-2 font-medium">Sheet</th>
                  <th className="px-2 py-2 font-medium">Row</th>
                  <th className="px-2 py-2 font-medium">Column</th>
                  <th className="px-2 py-2 font-medium">Preview</th>
                  <th className="px-2 py-2 font-medium">Message</th>
                  <th className="px-2 py-2 font-medium">Level</th>
                </tr>
              </thead>
              <tbody>
                {validationIssues.map((i, idx) => (
                  <tr key={idx} className="border-b border-border">
                    <td className="px-2 py-2 font-medium text-foreground">{i.sheetName}</td>
                    <td className="px-2 py-2 text-foreground/70">{i.rowIndex}</td>
                    <td className="px-2 py-2 font-mono text-foreground/70">{i.column}</td>
                    <td className="px-2 py-2 font-mono text-foreground/70">{i.preview}</td>
                    <td className="px-2 py-2 text-foreground">{i.message}</td>
                    <td className="px-2 py-2">
                      <span
                        className={`rounded px-1.5 py-0.5 font-medium capitalize ${severityBadge[i.severity]}`}
                      >
                        {i.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-foreground/60">
            Rows marked <span className="font-semibold text-destructive">error</span> will be skipped on commit. Warnings are kept.
          </p>
        </section>
      )}

      {step === 4 && (
        <section className="rounded-lg border border-border bg-white p-6 shadow-sm dark:bg-slate-900">
          <h3 className="text-sm font-semibold text-foreground">Confirm commit</h3>
          <p className="mt-1 text-xs text-foreground/60">
            You are about to commit the staged import. Errors will be skipped automatically.
          </p>
          <dl className="mt-4 grid grid-cols-2 gap-3 text-xs">
            <div className="rounded-md border border-border bg-background p-3">
              <dt className="text-foreground/50">Source file</dt>
              <dd className="mt-1 truncate font-medium text-foreground">
                {fileName ?? "(no file)"}
              </dd>
            </div>
            <div className="rounded-md border border-border bg-background p-3">
              <dt className="text-foreground/50">Sheets</dt>
              <dd className="mt-1 font-medium text-foreground">{sheets.length}</dd>
            </div>
            <div className="rounded-md border border-border bg-background p-3">
              <dt className="text-foreground/50">Rows to commit</dt>
              <dd className="mt-1 font-medium text-accent">
                {validationIssues.filter((i) => i.severity !== "error").length}
              </dd>
            </div>
            <div className="rounded-md border border-border bg-background p-3">
              <dt className="text-foreground/50">Rows to skip</dt>
              <dd className="mt-1 font-medium text-destructive">{errorCount}</dd>
            </div>
          </dl>
          <button
            type="button"
            onClick={handleConfirm}
            className="mt-4 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
          >
            Commit import
          </button>
        </section>
      )}

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={handleBack}
          disabled={step === 1}
          className="rounded-md border border-border bg-white px-4 py-2 text-sm font-semibold text-foreground hover:bg-border disabled:cursor-not-allowed disabled:opacity-40 dark:bg-slate-900"
        >
          Back
        </button>
        {step < 4 && (
          <button
            type="button"
            onClick={handleNext}
            disabled={!canAdvance}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
          </button>
        )}
      </div>

      <section className="rounded-lg border border-border bg-white p-6 shadow-sm dark:bg-slate-900">
        <h3 className="text-sm font-semibold text-foreground">Staged sheet preview</h3>
        <p className="mt-1 text-xs text-foreground/60">
          First rows of each of the {sheets.length} detected sheets.
        </p>
        <div className="mt-4 space-y-4">
          {sheets.map((s) => (
            <div key={s.id} className="rounded-md border border-border">
              <div className="border-b border-border bg-background px-3 py-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-foreground">{s.name}</span>
                  <span className="text-xs text-foreground/50">{s.description}</span>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-left text-xs">
                  <thead>
                    <tr className="border-b border-border bg-background/50 text-foreground/60">
                      {s.columns.map((c) => (
                        <th key={c.key} className="px-2 py-2 font-medium">
                          {c.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {s.rows.map((row, ri) => (
                      <tr key={ri} className="border-b border-border last:border-0">
                        {row.map((cell, ci) => (
                          <td key={ci} className="px-2 py-2 text-foreground/80">
                            {String(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

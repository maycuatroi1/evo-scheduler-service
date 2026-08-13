"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ScheduleGrid } from "@/components/schedule/ScheduleGrid";
import { ScheduleSelector } from "@/components/ScheduleSelector";
import { useAuth } from "@/components/providers/AuthProvider";
import {
  createApiClient,
  exportBlob,
  toGridSessions,
  type Conflict,
  type MoveSessionResponse,
  type SessionRow,
} from "@/lib/api";

export default function SchedulePage() {
  const { token } = useAuth();
  const [scheduleId, setScheduleId] = useState<number | null>(null);
  const [rows, setRows] = useState<SessionRow[]>([]);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const api = useMemo(() => createApiClient(token), [token]);

  const load = useCallback(async () => {
    if (!token || scheduleId === null) {
      setRows([]);
      setConflicts([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [sess, conf] = await Promise.all([
        api.getSessions(scheduleId),
        api.getConflicts(scheduleId),
      ]);
      setRows(sess);
      setConflicts(conf);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tải lịch");
      setRows([]);
      setConflicts([]);
    } finally {
      setLoading(false);
    }
  }, [token, scheduleId, api]);

  useEffect(() => {
    load();
  }, [load]);

  const gridSessions = useMemo(() => toGridSessions(rows), [rows]);

  async function handleMove(
    sessionId: string,
    day: number,
    period: number,
    currentRoom: string,
  ): Promise<MoveSessionResponse> {
    if (scheduleId === null) {
      throw new Error("Chua chon lich");
    }
    return api.moveSession(
      Number(sessionId),
      scheduleId,
      day,
      period,
      currentRoom || undefined,
    );
  }

  async function handleExport() {
    if (scheduleId === null) return;
    setExporting(true);
    setError(null);
    try {
      await exportBlob(api.exportUrl(scheduleId), token, "schedule.xlsx");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi xuất file");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Lưới lịch</h2>
          <p className="text-sm text-foreground/60">
            Xem lịch thật từ backend theo giáo viên, lớp, phòng.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ScheduleSelector value={scheduleId} onChange={setScheduleId} />
          <button
            type="button"
            onClick={handleExport}
            disabled={scheduleId === null || exporting || rows.length === 0}
            className="rounded-md bg-accent px-4 py-1.5 text-xs font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {exporting ? "Đang xuất..." : "Xuất Excel"}
          </button>
        </div>
      </div>
      <ScheduleGrid
        scheduleId={scheduleId}
        sessions={gridSessions}
        conflicts={conflicts}
        loading={loading}
        error={error}
        onRefresh={load}
        onMove={handleMove}
      />
    </div>
  );
}

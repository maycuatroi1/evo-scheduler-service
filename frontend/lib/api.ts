import type { Session } from "@/lib/mock/schedule";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8888/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export type Teacher = { code: string; name: string };

export type ScheduleSummary = {
  id: number;
  name: string;
  status: string;
  tier: string | null;
  objective_value: number | null;
};

export type SessionRow = {
  id: number;
  module_code: string;
  module_name: string;
  student_group_code: string;
  student_group_name: string;
  session_type: "theory" | "practice";
  tier: string | null;
  duration_slots: number;
  is_locked: boolean;
  day: number | null;
  period: number | null;
  day_name: string | null;
  resource_code: string | null;
  teachers: Teacher[];
};

export type SessionsResponse = {
  schedule_id: number;
  sessions: SessionRow[];
};

export type Conflict = {
  type: "teacher" | "room" | "student_group";
  session_ids: [number, number];
  day: number;
  period: number;
  day_name: string;
  detail: string | null;
};

export type ConflictsResponse = {
  schedule_id: number;
  conflicts: Conflict[];
};

export type SolveTierResult = {
  tier: string;
  status: string;
  objective_value: number;
  num_sessions: number;
  num_assignments: number;
  violations?: string[];
};

export type SolveResponse = {
  solve_job_id: string;
  schedule_id: number;
  status: string;
};

export type SolveJobStatus = {
  job_id: string;
  schedule_id: number;
  status: string;
  phase: string | null;
  progress: number;
  objective_value: number | null;
  error: string;
  metrics: {
    tier_mode?: string;
    conflicts?: number;
    violations?: string[];
    num_assignments?: number;
    tier_results?: SolveTierResult[];
  };
};

export type Weights = {
  idle_teacher: number;
  room_change: number;
  compact_schedule: number;
  teacher_load_balance: number;
};

export type WeightsResponse = { schedule_id: number; weights: Weights };

export type ValidationIssue = {
  row: number;
  sheet: string;
  field: string;
  error: string;
  severity: "error" | "warning";
};

export type UploadSummary = {
  row_counts: Record<string, number>;
  issues: ValidationIssue[];
  errors_count: number;
  warnings_count: number;
  sample: Record<string, unknown[]>;
};

export type CommitResult = {
  created: Record<string, number>;
  issues: ValidationIssue[];
};

export type StatsResponse = {
  tenant_code: string;
  counts: {
    teachers: number;
    student_groups: number;
    resources: number;
    modules: number;
    sessions: number;
    sessions_assigned: number;
  };
  completion: number;
  weekly_load: { day: string; load: number }[];
  schedules: ScheduleSummary[];
};

export type ChangedSession = {
  session_id: number;
  old_day: number | null;
  old_period: number | null;
  old_resource: string | null;
  new_day: number;
  new_period: number;
  new_resource: string;
  is_dragged: boolean;
};

export type MoveSessionResponse = {
  changed_sessions: ChangedSession[];
  unchanged_session_ids: number[];
  unchanged_count: number;
  objective_value: number;
  status: string;
  wall_time: number;
  dragged_session_id: number | null;
};

export type ApiClient = {
  listTeachers: () => Promise<Teacher[]>;
  listSchedules: () => Promise<ScheduleSummary[]>;
  createSchedule: (name: string, tier?: string) => Promise<ScheduleSummary>;
  getSessions: (scheduleId: number) => Promise<SessionRow[]>;
  getConflicts: (scheduleId: number) => Promise<Conflict[]>;
  solve: (scheduleId: number) => Promise<SolveResponse>;
  solveJobStatus: (jobId: string) => Promise<SolveJobStatus>;
  getWeights: (scheduleId: number) => Promise<Weights>;
  putWeights: (scheduleId: number, weights: Weights) => Promise<Weights>;
  uploadFile: (file: File) => Promise<UploadSummary>;
  commitFile: (file: File) => Promise<CommitResult>;
  templateUrl: () => string;
  exportUrl: (scheduleId: number) => string;
  getStats: () => Promise<StatsResponse>;
  moveSession: (
    sessionId: number,
    scheduleId: number,
    newDay: number,
    newPeriod: number,
    newResource?: string,
  ) => Promise<MoveSessionResponse>;
};

export type AuthUser = { id: string; email: string; name: string };

export type AuthResult = {
  token: string;
  user: AuthUser;
  tenant_id: number;
};

export async function authRegister(input: {
  name: string;
  email: string;
  password: string;
}): Promise<AuthResult> {
  const res = await fetch(API_URL + "/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as AuthResult;
}

export async function authLogin(input: {
  email: string;
  password: string;
}): Promise<AuthResult> {
  const res = await fetch(API_URL + "/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as AuthResult;
}

async function parseError(res: Response): Promise<ApiError> {
  let message = "Lỗi %s".replace("%s", String(res.status));
  try {
    const data = await res.json();
    if (data?.detail) message = String(data.detail);
    else if (data?.message) message = String(data.message);
    else if (typeof data === "string") message = data;
  } catch {
    if (res.status === 401) message = "Phiên đăng nhập hết hạn";
    else if (res.status === 403) message = "Không có quyền truy cập";
  }
  return new ApiError(res.status, message);
}

function authHeaders(token: string | null): HeadersInit {
  return token ? { Authorization: "Bearer " + token } : {};
}

export function createApiClient(token: string | null): ApiClient {
  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(API_URL + path, {
      ...init,
      headers: {
        ...authHeaders(token),
        ...(init?.headers ?? {}),
      },
    });
    if (!res.ok) throw await parseError(res);
    if (res.status === 204) return undefined as T;
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) return (await res.json()) as T;
    return (await res.text()) as unknown as T;
  }

  return {
    async listTeachers() {
      return request<Teacher[]>("/teachers");
    },
    async listSchedules() {
      return request<ScheduleSummary[]>("/schedule");
    },
    async createSchedule(name, tier) {
      return request<ScheduleSummary>("/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, tier: tier ?? null }),
      });
    },
    async getSessions(scheduleId) {
      const data = await request<SessionsResponse>(
        "/schedule/" + scheduleId + "/sessions",
      );
      return data.sessions;
    },
    async getConflicts(scheduleId) {
      const data = await request<ConflictsResponse>(
        "/schedule/" + scheduleId + "/conflicts",
      );
      return data.conflicts;
    },
    async solve(scheduleId) {
      return request<SolveResponse>(
        "/schedule/" + scheduleId + "/solve",
        { method: "POST" },
      );
    },
    async solveJobStatus(jobId) {
      return request<SolveJobStatus>("/solve/" + jobId + "/status");
    },
    async getWeights(scheduleId) {
      const data = await request<WeightsResponse>(
        "/schedule/" + scheduleId + "/weights",
      );
      return data.weights;
    },
    async putWeights(scheduleId, weights) {
      const data = await request<WeightsResponse>(
        "/schedule/" + scheduleId + "/weights",
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ weights }),
        },
      );
      return data.weights;
    },
    async uploadFile(file) {
      const form = new FormData();
      form.append("file", file);
      return request<UploadSummary>("/import/upload", {
        method: "POST",
        body: form,
      });
    },
    async commitFile(file) {
      const form = new FormData();
      form.append("file", file);
      return request<CommitResult>("/import/commit", { method: "POST", body: form });
    },
    templateUrl() {
      return API_URL + "/import/template";
    },
    exportUrl(scheduleId) {
      return (
        API_URL +
        "/schedule/" +
        scheduleId +
        "/export?format=xlsx"
      );
    },
    async getStats() {
      return request<StatsResponse>("/stats");
    },
    async moveSession(sessionId, scheduleId, newDay, newPeriod, newResource) {
      return request<MoveSessionResponse>(
        "/sessions/" + sessionId + "/move",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            schedule_id: scheduleId,
            new_day: newDay,
            new_period: newPeriod,
            new_resource: newResource ?? null,
          }),
        },
      );
    },
  };
}

export type GridSession = Session;

export function toGridSession(row: SessionRow): GridSession {
  const teacher = row.teachers[0];
  return {
    id: String(row.id),
    moduleCode: row.module_code,
    moduleName: row.module_name,
    teacherCode: teacher?.code ?? "",
    teacherName: teacher?.name ?? "(chưa phân GV)",
    classCode: row.student_group_code,
    room: row.resource_code ?? "",
    type: row.session_type === "practice" ? "TH" : "LT",
    day: row.day ?? -1,
    period: row.period ?? -1,
    tier: row.tier,
    teachers: row.teachers,
    className: row.student_group_name,
    duration: row.duration_slots,
    locked: row.is_locked,
    dayName: row.day_name,
  };
}

export function toGridSessions(rows: SessionRow[]): GridSession[] {
  return rows
    .filter((r) => r.day !== null && r.period !== null)
    .map(toGridSession);
}

export function distinctTeachers(rows: SessionRow[]): Teacher[] {
  const seen = new Map<string, Teacher>();
  for (const r of rows) {
    for (const t of r.teachers) {
      if (!seen.has(t.code)) seen.set(t.code, t);
    }
  }
  return [...seen.values()];
}

export function distinctValues(rows: SessionRow[], key: "student_group_code" | "resource_code"): string[] {
  const seen = new Set<string>();
  for (const r of rows) {
    const v = r[key];
    if (v) seen.add(v);
  }
  return [...seen];
}

export async function exportBlob(
  url: string,
  token: string | null,
  filename: string,
): Promise<void> {
  const res = await fetch(url, {
    headers: authHeaders(token),
  });
  if (!res.ok) throw await parseError(res);
  const blob = await res.blob();
  const objUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(objUrl);
}

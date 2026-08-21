/* Client cho API nghiệp vụ trường nghề ở /api/v2.
   Tách khỏi lib/api.ts để phần cũ không phình thêm. */

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8888/api";
const V2 = API_URL + "/v2";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.errors) && data.errors.length)
      return String(data.errors[0]);
    if (typeof data?.message === "string") return data.message;
  } catch {
    /* trả thông báo mặc định bên dưới */
  }
  if (res.status === 401) return "Phiên đăng nhập hết hạn";
  if (res.status === 403) return "Bạn không có quyền thực hiện thao tác này";
  return `Lỗi ${res.status}`;
}

async function req<T>(
  token: string,
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const res = await fetch(V2 + path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init.headers || {}),
    },
  });
  if (!res.ok) throw new ApiError(await parseError(res), res.status);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/* ---------- Kiểu dữ liệu ---------- */

export type Shift = "morning" | "afternoon" | "full_day";

export type Homeroom = {
  id: number;
  code: string;
  name: string;
  grade: number | null;
  size: number;
  culture_shift: Shift;
  vocational_shift: Shift;
  room_id: number | null;
  group_count: number;
};

export type Group = {
  id: number;
  code: string;
  name: string;
  enrollment_type: string;
  size: number;
  occupation: string;
  hazardous: boolean;
  homeroom_codes: string[];
  practice_batches: number;
};

export type TeacherFull = {
  id: number;
  code: string;
  name: string;
  blocks: string[];
  quota_standard_hours: number | null;
  moet_code: string;
  email: string;
  department_id: number | null;
  campus_id: number | null;
  max_periods_per_session: number | null;
  min_periods_per_session: number | null;
  days_off_per_week: number | null;
};

export type WorkloadRow = {
  code: string;
  name: string;
  department_id: number | null;
  theory_periods: number;
  practice_periods: number;
  standard_hours: number;
  quota: number;
  over: number;
  usage_pct: number;
};

export type Rule = {
  id: number;
  type: string;
  scope_json: Record<string, unknown>;
  params_json: Record<string, unknown>;
  hardness: string;
  priority: "high" | "medium" | "low";
  weight: number;
  active: boolean;
  effective_weight: number;
};

export type Version = {
  id: number;
  name: string;
  status: string;
  is_manual_edit: boolean;
  inherited_from: number | null;
  week_number: number | null;
  objective_value: number | null;
  unplaced_count: number;
  published_at: string | null;
};

export type InheritDiff = {
  schedule_id: number;
  base_id: number;
  changed: {
    teacher_code: string;
    teacher_name: string;
    added_modules: string[];
    removed_modules: string[];
    old_count: number;
    new_count: number;
  }[];
  unchanged_count: number;
  total_teachers: number;
  keep_pct: number;
};

export type BellPeriod = { period: number; start: string; end: string };

export type Resource = {
  id: number;
  code: string;
  name: string;
  type: string;
  capacity: number;
  quantity: number;
  available_quantity: number;
};

export type RoomUsage = {
  code: string;
  name: string;
  type: string;
  capacity: number;
  quantity: number;
  periods_used: number;
  slots_available: number;
  usage_pct: number;
};

export type Campus = {
  id: number;
  code: string;
  name: string;
  address: string;
  travel_minutes: number;
};

export type Department = {
  id: number;
  code: string;
  name: string;
  parent_id: number | null;
};

/* ---------- Client ---------- */

export function createV2(token: string) {
  const get = <T,>(p: string) => req<T>(token, p);
  const post = <T,>(p: string, body?: unknown) =>
    req<T>(token, p, { method: "POST", body: JSON.stringify(body ?? {}) });
  const put = <T,>(p: string, body: unknown) =>
    req<T>(token, p, { method: "PUT", body: JSON.stringify(body) });
  const del = <T,>(p: string) => req<T>(token, p, { method: "DELETE" });

  return {
    // Lớp văn hoá
    listHomerooms: (grade?: number) =>
      get<Homeroom[]>("/homerooms" + (grade ? `?grade=${grade}` : "")),
    createHomeroom: (b: Partial<Homeroom>) => post<Homeroom>("/homerooms", b),
    updateHomeroom: (id: number, b: Partial<Homeroom>) =>
      put<Homeroom>(`/homerooms/${id}`, b),
    deleteHomeroom: (id: number) => del(`/homerooms/${id}`),
    homeroomSplit: (id: number) =>
      get<{
        homeroom: string;
        declared_size: number;
        group_count: number;
        total_in_groups: number;
        is_split: boolean;
        groups: { code: string; name: string; size: number }[];
      }>(`/homerooms/${id}/split`),

    // Nhóm nghề
    listGroups: (homeroom?: string) =>
      get<Group[]>("/groups" + (homeroom ? `?homeroom=${homeroom}` : "")),
    createGroup: (b: Partial<Group> & { homeroom_ids?: number[] }) =>
      post<Group>("/groups", b),
    updateGroup: (id: number, b: Partial<Group> & { homeroom_ids?: number[] }) =>
      put<Group>(`/groups/${id}`, b),
    deleteGroup: (id: number) => del(`/groups/${id}`),

    // Giáo viên
    listTeachers: (department?: number) =>
      get<TeacherFull[]>(
        "/teachers/full" + (department ? `?department=${department}` : "")
      ),
    createTeacher: (b: Partial<TeacherFull>) => post<TeacherFull>("/teachers", b),
    updateTeacher: (id: number, b: Partial<TeacherFull>) =>
      put<TeacherFull>(`/teachers/${id}`, b),
    deleteTeacher: (id: number) => del(`/teachers/${id}`),
    workload: () =>
      get<{ teachers: WorkloadRow[]; count: number }>("/reports/teacher-workload"),

    // Ràng buộc
    listRules: (type?: string) =>
      get<Rule[]>("/rules" + (type ? `?type=${type}` : "")),
    createRule: (b: Partial<Rule>) => post<Rule>("/rules", b),
    updateRule: (id: number, b: Partial<Rule>) => put<Rule>(`/rules/${id}`, b),
    deleteRule: (id: number) => del(`/rules/${id}`),
    setPriority: (id: number, priority: string, weight?: number) =>
      put<Rule>(`/rules/${id}/priority`, { priority, weight }),

    // Ghim tiết
    listPins: (scheduleId: number) =>
      get<{ schedule_id: number; pins: unknown[] }>(
        `/schedule/${scheduleId}/pins`
      ),
    addPin: (scheduleId: number, b: { session_id: number; day: number; period: number }) =>
      post(`/schedule/${scheduleId}/pins`, b),
    removePin: (scheduleId: number, sessionId: number) =>
      del(`/schedule/${scheduleId}/pins/${sessionId}`),

    // Kế thừa và xuất bản
    versions: () => get<{ versions: Version[]; count: number }>("/schedule/versions"),
    inheritDiff: (scheduleId: number, baseId: number) =>
      get<InheritDiff>(`/schedule/${scheduleId}/inherit-diff?base_id=${baseId}`),
    inherit: (scheduleId: number, baseId: number, keepLevel: string) =>
      post<{ copied: number; to_resolve: number }>(
        `/schedule/${scheduleId}/inherit`,
        { base_id: baseId, keep_level: keepLevel }
      ),
    publish: (scheduleId: number) =>
      post<{ status: string; published_at: string; unplaced_count: number }>(
        `/schedule/${scheduleId}/publish`
      ),

    // Mốc giờ
    getBellTimes: () =>
      get<{
        config: Record<string, unknown>;
        periods: { morning: BellPeriod[]; afternoon: BellPeriod[] };
      }>("/tenant/bell-times"),
    setBellTimes: (b: Record<string, unknown>) =>
      put<{
        config: Record<string, unknown>;
        periods: { morning: BellPeriod[]; afternoon: BellPeriod[] };
      }>("/tenant/bell-times", b),

    // Phòng, xưởng
    listResources: (type?: string) =>
      get<Resource[]>("/resources" + (type ? `?type=${type}` : "")),
    createResource: (b: Partial<Resource>) => post<Resource>("/resources", b),
    updateResource: (id: number, b: Partial<Resource>) =>
      put<Resource>(`/resources/${id}`, b),
    deleteResource: (id: number) => del(`/resources/${id}`),
    roomUsage: (scheduleId?: number) =>
      get<{ rooms: RoomUsage[]; total_slots_per_room: number }>(
        "/reports/room-usage" + (scheduleId ? `?schedule_id=${scheduleId}` : "")
      ),

    // Tổ chức
    listCampuses: () => get<Campus[]>("/campuses"),
    listDepartments: () => get<Department[]>("/departments"),
  };
}

export type V2Client = ReturnType<typeof createV2>;

export const SHIFT_LABEL: Record<Shift, string> = {
  morning: "Sáng",
  afternoon: "Chiều",
  full_day: "Cả ngày",
};

export const PRIORITY_LABEL: Record<string, string> = {
  high: "Cao",
  medium: "Trung bình",
  low: "Thấp",
};

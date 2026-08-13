import { teachers, classes, rooms } from "./schedule";

export type ConstraintType =
  | "unavailability"
  | "resource_requirement"
  | "capacity_limit"
  | "quota_limit"
  | "preference"
  | "exclusion"
  | "adjacency"
  | "distribution";

export type ConstraintMode = "hard" | "soft";

export type ConstraintStatus = "active" | "inactive";

export type ConstraintTemplate = {
  type: ConstraintType;
  label: string;
  description: string;
  entityLabel: string;
  paramLabel: string;
  paramKind: "day" | "period_range" | "quantity" | "resource" | "day_count";
};

export const constraintTemplates: ConstraintTemplate[] = [
  {
    type: "unavailability",
    label: "Không khả dụng",
    description: "Giáo viên, lớp hoặc phòng không xếp vào khung đã chọn.",
    entityLabel: "Đối tượng",
    paramLabel: "Ngày nghỉ",
    paramKind: "day",
  },
  {
    type: "resource_requirement",
    label: "Yêu cầu tài nguyên",
    description: "Buổi học cần phòng/xưởng chuyên dụng.",
    entityLabel: "Lớp học",
    paramLabel: "Phòng yêu cầu",
    paramKind: "resource",
  },
  {
    type: "capacity_limit",
    label: "Giới hạn sức chứa",
    description: "Số lượng sinh viên tối đa trong phòng.",
    entityLabel: "Phòng",
    paramLabel: "Sức chứa tối đa",
    paramKind: "quantity",
  },
  {
    type: "quota_limit",
    label: "Định mức",
    description: "Số buổi tối đa cho mỗi đối tượng trong ngày.",
    entityLabel: "Giáo viên",
    paramLabel: "Số buổi / ngày",
    paramKind: "quantity",
  },
  {
    type: "preference",
    label: "Ưu tiên",
    description: "Đối tượng mong muốn xếp vào khung giờ này.",
    entityLabel: "Giáo viên",
    paramLabel: "Khung tiết ưu tiên",
    paramKind: "period_range",
  },
  {
    type: "exclusion",
    label: "Loại trừ",
    description: "Hai đối tượng không xếp cùng một khung.",
    entityLabel: "Đối tượng A",
    paramLabel: "Đối tượng B loại trừ",
    paramKind: "resource",
  },
  {
    type: "adjacency",
    label: "Liền kề",
    description: "Các buổi của đối tượng phải xếp liền nhau.",
    entityLabel: "Lớp học",
    paramLabel: "Số buổi liền kề",
    paramKind: "quantity",
  },
  {
    type: "distribution",
    label: "Phân bổ",
    description: "Trải đều các buổi trong số ngày đã chọn.",
    entityLabel: "Lớp học",
    paramLabel: "Số ngày phân bổ",
    paramKind: "day_count",
  },
];

export const weekDays = [
  { index: 0, code: "T2", label: "Thứ 2" },
  { index: 1, code: "T3", label: "Thứ 3" },
  { index: 2, code: "T4", label: "Thứ 4" },
  { index: 3, code: "T5", label: "Thứ 5" },
  { index: 4, code: "T6", label: "Thứ 6" },
  { index: 5, code: "T7", label: "Thứ 7" },
];

export const periodOptions = [
  { value: "1", label: "Tiết 1" },
  { value: "2", label: "Tiết 2" },
  { value: "3", label: "Tiết 3" },
  { value: "4", label: "Tiết 4" },
  { value: "5", label: "Tiết 5" },
  { value: "6", label: "Tiết 6" },
];

export type EntityGroup = {
  id: string;
  label: string;
  options: { value: string; label: string }[];
};

export const entityGroups: EntityGroup[] = [
  {
    id: "teacher",
    label: "Giáo viên",
    options: teachers.map((t) => ({ value: t.code, label: `${t.code} - ${t.name}` })),
  },
  {
    id: "class",
    label: "Lớp học",
    options: classes.map((c) => ({ value: c, label: c })),
  },
  {
    id: "room",
    label: "Phòng",
    options: rooms.map((r) => ({ value: r, label: r })),
  },
];

export type CreatedConstraint = {
  id: string;
  type: ConstraintType;
  typeLabel: string;
  entity: string;
  param: string;
  mode: ConstraintMode;
  weight: number;
  status: ConstraintStatus;
  summary: string;
};

export const seedConstraints: CreatedConstraint[] = [
  {
    id: "C-001",
    type: "unavailability",
    typeLabel: "Không khả dụng",
    entity: "GV-ĐE01 - Nguyễn Văn A",
    param: "Thứ 7",
    mode: "hard",
    weight: 10,
    status: "active",
    summary: "GV Nguyễn Văn A không dạy thứ 7",
  },
  {
    id: "C-002",
    type: "quota_limit",
    typeLabel: "Định mức",
    entity: "GV-ĐE02 - Trần Thị B",
    param: "4 buổi / ngày",
    mode: "soft",
    weight: 6,
    status: "active",
    summary: "GV Trần Thị B dạy tối đa 4 buổi / ngày",
  },
  {
    id: "C-003",
    type: "capacity_limit",
    typeLabel: "Giới hạn sức chứa",
    entity: "Xưởng Điện 1",
    param: "30 sinh viên",
    mode: "hard",
    weight: 10,
    status: "inactive",
    summary: "Xưởng Điện 1 chứa tối đa 30 sinh viên",
  },
];

export type SolverMetrics = {
  sessionsPlaced: number;
  sessionsTotal: number;
  remainingConflicts: number;
  objectiveValue: number;
};

export const finalSolverMetrics: SolverMetrics = {
  sessionsPlaced: 124,
  sessionsTotal: 128,
  remainingConflicts: 2,
  objectiveValue: 4820,
};

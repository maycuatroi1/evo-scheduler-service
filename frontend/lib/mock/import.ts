export type Column = {
  key: string;
  label: string;
};

export type Sheet = {
  id: string;
  name: string;
  description: string;
  columns: Column[];
  rows: (string | number)[][];
};

export const sheets: Sheet[] = [
  {
    id: "teachers",
    name: "Teachers",
    description: "Instructor roster and qualifications",
    columns: [
      { key: "code", label: "Code" },
      { key: "name", label: "Name" },
      { key: "email", label: "Email" },
      { key: "modules", label: "Modules" },
    ],
    rows: [
      ["GV001", "Nguyễn Thị Lan", "lan.nt@evo.edu.vn", "Math, Stats"],
      ["GV002", "Trần Văn Minh", "minh.tv@evo.edu.vn", "Physics"],
      ["GV003", "Lê Hoàng Phúc", "phuc.lh@evo.edu.vn", "Chemistry, Bio"],
    ],
  },
  {
    id: "student-groups",
    name: "StudentGroups",
    description: "Class cohorts and headcounts",
    columns: [
      { key: "group", label: "Group" },
      { key: "size", label: "Size" },
      { key: "grade", label: "Grade" },
    ],
    rows: [
      ["10A", 32, "Grade 10"],
      ["10B", 30, "Grade 10"],
      ["11C", 28, "Grade 11"],
    ],
  },
  {
    id: "resources",
    name: "Resources",
    description: "Rooms and equipment",
    columns: [
      { key: "room", label: "Room" },
      { key: "type", label: "Type" },
      { key: "capacity", label: "Capacity" },
    ],
    rows: [
      ["R101", "Lecture", 40],
      ["LabA", "Lab", 24],
      ["WS-B", "Workshop", 18],
    ],
  },
  {
    id: "modules",
    name: "Modules",
    description: "Course modules and weekly hours",
    columns: [
      { key: "code", label: "Code" },
      { key: "title", label: "Title" },
      { key: "hours", label: "Hours/Week" },
    ],
    rows: [
      ["MATH-1", "Algebra I", 4],
      ["PHYS-2", "Mechanics", 3],
      ["CHEM-1", "Organic", 3],
    ],
  },
  {
    id: "teacher-module",
    name: "TeacherModule",
    description: "Teacher to module assignments",
    columns: [
      { key: "teacher", label: "Teacher" },
      { key: "module", label: "Module" },
      { key: "priority", label: "Priority" },
    ],
    rows: [
      ["GV001", "MATH-1", "Primary"],
      ["GV002", "PHYS-2", "Primary"],
      ["GV003", "CHEM-1", "Secondary"],
    ],
  },
  {
    id: "fixed-sessions",
    name: "FixedSessions",
    description: "Pinned sessions that must not move",
    columns: [
      { key: "day", label: "Day" },
      { key: "slot", label: "Slot" },
      { key: "group", label: "Group" },
      { key: "room", label: "Room" },
    ],
    rows: [
      ["Mon", "S1", "10A", "R101"],
      ["Wed", "S3", "11C", "LabA"],
      ["Fri", "S2", "10B", "WS-B"],
    ],
  },
];

export type Mapping = {
  sheetId: string;
  sheetName: string;
  detected: { source: string; target: string; confidence: number }[];
};

export const mappings: Mapping[] = sheets.map((s) => ({
  sheetId: s.id,
  sheetName: s.name,
  detected: s.columns.map((c) => ({
    source: c.label.toLowerCase().replace(/\s+/g, "_"),
    target: c.key,
    confidence: c.label === "Capacity" ? 0.71 : 0.93,
  })),
}));

export type Severity = "error" | "warning";

export type ValidationIssue = {
  sheetName: string;
  rowIndex: number;
  column: string;
  severity: Severity;
  message: string;
  preview: string;
};

export const validationIssues: ValidationIssue[] = [
  {
    sheetName: "Teachers",
    rowIndex: 3,
    column: "email",
    severity: "error",
    message: "Invalid email format",
    preview: "phuc.lh@",
  },
  {
    sheetName: "StudentGroups",
    rowIndex: 2,
    column: "size",
    severity: "warning",
    message: "Class size exceeds room capacity of 30",
    preview: "32",
  },
  {
    sheetName: "Resources",
    rowIndex: 1,
    column: "capacity",
    severity: "warning",
    message: "Workshop capacity below recommended 20",
    preview: "18",
  },
  {
    sheetName: "TeacherModule",
    rowIndex: 4,
    column: "teacher",
    severity: "error",
    message: "Unknown teacher code",
    preview: "GV099",
  },
  {
    sheetName: "FixedSessions",
    rowIndex: 6,
    column: "room",
    severity: "error",
    message: "Room does not exist in Resources",
    preview: "R999",
  },
  {
    sheetName: "Modules",
    rowIndex: 2,
    column: "hours",
    severity: "warning",
    message: "Hours exceed weekly budget",
    preview: "9",
  },
];

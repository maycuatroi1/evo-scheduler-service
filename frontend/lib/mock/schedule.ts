export type SessionType = "LT" | "TH";

export type Session = {
  id: string;
  moduleCode: string;
  moduleName: string;
  teacherCode: string;
  teacherName: string;
  classCode: string;
  room: string;
  type: SessionType;
  day: number;
  period: number;
};

export const days = [
  { index: 0, code: "T2", label: "Mon" },
  { index: 1, code: "T3", label: "Tue" },
  { index: 2, code: "T4", label: "Wed" },
  { index: 3, code: "T5", label: "Thu" },
  { index: 4, code: "T6", label: "Fri" },
];

export const periods = [
  { index: 1, label: "Tiết 1" },
  { index: 2, label: "Tiết 2" },
  { index: 3, label: "Tiết 3" },
  { index: 4, label: "Tiết 4" },
  { index: 5, label: "Tiết 5" },
  { index: 6, label: "Tiết 6" },
];

export const teachers = [
  { code: "GV-ĐE01", name: "Nguyễn Văn A" },
  { code: "GV-ĐE02", name: "Trần Thị B" },
  { code: "GV-ĐE03", name: "Lê Hoàng Phúc" },
  { code: "GV-ĐE04", name: "Phạm Thu Hà" },
  { code: "GV-ĐE05", name: "Vũ Đức Anh" },
];

export const classes = ["ĐT11A", "ĐT11B", "ĐT12A", "ĐT12B", "ĐT13A"];

const lectureRooms = ["P.201", "P.202"];
const workshops = ["Xưởng Điện 1", "Xưởng Điện 2", "Xưởng CNC"];
export const rooms = [...lectureRooms, ...workshops];

const modulePool: { code: string; name: string; type: SessionType }[] = [
  { code: "ĐE-101", name: "Cơ điện tử", type: "LT" },
  { code: "ĐE-102", name: "Mạch điện tử", type: "LT" },
  { code: "ĐE-103", name: "PLC cơ bản", type: "TH" },
  { code: "ĐE-201", name: "Hệ thống điều khiển", type: "LT" },
  { code: "ĐE-202", name: "Kỹ thuật số", type: "LT" },
  { code: "ĐE-203", name: "Điện công nghiệp", type: "TH" },
  { code: "ĐE-301", name: "PLC nâng cao", type: "TH" },
  { code: "ĐE-302", name: "Robot công nghiệp", type: "TH" },
  { code: "ĐE-303", name: "Cảm biến và đo lường", type: "LT" },
  { code: "ĐE-304", name: "An toàn điện", type: "LT" },
];

function buildSessions(): Session[] {
  const out: Session[] = [];
  classes.forEach((classCode, c) => {
    modulePool.forEach((mod, i) => {
      const roomPool = mod.type === "TH" ? workshops : lectureRooms;
      const teacher = teachers[(c + i) % teachers.length];
      const room = roomPool[(c + i) % roomPool.length];
      const day = i % 5;
      const period = i < 5 ? 1 + (c % 3) : 4 + (c % 3);
      out.push({
        id: `S-${classCode}-${mod.code}`,
        moduleCode: mod.code,
        moduleName: mod.name,
        teacherCode: teacher.code,
        teacherName: teacher.name,
        classCode,
        room,
        type: mod.type,
        day,
        period,
      });
    });
  });
  return out;
}

export const sessions: Session[] = buildSessions();

export function isConflict(list: Session[], extra?: Session): boolean {
  const merged = extra ? [...list, extra] : list;
  for (let i = 0; i < merged.length; i++) {
    for (let j = i + 1; j < merged.length; j++) {
      if (
        merged[i].teacherCode === merged[j].teacherCode ||
        merged[i].room === merged[j].room
      ) {
        return true;
      }
    }
  }
  return false;
}

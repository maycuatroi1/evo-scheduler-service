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

export function isConflict(list: Session[], extra?: Session): boolean {
  const merged = extra ? [...list, extra] : list;
  for (let i = 0; i < merged.length; i++) {
    for (let j = i + 1; j < merged.length; j++) {
      if (
        (merged[i].teacherCode && merged[i].teacherCode === merged[j].teacherCode) ||
        (merged[i].room && merged[i].room === merged[j].room) ||
        (merged[i].classCode && merged[i].classCode === merged[j].classCode)
      ) {
        return true;
      }
    }
  }
  return false;
}

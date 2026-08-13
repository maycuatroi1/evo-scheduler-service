class BuildContext:
    def __init__(self, model, data):
        self.model = model
        self.data = data
        self.horizon = data["horizon"]
        self.num_timeslots = len(self.horizon)
        self.sessions = data["sessions"]
        self.resources = data["resources"]
        self.teachers = data.get("teachers", [])
        self.hours_per_slot = data.get("hours_per_slot", 1.0)
        self.resources_by_code = {r["code"]: r for r in self.resources}
        self.resources_by_id = {r["id"]: r for r in self.resources}
        self.sessions_by_id = {s["id"]: s for s in self.sessions}
        self.sessions_by_teacher = {}
        for s in self.sessions:
            for code in s.get("teacher_codes", []):
                self.sessions_by_teacher.setdefault(code, []).append(s)
        self.sessions_by_group = {}
        for s in self.sessions:
            grp = s.get("group_code")
            if grp is not None:
                self.sessions_by_group.setdefault(grp, []).append(s)
        self.day_names = [ts.get("day_name", "") for ts in self.horizon]
        self.teacher_module_map = data.get("teacher_module_map", {})
        self.X = {}
        self.Y = {}
        self.eligible_teachers = {}
        self.occ = {}
        self.start_timeslot = {}
        self.start_period = {}
        self.start_day = {}
        self.valid_starts = {}
        self.candidate_resources = {}
        self.soft_records = []

    def record_soft(self, rule, violation_var, detail=""):
        self.soft_records.append((rule, violation_var, detail))

    def horizon_index(self, day, period):
        for i, ts in enumerate(self.horizon):
            if ts["day"] == day and ts["period"] == period:
                return i
        return None

    def timeslots_for_day(self, day_name):
        out = []
        for i, ts in enumerate(self.horizon):
            if str(ts.get("day_name", "")).lower() == str(day_name).lower():
                out.append(i)
        return out

    def timeslots_for_period_in(self, periods):
        out = []
        for i, ts in enumerate(self.horizon):
            if ts["period"] in periods:
                out.append(i)
        return out

    def morning_indices(self):
        return [i for i, ts in enumerate(self.horizon) if ts.get("is_morning")]

    def covers(self, start_t, duration):
        return list(range(start_t, start_t + duration))

    def same_day_run(self, start_t, duration):
        if start_t < 0 or start_t + duration - 1 >= self.num_timeslots:
            return False
        day = self.horizon[start_t]["day"]
        for k in range(1, duration):
            if self.horizon[start_t + k]["day"] != day:
                return False
        return True

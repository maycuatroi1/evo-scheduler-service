class OccupancyTable:
    """Bảng "buổi sid có chiếm tiết p không", dựng biến khi được hỏi.

    Mô hình không tạo sẵn |buổi| x |tiết| biến vì phần lớn cặp không luật nào
    chạm tới. Các module ràng buộc vẫn dùng ``ctx.occ.get(...)`` như cũ.
    """

    def __init__(self, ctx):
        self._ctx = ctx
        self._cache = {}

    def _build(self, sid, p):
        ctx = self._ctx
        session = ctx.sessions_by_id.get(sid)
        if session is None:
            return None
        duration = int(session.get("duration_slots", 1) or 1)
        terms = [
            ctx.start_lit[(sid, t)]
            for t in ctx.valid_starts.get(sid, [])
            if (sid, t) in ctx.start_lit and p in ctx.covers(t, duration)
        ]
        var = ctx.model.NewBoolVar("occ_%s_%s" % (sid, p))
        if terms:
            ctx.model.Add(var == sum(terms))
        else:
            ctx.model.Add(var == 0)
        return var

    def get(self, key, default=None):
        if key in self._cache:
            return self._cache[key]
        sid, p = key
        if sid not in self._ctx.sessions_by_id:
            return default
        if not 0 <= int(p) < self._ctx.num_timeslots:
            return default
        var = self._build(sid, p)
        if var is None:
            return default
        self._cache[key] = var
        return var

    def __getitem__(self, key):
        var = self.get(key)
        if var is None:
            raise KeyError(key)
        return var

    def __contains__(self, key):
        return self.get(key) is not None

    def __len__(self):
        return len(self._cache)


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
        # Buổi sid bắt đầu ở tiết t.
        self.start_lit = {}
        # Buổi sid dùng tài nguyên rcode.
        self.assign = {}
        # Khoảng thời gian của buổi, dùng cho các ràng buộc không chồng lấn.
        self.interval = {}
        self.res_interval = {}
        self.teacher_interval = {}
        self.Y = {}
        self.eligible_teachers = {}
        self.occ = OccupancyTable(self)
        self.start_timeslot = {}
        self.start_period = {}
        self.start_day = {}
        self.valid_starts = {}
        self.candidate_resources = {}
        self.soft_records = []
        self._on_day = {}
        self._resource_capacity_done = False
        # Lý do khiến mô hình chắc chắn vô nghiệm, phát hiện lúc dựng biến.
        self.blockers = []
        # Chỗ dữ liệu đã được nới để giải tiếp, cần báo lại cho người dùng.
        self.warnings = []

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

    def enforce_resource_capacity(self):
        """Một tài nguyên không phục vụ quá số lượng sẵn có tại cùng thời điểm.

        Luật shared_resource_pool và bước dựng mô hình cùng cần ràng buộc này;
        cờ nội bộ giữ cho nó chỉ được thêm một lần.
        """
        if self._resource_capacity_done:
            return
        self._resource_capacity_done = True
        by_resource = {}
        for (sid, rcode), iv in self.res_interval.items():
            by_resource.setdefault(rcode, []).append(iv)
        for r in self.resources:
            intervals = by_resource.get(r["code"])
            if not intervals:
                continue
            quantity = int(r.get("available_quantity", 1) or 1)
            if quantity <= 1:
                self.model.AddNoOverlap(intervals)
            else:
                self.model.AddCumulative(intervals, [1] * len(intervals), quantity)

    def on_day(self, sid, day):
        """Buổi sid có nằm trong ngày day không. Dựng lười như occ."""
        key = (sid, day)
        if key in self._on_day:
            return self._on_day[key]
        terms = [
            self.start_lit[(sid, t)]
            for t in self.valid_starts.get(sid, [])
            if (sid, t) in self.start_lit and self.horizon[t]["day"] == day
        ]
        var = self.model.NewBoolVar("onday_%s_%s" % (sid, day))
        if terms:
            self.model.Add(var == sum(terms))
        else:
            self.model.Add(var == 0)
        self._on_day[key] = var
        return var

    def solution_for(self, solver, sid):
        """Tiết bắt đầu và tài nguyên đã chọn của một buổi, hoặc (None, None)."""
        chosen_t = None
        for t in self.valid_starts.get(sid, []):
            lit = self.start_lit.get((sid, t))
            if lit is not None and solver.Value(lit) == 1:
                chosen_t = t
                break
        chosen_r = None
        for rcode in self.candidate_resources.get(sid, []):
            lit = self.assign.get((sid, rcode))
            if lit is not None and solver.Value(lit) == 1:
                chosen_r = rcode
                break
        return chosen_t, chosen_r

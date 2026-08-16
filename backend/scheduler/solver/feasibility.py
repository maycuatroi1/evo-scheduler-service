"""Kiểm tra tính khả thi của dữ liệu trước khi dựng mô hình CP-SAT.

CP-SAT chỉ trả về INFEASIBLE mà không chỉ ra thực thể nào gây mâu thuẫn, và
với vài trăm buổi học thì phải chờ hết time limit mới biết. Các vi phạm ở đây
là vi phạm số học: không tồn tại cách xếp nào thoả mãn, nên phát hiện trước
khi gọi solver vừa nhanh vừa nói được chính xác phải sửa gì.
"""

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

# Loại tài nguyên dùng được cho mỗi loại buổi học.
COMPAT = {
    "theory": ("theory_room",),
    "practice": ("workshop", "tool_set"),
}

RESOURCE_LABELS = {
    "theory_room": "phòng lý thuyết",
    "workshop": "xưởng",
    "tool_set": "bộ dụng cụ",
}

# Số thực thể được liệt kê chi tiết cho mỗi loại lỗi trước khi gộp phần còn lại.
MAX_DETAILED = 10


def _issue(code, message, severity=SEVERITY_ERROR, **detail):
    out = {"code": code, "severity": severity, "message": message}
    out.update(detail)
    return out


def _resource_label(types):
    labels = [RESOURCE_LABELS.get(t, t) for t in types]
    return " hoặc ".join(labels) if labels else "tài nguyên"


def allowed_resource_types(session):
    return COMPAT.get(session.get("session_type"), ())


def resource_fits(resource, session):
    """Tài nguyên có dùng được cho buổi học này không.

    Sức chứa 0 nghĩa là không khai báo giới hạn (bộ dụng cụ), không phải
    sức chứa bằng không.
    """
    allowed = allowed_resource_types(session)
    if allowed and str(resource.get("type", "")).lower() not in allowed:
        return False
    capacity = int(resource.get("capacity", 0) or 0)
    if capacity > 0 and capacity < int(session.get("group_size", 0) or 0):
        return False
    return True


def candidate_resources(resources, session):
    """Danh sách mã tài nguyên hợp lệ cho một buổi học.

    Trả về rỗng khi không có tài nguyên nào phù hợp; nơi gọi phải tự quyết
    định coi đó là lỗi hay dùng phương án dự phòng.
    """
    return [r["code"] for r in resources if resource_fits(r, session)]


def longest_same_day_run(horizon):
    """Số tiết liên tiếp dài nhất nằm trọn trong một ngày."""
    best = 0
    current = 0
    previous = None
    for ts in horizon:
        key = (ts.get("week", 0), ts.get("day"))
        if key == previous:
            current += 1
        else:
            current = 1
            previous = key
        if current > best:
            best = current
    return best


def _session_label(session):
    code = session.get("code") or session.get("id")
    group = session.get("group_code")
    if group:
        return "%s (lớp %s)" % (code, group)
    return str(code)


def _overload_issues(loads, capacity, code, noun, unit="tiết mỗi tuần"):
    issues = []
    over = sorted(
        ((key, value) for key, value in loads.items() if value > capacity),
        key=lambda kv: -kv[1],
    )
    for key, value in over[:MAX_DETAILED]:
        issues.append(
            _issue(
                code,
                "%s %s cần %d %s nhưng thời khoá biểu chỉ có %d tiết."
                % (noun, key, value, unit, capacity),
                entity=key,
                required=value,
                available=capacity,
            )
        )
    if len(over) > MAX_DETAILED:
        issues.append(
            _issue(
                code,
                "Còn %d %s khác cũng vượt quá %d tiết mỗi tuần."
                % (len(over) - MAX_DETAILED, noun.lower(), capacity),
                overflow=len(over) - MAX_DETAILED,
            )
        )
    return issues


def _check_horizon(horizon, resources, sessions):
    issues = []
    if not horizon:
        issues.append(
            _issue(
                "empty_horizon",
                "Thời khoá biểu không có tiết nào. Hãy khai báo số ngày và số tiết mỗi ngày.",
            )
        )
    if not resources:
        issues.append(
            _issue(
                "no_resources",
                "Chưa khai báo phòng học hay thiết bị nào nên không xếp được buổi nào.",
            )
        )
    if not sessions:
        issues.append(
            _issue(
                "no_sessions",
                "Không có buổi học nào để xếp.",
                severity=SEVERITY_WARNING,
            )
        )
    return issues


def _check_session_duration(sessions, horizon):
    max_run = longest_same_day_run(horizon)
    too_long = [
        s for s in sessions if int(s.get("duration_slots", 1) or 1) > max_run
    ]
    issues = []
    for s in too_long[:MAX_DETAILED]:
        issues.append(
            _issue(
                "session_too_long",
                "Buổi %s dài %d tiết liên tục nhưng ngày học dài nhất chỉ có %d tiết."
                % (
                    _session_label(s),
                    int(s.get("duration_slots", 1) or 1),
                    max_run,
                ),
                session_code=s.get("code"),
                required=int(s.get("duration_slots", 1) or 1),
                available=max_run,
            )
        )
    if len(too_long) > MAX_DETAILED:
        issues.append(
            _issue(
                "session_too_long",
                "Còn %d buổi khác dài hơn %d tiết của một ngày học."
                % (len(too_long) - MAX_DETAILED, max_run),
                overflow=len(too_long) - MAX_DETAILED,
            )
        )
    return issues


def _check_group_load(sessions, num_timeslots):
    loads = {}
    for s in sessions:
        group = s.get("group_code")
        if not group:
            continue
        loads[group] = loads.get(group, 0) + int(s.get("duration_slots", 1) or 1)
    return _overload_issues(loads, num_timeslots, "group_overloaded", "Lớp")


def _forced_teacher(session, teacher_module_map):
    """Giáo viên chắc chắn phải dạy buổi này.

    Buổi đã gán cứng thì lấy danh sách đó; buổi chưa gán mà môn chỉ có đúng
    một giáo viên đủ điều kiện thì giáo viên đó cũng là bắt buộc.
    """
    assigned = session.get("teacher_codes") or []
    if assigned:
        return list(assigned)
    eligible = teacher_module_map.get(session.get("module_code")) or []
    if len(eligible) == 1:
        return list(eligible)
    return []


def _check_teacher_load(sessions, teacher_module_map, num_timeslots):
    loads = {}
    for s in sessions:
        duration = int(s.get("duration_slots", 1) or 1)
        for code in _forced_teacher(s, teacher_module_map):
            loads[code] = loads.get(code, 0) + duration
    return _overload_issues(
        loads, num_timeslots, "teacher_overloaded", "Giáo viên"
    )


def _teacher_groups(sessions, teacher_module_map):
    """Gom giáo viên thành nhóm khi họ dùng chung một rổ buổi học.

    Buổi chưa gán giáo viên được solver phân cho một người trong nhóm đủ điều
    kiện, nên năng lực phải tính theo cả nhóm chứ không theo từng người.
    """
    parent = {}

    def find(code):
        parent.setdefault(code, code)
        while parent[code] != code:
            parent[code] = parent[parent[code]]
            code = parent[code]
        return code

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    free = []
    for s in sessions:
        if s.get("teacher_codes"):
            continue
        eligible = teacher_module_map.get(s.get("module_code")) or []
        if not eligible:
            continue
        free.append((s, eligible))
        for code in eligible[1:]:
            union(eligible[0], code)

    groups = {}
    for s, eligible in free:
        root = find(eligible[0])
        group = groups.setdefault(root, {"teachers": set(), "demand": 0})
        group["teachers"].update(eligible)
        group["demand"] += int(s.get("duration_slots", 1) or 1)
    return groups


def _check_teacher_pool(sessions, teacher_module_map, num_timeslots):
    """Năng lực của cả nhóm giáo viên so với số tiết nhóm đó phải gánh."""
    fixed_load = {}
    for s in sessions:
        duration = int(s.get("duration_slots", 1) or 1)
        for code in s.get("teacher_codes") or []:
            fixed_load[code] = fixed_load.get(code, 0) + duration

    issues = []
    for group in _teacher_groups(sessions, teacher_module_map).values():
        teachers = sorted(group["teachers"])
        if len(teachers) < 2:
            # Một người là trường hợp đã được báo chi tiết ở _check_teacher_load.
            continue
        demand = group["demand"] + sum(fixed_load.get(c, 0) for c in teachers)
        capacity = len(teachers) * num_timeslots
        if demand <= capacity:
            continue
        listed = ", ".join(teachers[:5])
        if len(teachers) > 5:
            listed += " và %d người nữa" % (len(teachers) - 5)
        issues.append(
            _issue(
                "teacher_pool_overloaded",
                "Nhóm %d giáo viên (%s) phải dạy %d tiết mỗi tuần nhưng tối đa "
                "chỉ được %d tiết (%d giáo viên x %d tiết)."
                % (
                    len(teachers),
                    listed,
                    demand,
                    capacity,
                    len(teachers),
                    num_timeslots,
                ),
                teachers=teachers,
                required=demand,
                available=capacity,
            )
        )
    return issues


def _check_teacher_coverage(sessions, teacher_module_map):
    uncovered = {}
    for s in sessions:
        if s.get("teacher_codes"):
            continue
        module = s.get("module_code")
        if teacher_module_map.get(module):
            continue
        uncovered[module] = uncovered.get(module, 0) + 1
    issues = []
    for module, count in sorted(uncovered.items(), key=lambda kv: -kv[1])[:MAX_DETAILED]:
        issues.append(
            _issue(
                "module_without_teacher",
                "Môn %s không có giáo viên nào đủ điều kiện; %d buổi sẽ xếp mà không có giáo viên."
                % (module, count),
                severity=SEVERITY_WARNING,
                entity=module,
                sessions=count,
            )
        )
    return issues


def _check_resource_match(sessions, resources):
    missing = {}
    for s in sessions:
        if candidate_resources(resources, s):
            continue
        key = (
            s.get("session_type"),
            int(s.get("group_size", 0) or 0),
            s.get("group_code"),
        )
        missing.setdefault(key, []).append(s)
    issues = []
    for (session_type, size, group), group_sessions in list(missing.items())[:MAX_DETAILED]:
        issues.append(
            _issue(
                "no_matching_resource",
                "Lớp %s (%d học sinh) có %d buổi %s nhưng không %s nào đủ sức chứa."
                % (
                    group,
                    size,
                    len(group_sessions),
                    "lý thuyết" if session_type == "theory" else "thực hành",
                    _resource_label(COMPAT.get(session_type, ())),
                ),
                entity=group,
                session_type=session_type,
                group_size=size,
                sessions=len(group_sessions),
            )
        )
    if len(missing) > MAX_DETAILED:
        issues.append(
            _issue(
                "no_matching_resource",
                "Còn %d nhóm buổi khác không tìm được phòng hay thiết bị phù hợp."
                % (len(missing) - MAX_DETAILED),
                overflow=len(missing) - MAX_DETAILED,
            )
        )
    return issues


def _check_resource_pool(sessions, resources, num_timeslots):
    """Tổng số tiết cần của mỗi nhóm tài nguyên so với sức chứa cả tuần."""
    demand = {}
    for s in sessions:
        allowed = allowed_resource_types(s)
        if not allowed:
            continue
        demand[allowed] = demand.get(allowed, 0) + int(
            s.get("duration_slots", 1) or 1
        )
    issues = []
    for allowed, needed in sorted(demand.items(), key=lambda kv: -kv[1]):
        supply = sum(
            int(r.get("available_quantity", 1) or 1)
            for r in resources
            if str(r.get("type", "")).lower() in allowed
        )
        capacity = supply * num_timeslots
        if needed <= capacity:
            continue
        issues.append(
            _issue(
                "resource_pool_overloaded",
                "Cần %d tiết %s mỗi tuần nhưng chỉ có %d chỗ (%d đơn vị x %d tiết)."
                % (
                    needed,
                    _resource_label(allowed),
                    capacity,
                    supply,
                    num_timeslots,
                ),
                resource_types=list(allowed),
                required=needed,
                available=capacity,
            )
        )
    return issues


def _check_capacity_levels(sessions, resources, num_timeslots):
    """Sức chứa phải đủ ở từng ngưỡng sĩ số, không chỉ đủ tổng.

    Lớp đông chỉ vào được phòng lớn, nên tổng số chỗ đủ vẫn có thể vô nghiệm
    khi phòng lớn quá ít. Đây là điều kiện Hall áp cho từng ngưỡng sĩ số.
    """
    demand = {}
    for s in sessions:
        allowed = allowed_resource_types(s)
        if not allowed:
            continue
        demand.setdefault(allowed, []).append(s)

    issues = []
    for allowed, group_sessions in demand.items():
        pool = [
            r for r in resources if str(r.get("type", "")).lower() in allowed
        ]
        thresholds = sorted(
            {int(r.get("capacity", 0) or 0) for r in pool if int(r.get("capacity", 0) or 0) > 0}
        )
        worst = None
        for threshold in thresholds:
            needed = sum(
                int(s.get("duration_slots", 1) or 1)
                for s in group_sessions
                if int(s.get("group_size", 0) or 0) > threshold
            )
            if not needed:
                continue
            supply = sum(
                int(r.get("available_quantity", 1) or 1)
                for r in pool
                if int(r.get("capacity", 0) or 0) == 0
                or int(r.get("capacity", 0) or 0) > threshold
            )
            capacity = supply * num_timeslots
            if needed <= capacity:
                continue
            gap = needed - capacity
            if worst is None or gap > worst[3]:
                worst = (threshold, needed, capacity, gap, supply)
        if worst is None:
            continue
        threshold, needed, capacity, gap, supply = worst
        issues.append(
            _issue(
                "resource_capacity_shortage",
                "Các lớp trên %d học sinh cần %d tiết %s mỗi tuần nhưng chỉ có "
                "%d chỗ đủ sức chứa (%d đơn vị x %d tiết), thiếu %d tiết."
                % (
                    threshold,
                    needed,
                    _resource_label(allowed),
                    capacity,
                    supply,
                    num_timeslots,
                    gap,
                ),
                resource_types=list(allowed),
                threshold=threshold,
                required=needed,
                available=capacity,
            )
        )
    return issues


def _check_locked(sessions, horizon, resources):
    """Buổi đã khoá phải trỏ vào một tiết và một tài nguyên có thật."""
    num_timeslots = len(horizon)
    codes = {r["code"] for r in resources}
    issues = []
    for s in sessions:
        slot = s.get("assigned_timeslot")
        if not (s.get("is_locked") and slot):
            continue
        index = slot.get("index") if isinstance(slot, dict) else slot
        duration = int(s.get("duration_slots", 1) or 1)
        label = _session_label(s)
        if not isinstance(index, int) or index < 0 or index >= num_timeslots:
            issues.append(
                _issue(
                    "locked_slot_invalid",
                    "Buổi %s bị khoá vào tiết không tồn tại trong thời khoá biểu."
                    % label,
                    session_code=s.get("code"),
                )
            )
            continue
        end = index + duration - 1
        if end >= num_timeslots or horizon[end].get("day") != horizon[index].get("day"):
            issues.append(
                _issue(
                    "locked_slot_invalid",
                    "Buổi %s bị khoá vào tiết %d nhưng %d tiết liên tục sẽ tràn sang ngày khác."
                    % (label, index, duration),
                    session_code=s.get("code"),
                )
            )
            continue
        rcode = s.get("assigned_resource_code")
        if rcode and rcode not in codes:
            issues.append(
                _issue(
                    "locked_resource_missing",
                    "Buổi %s bị khoá vào tài nguyên %s không còn trong danh sách."
                    % (label, rcode),
                    session_code=s.get("code"),
                    entity=rcode,
                )
            )
    return issues


def check(data):
    """Trả về danh sách vấn đề của bộ dữ liệu, nặng nhất trước."""
    horizon = data.get("horizon") or []
    sessions = data.get("sessions") or []
    resources = data.get("resources") or []
    teacher_module_map = data.get("teacher_module_map") or {}
    num_timeslots = len(horizon)

    issues = _check_horizon(horizon, resources, sessions)
    if not horizon or not sessions:
        return issues

    issues.extend(_check_session_duration(sessions, horizon))
    issues.extend(_check_group_load(sessions, num_timeslots))
    issues.extend(
        _check_teacher_load(sessions, teacher_module_map, num_timeslots)
    )
    issues.extend(
        _check_teacher_pool(sessions, teacher_module_map, num_timeslots)
    )
    issues.extend(_check_resource_pool(sessions, resources, num_timeslots))
    if resources:
        issues.extend(
            _check_capacity_levels(sessions, resources, num_timeslots)
        )
        issues.extend(_check_resource_match(sessions, resources))
        issues.extend(_check_locked(sessions, horizon, resources))
    issues.extend(_check_teacher_coverage(sessions, teacher_module_map))
    return issues


def blocking(issues):
    return [i for i in issues if i.get("severity") == SEVERITY_ERROR]


def messages(issues):
    return [i["message"] for i in issues]

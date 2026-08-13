from scheduler.excel_parser import to_float, to_int, to_list, to_str

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

ENROLLMENT_TYPES = {"dual_degree", "college"}
RESOURCE_TYPES = {"theory_room", "workshop", "tool_set"}
SESSION_TYPES = {"theory", "practice"}
TIERS = {"culture", "vocational"}
BLOCKS = {"culture", "vocational", "both"}


def _issue(row, sheet, field, error, severity=SEVERITY_ERROR):
    return {
        "row": row,
        "sheet": sheet,
        "field": field,
        "error": error,
        "severity": severity,
    }


def _collect_codes(rows, key="code"):
    codes = set()
    for r in rows:
        value = to_str(r.get(key))
        if value:
            codes.add(value)
    return codes


def _validate_required(row_num, sheet, field, value, issues):
    text = to_str(value)
    if not text:
        issues.append(
            _issue(row_num, sheet, field, "%s is required" % field)
        )
        return False
    return True


def _validate_enum(row_num, sheet, field, value, valid, issues, required=False):
    text = to_str(value)
    if not text:
        if required:
            issues.append(_issue(row_num, sheet, field, "%s is required" % field))
            return False
        return True
    if text.lower() not in valid:
        issues.append(
            _issue(
                row_num,
                sheet,
                field,
                "invalid %s '%s' (allowed: %s)" % (field, text, ", ".join(sorted(valid))),
            )
        )
        return False
    return True


def _validate_int(row_num, sheet, field, value, issues, required=False, min_value=None):
    if value is None or value == "":
        if required:
            issues.append(_issue(row_num, sheet, field, "%s is required" % field))
            return None
        return None
    iv = to_int(value)
    if iv is None:
        issues.append(_issue(row_num, sheet, field, "%s must be an integer" % field))
        return None
    if min_value is not None and iv < min_value:
        issues.append(
            _issue(row_num, sheet, field, "%s must be >= %s" % (field, min_value))
        )
    return iv


def _validate_float(row_num, sheet, field, value, issues, required=False, min_value=None):
    if value is None or value == "":
        if required:
            issues.append(_issue(row_num, sheet, field, "%s is required" % field))
            return None
        return None
    fv = to_float(value)
    if fv is None:
        issues.append(_issue(row_num, sheet, field, "%s must be numeric" % field))
        return None
    if min_value is not None and fv < min_value:
        issues.append(
            _issue(row_num, sheet, field, "%s must be >= %s" % (field, min_value))
        )
    return fv


def _validate_fk(row_num, sheet, field, value, known_codes, issues, required=False):
    text = to_str(value)
    if not text:
        if required:
            issues.append(_issue(row_num, sheet, field, "%s is required" % field))
            return False
        return True
    if text not in known_codes:
        issues.append(
            _issue(
                row_num,
                sheet,
                field,
                "%s '%s' does not reference a known code" % (field, text),
            )
        )
        return False
    return True


def validate(parsed):
    issues = []

    for missing in parsed.get("_missing_sheets", []):
        issues.append(
            _issue(
                0,
                missing,
                "_sheet",
                "sheet '%s' not found in workbook" % missing,
                severity=SEVERITY_WARNING,
            )
        )

    teacher_codes = _collect_codes(parsed["Teachers"])
    sg_codes = _collect_codes(parsed["StudentGroups"])
    resource_codes = _collect_codes(parsed["Resources"])
    module_codes = _collect_codes(parsed["Modules"])

    _validate_teachers(parsed["Teachers"], issues)
    _validate_student_groups(parsed["StudentGroups"], sg_codes, issues)
    _validate_resources(parsed["Resources"], resource_codes, issues)
    _validate_modules(parsed["Modules"], sg_codes, module_codes, issues)
    _validate_teacher_modules(parsed["TeacherModule"], teacher_codes, module_codes, issues)
    _validate_fixed_sessions(
        parsed["FixedSessions"],
        module_codes,
        sg_codes,
        resource_codes,
        teacher_codes,
        issues,
    )
    return issues


def _validate_teachers(rows, issues):
    seen = set()
    for r in rows:
        row_num = r["row"]
        code = to_str(r.get("code"))
        ok_code = _validate_required(row_num, "Teachers", "code", code, issues)
        _validate_required(row_num, "Teachers", "name", r.get("name"), issues)
        if ok_code:
            if code in seen:
                issues.append(
                    _issue(row_num, "Teachers", "code", "duplicate teacher code '%s'" % code)
                )
            seen.add(code)
        blocks = to_list(r.get("blocks"))
        for b in blocks:
            if b.lower() not in BLOCKS:
                issues.append(
                    _issue(row_num, "Teachers", "blocks", "invalid block '%s'" % b)
                )
        if r.get("quota_standard_hours") not in (None, ""):
            _validate_float(
                row_num,
                "Teachers",
                "quota_standard_hours",
                r.get("quota_standard_hours"),
                issues,
                min_value=0,
            )


def _validate_student_groups(rows, sg_codes, issues):
    seen = set()
    for r in rows:
        row_num = r["row"]
        code = to_str(r.get("code"))
        ok_code = _validate_required(row_num, "StudentGroups", "code", code, issues)
        _validate_required(row_num, "StudentGroups", "name", r.get("name"), issues)
        _validate_enum(
            row_num,
            "StudentGroups",
            "enrollment_type",
            r.get("enrollment_type"),
            ENROLLMENT_TYPES,
            issues,
            required=True,
        )
        _validate_int(
            row_num,
            "StudentGroups",
            "size",
            r.get("size"),
            issues,
            min_value=0,
        )
        if ok_code:
            if code in seen:
                issues.append(
                    _issue(row_num, "StudentGroups", "code", "duplicate code '%s'" % code)
                )
            seen.add(code)


def _validate_resources(rows, resource_codes, issues):
    seen = set()
    for r in rows:
        row_num = r["row"]
        code = to_str(r.get("code"))
        ok_code = _validate_required(row_num, "Resources", "code", code, issues)
        _validate_required(row_num, "Resources", "name", r.get("name"), issues)
        _validate_enum(
            row_num,
            "Resources",
            "type",
            r.get("type"),
            RESOURCE_TYPES,
            issues,
            required=True,
        )
        _validate_int(row_num, "Resources", "capacity", r.get("capacity"), issues, min_value=0)
        quantity = _validate_int(
            row_num, "Resources", "quantity", r.get("quantity"), issues, min_value=0
        )
        available = _validate_int(
            row_num,
            "Resources",
            "available_quantity",
            r.get("available_quantity"),
            issues,
            min_value=0,
        )
        if quantity is not None and available is not None and available > quantity:
            issues.append(
                _issue(
                    row_num,
                    "Resources",
                    "available_quantity",
                    "available_quantity cannot exceed quantity",
                )
            )
        if ok_code:
            if code in seen:
                issues.append(
                    _issue(row_num, "Resources", "code", "duplicate code '%s'" % code)
                )
            seen.add(code)


def _validate_modules(rows, sg_codes, module_codes, issues):
    seen = set()
    for r in rows:
        row_num = r["row"]
        code = to_str(r.get("code"))
        ok_code = _validate_required(row_num, "Modules", "code", code, issues)
        _validate_required(row_num, "Modules", "name", r.get("name"), issues)
        _validate_int(row_num, "Modules", "theory_hours", r.get("theory_hours"), issues, min_value=0)
        _validate_int(row_num, "Modules", "practice_hours", r.get("practice_hours"), issues, min_value=0)
        if to_str(r.get("student_group")):
            _validate_fk(
                row_num, "Modules", "student_group", r.get("student_group"), sg_codes, issues
            )
        if ok_code:
            if code in seen:
                issues.append(
                    _issue(row_num, "Modules", "code", "duplicate code '%s'" % code)
                )
            seen.add(code)


def _validate_teacher_modules(rows, teacher_codes, module_codes, issues):
    seen = set()
    for r in rows:
        row_num = r["row"]
        teacher_code = to_str(r.get("teacher_code"))
        module_code = to_str(r.get("module_code"))
        ok_t = _validate_required(row_num, "TeacherModule", "teacher_code", teacher_code, issues)
        ok_m = _validate_required(row_num, "TeacherModule", "module_code", module_code, issues)
        if ok_t:
            if teacher_code not in teacher_codes:
                issues.append(
                    _issue(
                        row_num,
                        "TeacherModule",
                        "teacher_code",
                        "teacher_code '%s' does not reference a known Teacher" % teacher_code,
                    )
                )
        if ok_m:
            if module_code not in module_codes:
                issues.append(
                    _issue(
                        row_num,
                        "TeacherModule",
                        "module_code",
                        "module_code '%s' does not reference a known Module" % module_code,
                    )
                )
        if ok_t and ok_m:
            key = (teacher_code, module_code)
            if key in seen:
                issues.append(
                    _issue(
                        row_num,
                        "TeacherModule",
                        "teacher_code",
                        "duplicate teacher-module pair '%s -> %s'" % key,
                    )
                )
            seen.add(key)


def _validate_fixed_sessions(rows, module_codes, sg_codes, resource_codes, teacher_codes, issues):
    for r in rows:
        row_num = r["row"]
        ok_m = _validate_required(
            row_num, "FixedSessions", "module_code", r.get("module_code"), issues
        )
        ok_sg = _validate_required(
            row_num, "FixedSessions", "student_group_code", r.get("student_group_code"), issues
        )
        _validate_enum(
            row_num,
            "FixedSessions",
            "session_type",
            r.get("session_type"),
            SESSION_TYPES,
            issues,
            required=True,
        )
        _validate_enum(
            row_num, "FixedSessions", "tier", r.get("tier"), TIERS, issues, required=True
        )
        _validate_int(
            row_num,
            "FixedSessions",
            "duration_slots",
            r.get("duration_slots"),
            issues,
            min_value=1,
        )
        if ok_m and to_str(r.get("module_code")) not in module_codes:
            issues.append(
                _issue(
                    row_num,
                    "FixedSessions",
                    "module_code",
                    "module_code '%s' does not reference a known Module"
                    % to_str(r.get("module_code")),
                )
            )
        if ok_sg and to_str(r.get("student_group_code")) not in sg_codes:
            issues.append(
                _issue(
                    row_num,
                    "FixedSessions",
                    "student_group_code",
                    "student_group_code '%s' does not reference a known StudentGroup"
                    % to_str(r.get("student_group_code")),
                )
            )
        if to_str(r.get("resource_code")):
            _validate_fk(
                row_num,
                "FixedSessions",
                "resource_code",
                r.get("resource_code"),
                resource_codes,
                issues,
            )
        for t in to_list(r.get("teacher_codes")):
            if t not in teacher_codes:
                issues.append(
                    _issue(
                        row_num,
                        "FixedSessions",
                        "teacher_codes",
                        "teacher '%s' does not reference a known Teacher" % t,
                    )
                )


def has_errors(issues):
    return any(i["severity"] == SEVERITY_ERROR for i in issues)

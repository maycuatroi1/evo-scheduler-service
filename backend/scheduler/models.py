import uuid

from django.db import models


class Tenant(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, unique=True, db_index=True)
    config_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["code"]
        indexes = [models.Index(fields=["code"], name="idx_tenant_code")]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Campus(models.Model):
    """Cơ sở đào tạo. Trường có cơ sở chính Hà Nội và phân hiệu Huế; giáo
    viên dạy chéo hai cơ sở cần khoảng nghỉ đủ để di chuyển."""

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="campuses"
    )
    code = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, default="")
    travel_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Thời gian di chuyển tối thiểu tới cơ sở khác, tính bằng phút",
    )

    class Meta:
        ordering = ["tenant", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"], name="uq_campus_tenant_code"
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Department(models.Model):
    """Khoa hoặc tổ bộ môn."""

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="departments"
    )
    code = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        help_text="Tổ bộ môn trực thuộc khoa nào",
    )

    class Meta:
        ordering = ["tenant", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"], name="uq_department_tenant_code"
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Teacher(models.Model):
    class Block(models.TextChoices):
        CULTURE = "culture", "Culture"
        VOCATIONAL = "vocational", "Vocational"
        BOTH = "both", "Both"

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="teachers"
    )
    code = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    blocks = models.JSONField(default=list, blank=True)
    quota_standard_hours = models.FloatField(
        null=True,
        blank=True,
        help_text="Định mức giờ chuẩn/năm, đặt riêng từng người",
    )
    modules = models.ManyToManyField(
        "Module", through="TeacherModule", related_name="teachers", blank=True
    )
    # Hồ sơ mở rộng
    moet_code = models.CharField(
        max_length=64, blank=True, default="", help_text="Mã định danh Bộ GD&ĐT"
    )
    email = models.EmailField(blank=True, default="")
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teachers",
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teachers",
    )
    # Ràng buộc cá nhân — để trống nghĩa là không áp
    max_periods_per_session = models.PositiveSmallIntegerField(null=True, blank=True)
    min_periods_per_session = models.PositiveSmallIntegerField(null=True, blank=True)
    days_off_per_week = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["tenant", "code"]
        indexes = [
            models.Index(fields=["tenant", "code"], name="idx_teacher_t_code"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"], name="uq_teacher_tenant_code"
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class HomeroomClass(models.Model):
    """Lớp văn hoá (11A3, 12A1…) — đơn vị sinh hoạt của học sinh hệ 9+.

    Một lớp văn hoá có thể tách thành nhiều nhóm nghề, và ngược lại nhiều
    lớp có thể gộp chung một nhóm nghề. Quan hệ nhiều-nhiều này diễn ra
    thật trong thời khoá biểu của trường (11A3 tách 3 nhóm; 12A1+12A4 gộp
    một nhóm), nên phải mô hình hoá tách khỏi StudentGroup.
    """

    class Shift(models.TextChoices):
        MORNING = "morning", "Sáng"
        AFTERNOON = "afternoon", "Chiều"
        FULL_DAY = "full_day", "Cả ngày"

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="homeroom_classes"
    )
    code = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255, blank=True, default="")
    grade = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Khối 10, 11 hoặc 12"
    )
    size = models.PositiveIntegerField(default=0)
    culture_shift = models.CharField(
        max_length=16,
        choices=Shift.choices,
        default=Shift.MORNING,
        help_text="Ca học văn hoá; ca học nghề là phần bù",
    )
    room = models.ForeignKey(
        "Resource",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homeroom_classes",
        help_text="Phòng cố định của lớp văn hoá",
    )

    class Meta:
        ordering = ["tenant", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"], name="uq_homeroom_tenant_code"
            ),
        ]

    def vocational_shift(self):
        """Ca học nghề suy ra từ ca văn hoá."""
        if self.culture_shift == self.Shift.MORNING:
            return self.Shift.AFTERNOON
        if self.culture_shift == self.Shift.AFTERNOON:
            return self.Shift.MORNING
        return self.Shift.AFTERNOON

    def __str__(self):
        return self.code


class StudentGroup(models.Model):
    """Nhóm xếp lịch — một cột trên thời khoá biểu.

    Với hệ song bằng đây là *nhóm nghề*, liên kết tới một hoặc nhiều lớp
    văn hoá qua `homerooms`. Với cao đẳng và trung cấp thường thì nhóm
    trùng luôn với lớp, `homerooms` để trống.
    """

    class EnrollmentType(models.TextChoices):
        DUAL_DEGREE = "dual_degree", "Dual Degree"
        COLLEGE = "college", "College"
        INTERMEDIATE = "intermediate", "Intermediate"

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="student_groups"
    )
    code = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    enrollment_type = models.CharField(
        max_length=32, choices=EnrollmentType.choices
    )
    size = models.PositiveIntegerField(default=0)
    homerooms = models.ManyToManyField(
        HomeroomClass,
        related_name="groups",
        blank=True,
        help_text="Các lớp văn hoá góp học sinh vào nhóm nghề này",
    )
    occupation = models.CharField(
        max_length=255, blank=True, default="", help_text="Tên nghề"
    )
    hazardous = models.BooleanField(
        default=False,
        help_text="Nghề nặng nhọc, độc hại — trần thực hành 10 thay vì 18",
    )

    class Meta:
        ordering = ["tenant", "code"]
        indexes = [
            models.Index(
                fields=["tenant", "code"], name="idx_studentgroup_t_code"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"], name="uq_studentgroup_t_code"
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Resource(models.Model):
    class ResourceType(models.TextChoices):
        THEORY_ROOM = "theory_room", "Theory Room"
        WORKSHOP = "workshop", "Workshop"
        TOOL_SET = "tool_set", "Tool Set"

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="resources"
    )
    code = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=32, choices=ResourceType.choices)
    capacity = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["tenant", "code"]
        indexes = [
            models.Index(fields=["tenant", "code"], name="idx_resource_t_code"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"], name="uq_resource_t_code"
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Module(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="modules"
    )
    code = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    theory_hours = models.PositiveIntegerField(default=0)
    practice_hours = models.PositiveIntegerField(default=0)
    student_group = models.ForeignKey(
        StudentGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modules",
    )

    class Meta:
        ordering = ["tenant", "code"]
        indexes = [
            models.Index(fields=["tenant", "code"], name="idx_module_t_code"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"], name="uq_module_t_code"
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TeacherModule(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="teacher_modules"
    )
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name="teacher_modules"
    )
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="teacher_modules"
    )

    class Meta:
        ordering = ["tenant", "teacher", "module"]
        indexes = [
            models.Index(
                fields=["tenant", "teacher"], name="idx_tm_t_teacher"
            ),
            models.Index(
                fields=["tenant", "module"], name="idx_tm_t_module"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "module"],
                name="uq_tm_teacher_module",
            ),
        ]

    def __str__(self):
        return f"{self.teacher.code} -> {self.module.code}"


class Session(models.Model):
    class SessionType(models.TextChoices):
        THEORY = "theory", "Theory"
        PRACTICE = "practice", "Practice"
        INTERNSHIP = "internship", "Internship"
        SUPPLEMENTARY = "supplementary", "Supplementary"

    class Tier(models.TextChoices):
        CULTURE = "culture", "Culture"
        VOCATIONAL = "vocational", "Vocational"

    class Location(models.TextChoices):
        ON_CAMPUS = "on_campus", "Tại trường"
        ENTERPRISE = "enterprise", "Doanh nghiệp"
        ONLINE = "online", "Trực tuyến"

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="sessions"
    )
    schedule = models.ForeignKey(
        "Schedule",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sessions",
        help_text="Phương án TKB chứa buổi học này",
    )
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="sessions"
    )
    student_group = models.ForeignKey(
        StudentGroup, on_delete=models.CASCADE, related_name="sessions"
    )
    session_type = models.CharField(max_length=16, choices=SessionType.choices)
    duration_slots = models.PositiveIntegerField(default=1)
    tier = models.CharField(max_length=16, choices=Tier.choices)
    assigned_timeslot = models.JSONField(null=True, blank=True)
    assigned_resource = models.ForeignKey(
        Resource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )
    assigned_teachers = models.ManyToManyField(
        Teacher, related_name="sessions", blank=True
    )
    is_locked = models.BooleanField(default=False)
    location = models.CharField(
        max_length=16, choices=Location.choices, default=Location.ON_CAMPUS
    )
    is_pinned = models.BooleanField(
        default=False,
        help_text="Ghim trước khi chạy bộ giải (Chào cờ, Sinh hoạt…)",
    )

    def consumes_resources(self):
        """Buổi thực tập và buổi ngoài trường chặn lớp nhưng không chiếm
        phòng, giáo viên của trường, và không tính vào định mức."""
        if self.session_type == self.SessionType.INTERNSHIP:
            return False
        return self.location == self.Location.ON_CAMPUS

    class Meta:
        ordering = ["tenant", "module", "student_group"]
        indexes = [
            models.Index(fields=["tenant", "tier"], name="idx_session_t_tier"),
            models.Index(
                fields=["tenant", "is_locked"], name="idx_session_t_locked"
            ),
        ]

    def __str__(self):
        return f"{self.tenant.code}/{self.module.code}/{self.session_type}"


class ConstraintRule(models.Model):
    class RuleType(models.TextChoices):
        UNAVAILABILITY = "unavailability", "Unavailability"
        RESOURCE_REQUIREMENT = "resource_requirement", "Resource Requirement"
        CAPACITY_LIMIT = "capacity_limit", "Capacity Limit"
        QUOTA_LIMIT = "quota_limit", "Quota Limit"
        PREFERENCE = "preference", "Preference"
        EXCLUSION = "exclusion", "Exclusion"
        ADJACENCY = "adjacency", "Adjacency"
        DISTRIBUTION = "distribution", "Distribution"
        # Các loại vốn chỉ tồn tại trong bộ giải, nay lưu được vào CSDL
        TEACHER_NO_OVERLAP = "teacher_no_overlap", "Teacher No Overlap"
        STUDENT_NO_OVERLAP = "student_no_overlap", "Student No Overlap"
        SHARED_RESOURCE_POOL = "shared_resource_pool", "Shared Resource Pool"
        # Ràng buộc đặc thù trường nghề
        GROUP_SAME_CLASS = "group_same_class", "Nhóm cùng lớp văn hoá"
        SHIFT_BY_GRADE = "shift_by_grade", "Ca học theo khối"
        CAPACITY_BY_TYPE = "capacity_by_type", "Trần sĩ số theo loại buổi"
        OFFSITE_NO_ROOM = "offsite_no_room", "Buổi ngoài trường không chiếm phòng"

    class Hardness(models.TextChoices):
        HARD = "hard", "Hard"
        SOFT = "soft", "Soft"

    class Priority(models.TextChoices):
        HIGH = "high", "Cao"
        MEDIUM = "medium", "Trung bình"
        LOW = "low", "Thấp"

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="constraint_rules"
    )
    type = models.CharField(
        max_length=64, choices=RuleType.choices, db_index=True
    )
    scope_json = models.JSONField(default=dict, blank=True)
    params_json = models.JSONField(default=dict, blank=True)
    hardness = models.CharField(
        max_length=8, choices=Hardness.choices, default=Hardness.HARD
    )
    priority = models.CharField(
        max_length=8,
        choices=Priority.choices,
        default=Priority.LOW,
        help_text="Cao = cố giữ bằng mọi giá; Thấp = bỏ được khi bí",
    )
    weight = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    #: Hệ số nhân trọng số theo độ ưu tiên, dùng khi dựng hàm mục tiêu.
    PRIORITY_FACTOR = {"high": 5, "medium": 2, "low": 1}

    def effective_weight(self):
        return max(1, int(self.weight)) * self.PRIORITY_FACTOR.get(
            self.priority, 1
        )

    class Meta:
        ordering = ["tenant", "type", "hardness"]
        indexes = [
            models.Index(
                fields=["tenant", "active"], name="idx_crule_t_active"
            ),
            models.Index(fields=["tenant", "type"], name="idx_crule_t_type"),
        ]

    def __str__(self):
        return f"{self.tenant.code}/{self.type} ({self.hardness})"


class Schedule(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SOLVING = "solving", "Solving"
        SOLVED = "solved", "Solved"
        FAILED = "failed", "Failed"
        PUBLISHED = "published", "Published"

    class Tier(models.TextChoices):
        CULTURE = "culture", "Culture"
        VOCATIONAL = "vocational", "Vocational"

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="schedules"
    )
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT
    )
    tier = models.CharField(
        max_length=16, choices=Tier.choices, null=True, blank=True
    )
    week_start = models.DateField(null=True, blank=True)
    week_number = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Tuần thứ mấy trong năm học (01–46)"
    )
    objective_value = models.FloatField(null=True, blank=True)
    weights_json = models.JSONField(default=dict, blank=True)
    # Kế thừa và xuất bản
    inherited_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived",
        help_text="Phiên bản gốc mà lịch này kế thừa",
    )
    is_manual_edit = models.BooleanField(
        default=False, help_text="Đã tinh chỉnh tay sau khi bộ giải chạy"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_schedules",
    )
    unplaced_count = models.PositiveIntegerField(
        default=0, help_text="Số buổi chưa xếp được"
    )

    class Meta:
        ordering = ["tenant", "-id"]
        indexes = [
            models.Index(
                fields=["tenant", "status"], name="idx_schedule_t_status"
            ),
            models.Index(fields=["tenant", "tier"], name="idx_schedule_t_tier"),
        ]

    def __str__(self):
        return f"{self.tenant.code}/{self.name} ({self.status})"


class SolveJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SOLVING = "solving", "Solving"
        SOLVED = "solved", "Solved"
        FAILED = "failed", "Failed"

    class Phase(models.TextChoices):
        BUILDING_MODEL = "building_model", "Building Model"
        SOLVING = "solving", "Solving"
        POST_PROCESSING = "post_processing", "Post Processing"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="solve_jobs"
    )
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="solve_jobs"
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.QUEUED,
        db_index=True,
    )
    phase = models.CharField(
        max_length=32, choices=Phase.choices, null=True, blank=True
    )
    progress = models.PositiveSmallIntegerField(default=0)
    objective_value = models.FloatField(null=True, blank=True)
    error = models.TextField(blank=True, default="")
    metrics_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["tenant", "status"], name="idx_solvejob_t_status"
            ),
        ]

    def __str__(self):
        return f"{self.tenant.code}/{self.id} ({self.status})"


class User(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Quản trị hệ thống"
        REGISTRAR = "registrar", "Phòng Đào tạo"
        DEAN = "dean", "Trưởng khoa"
        TEACHER = "teacher", "Giáo viên"
        STUDENT = "student", "Sinh viên"

    #: Vai trò nào được phép làm gì. Thứ tự từ mạnh xuống yếu.
    WRITE_ROLES = {Role.ADMIN, Role.REGISTRAR}
    IMPORT_ROLES = {Role.ADMIN, Role.REGISTRAR}
    SOLVE_ROLES = {Role.ADMIN, Role.REGISTRAR}
    PUBLISH_ROLES = {Role.ADMIN, Role.REGISTRAR}

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    password_hash = models.CharField(max_length=255)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="users"
    )
    role = models.CharField(
        max_length=16, choices=Role.choices, default=Role.REGISTRAR, db_index=True
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        help_text="Liên kết tài khoản với hồ sơ giáo viên",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def can_write(self):
        return self.role in self.WRITE_ROLES

    def can_solve(self):
        return self.role in self.SOLVE_ROLES

    def can_publish(self):
        return self.role in self.PUBLISH_ROLES

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.tenant.code})"

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
    quota_standard_hours = models.FloatField(null=True, blank=True)
    modules = models.ManyToManyField(
        "Module", through="TeacherModule", related_name="teachers", blank=True
    )

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


class StudentGroup(models.Model):
    class EnrollmentType(models.TextChoices):
        DUAL_DEGREE = "dual_degree", "Dual Degree"
        COLLEGE = "college", "College"

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

    class Tier(models.TextChoices):
        CULTURE = "culture", "Culture"
        VOCATIONAL = "vocational", "Vocational"

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="sessions"
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

    class Hardness(models.TextChoices):
        HARD = "hard", "Hard"
        SOFT = "soft", "Soft"

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
    weight = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

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
    objective_value = models.FloatField(null=True, blank=True)
    weights_json = models.JSONField(default=dict, blank=True)

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

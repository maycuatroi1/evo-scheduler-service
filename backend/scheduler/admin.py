from django.contrib import admin

from .models import (
    ConstraintRule,
    Module,
    Resource,
    Schedule,
    Session,
    StudentGroup,
    Teacher,
    TeacherModule,
    Tenant,
    User,
)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "name", "tenant", "created_at")
    list_filter = ("tenant",)
    search_fields = ("email", "name")
    list_select_related = ("tenant",)
    ordering = ("-created_at",)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "code", "name", "quota_standard_hours")
    list_filter = ("tenant",)
    search_fields = ("code", "name")
    list_select_related = ("tenant",)
    ordering = ("tenant", "code")


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "code", "name", "enrollment_type", "size")
    list_filter = ("tenant", "enrollment_type")
    search_fields = ("code", "name")
    list_select_related = ("tenant",)
    ordering = ("tenant", "code")


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "code",
        "name",
        "type",
        "capacity",
        "quantity",
        "available_quantity",
    )
    list_filter = ("tenant", "type")
    search_fields = ("code", "name")
    list_select_related = ("tenant",)
    ordering = ("tenant", "code")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "code",
        "name",
        "theory_hours",
        "practice_hours",
        "student_group",
    )
    list_filter = ("tenant",)
    search_fields = ("code", "name")
    list_select_related = ("tenant", "student_group")
    ordering = ("tenant", "code")


@admin.register(TeacherModule)
class TeacherModuleAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "teacher", "module")
    list_filter = ("tenant",)
    search_fields = ("teacher__code", "module__code")
    list_select_related = ("tenant", "teacher", "module")
    ordering = ("tenant", "teacher", "module")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "module",
        "student_group",
        "session_type",
        "tier",
        "duration_slots",
        "assigned_resource",
        "is_locked",
    )
    list_filter = ("tenant", "session_type", "tier", "is_locked")
    search_fields = ("module__code", "student_group__code")
    list_select_related = (
        "tenant",
        "module",
        "student_group",
        "assigned_resource",
    )
    ordering = ("tenant", "module", "student_group")


@admin.register(ConstraintRule)
class ConstraintRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "type",
        "hardness",
        "weight",
        "active",
    )
    list_filter = ("tenant", "type", "hardness", "active")
    search_fields = ("type",)
    list_select_related = ("tenant",)
    ordering = ("tenant", "type", "hardness")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "name",
        "status",
        "tier",
        "week_start",
        "objective_value",
    )
    list_filter = ("tenant", "status", "tier")
    search_fields = ("name",)
    list_select_related = ("tenant",)
    ordering = ("tenant", "-id")

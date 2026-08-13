from scheduler.models import (
    Module,
    Resource,
    Session,
    StudentGroup,
    Teacher,
)


def seed_demo_data(tenant) -> None:
    teachers_data = [
        ("GV001", "Nguyễn Văn An", ["culture"]),
        ("GV002", "Trần Thị Bình", ["vocational"]),
        ("GV003", "Lê Hoàng Cường", ["both"]),
    ]
    teachers = []
    for code, name, blocks in teachers_data:
        teachers.append(
            Teacher.objects.create(
                tenant=tenant, code=code, name=name, blocks=blocks
            )
        )

    groups_data = [
        ("LOP10A1", "Lớp 10A1", "dual_degree", 30),
        ("LOP11A2", "Lớp 11A2", "college", 25),
    ]
    groups = []
    for code, name, enrollment_type, size in groups_data:
        groups.append(
            StudentGroup.objects.create(
                tenant=tenant,
                code=code,
                name=name,
                enrollment_type=enrollment_type,
                size=size,
            )
        )

    resources_data = [
        ("P101", "Phòng lý thuyết 101", "theory_room", 40, 1),
        ("XN01", "Xưởng thực hành 01", "workshop", 20, 1),
    ]
    for code, name, rtype, capacity, quantity in resources_data:
        Resource.objects.create(
            tenant=tenant,
            code=code,
            name=name,
            type=rtype,
            capacity=capacity,
            quantity=quantity,
            available_quantity=quantity,
        )

    modules_data = [
        ("MH_TOAN", "Toán học", 60, 0, groups[0]),
        ("MH_TIN", "Tin học", 30, 30, groups[1]),
    ]
    modules = []
    for code, name, theory_hours, practice_hours, student_group in modules_data:
        modules.append(
            Module.objects.create(
                tenant=tenant,
                code=code,
                name=name,
                theory_hours=theory_hours,
                practice_hours=practice_hours,
                student_group=student_group,
            )
        )

    sessions_data = [
        (modules[0], groups[0], "theory", 2, "culture"),
        (modules[0], groups[0], "practice", 1, "culture"),
        (modules[1], groups[1], "theory", 2, "vocational"),
        (modules[1], groups[1], "practice", 2, "vocational"),
    ]
    for module, student_group, session_type, duration_slots, tier in sessions_data:
        Session.objects.create(
            tenant=tenant,
            module=module,
            student_group=student_group,
            session_type=session_type,
            duration_slots=duration_slots,
            tier=tier,
        )

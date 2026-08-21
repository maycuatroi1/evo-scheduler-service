from scheduler.solver.context import BuildContext


def apply(ctx: BuildContext, rule):
    """Ghi nhận các buổi không chiếm phòng của trường.

    Việc *không* dựng biến chọn phòng cho những buổi này nằm ở engine, vì
    mô hình bắt mỗi buổi phải chọn đúng một phòng — cấm hết bằng ràng buộc
    sẽ khiến bài toán vô nghiệm thay vì giải phóng phòng.

    Tuần thực tập tốt nghiệp chiếm trọn 50 tiết của lớp nhưng diễn ra tại
    doanh nghiệp: chặn lớp, không tốn phòng, không tốn giáo viên, không
    tính vào định mức.
    """
    offsite = [s for s in ctx.sessions if not s.get("consumes_resources", True)]
    if offsite:
        ctx.warnings.append(
            "offsite_no_room: %d buổi ngoài trường không chiếm phòng" % len(offsite)
        )
    return None

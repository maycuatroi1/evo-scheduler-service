"""Cấu hình khung thời gian của thời khoá biểu.

Số ngày học và số tiết mỗi ngày khác nhau giữa các trường: có nơi chỉ học một
buổi, có nơi học cả sáng lẫn chiều. Cấu hình nằm ở `Tenant.config_json`, khai
được qua API hoặc sheet Config trong file nhập liệu, và cùng một chỗ này sinh
ra khung giờ cho bộ giải.
"""

DAY_NAMES = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

DAY_LABELS = {
    "monday": "Thứ 2",
    "tuesday": "Thứ 3",
    "wednesday": "Thứ 4",
    "thursday": "Thứ 5",
    "friday": "Thứ 6",
    "saturday": "Thứ 7",
    "sunday": "Chủ nhật",
}

DEFAULT_DAYS_PER_WEEK = 6
DEFAULT_PERIODS_PER_DAY = 5
DEFAULT_MORNING_COUNT = 2
DEFAULT_WEEKS = 1

MAX_DAYS_PER_WEEK = 7
MAX_PERIODS_PER_DAY = 16
MAX_WEEKS = 8


def default_config():
    return {
        "weeks": DEFAULT_WEEKS,
        "days": DAY_NAMES[:DEFAULT_DAYS_PER_WEEK],
        "periods_per_day": DEFAULT_PERIODS_PER_DAY,
        "morning_count": DEFAULT_MORNING_COUNT,
    }


def _coerce_int(value, fallback):
    if value is None or value == "":
        return fallback
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _day_list(cfg):
    days = cfg.get("days")
    if isinstance(days, list) and days:
        out = []
        for i, d in enumerate(days):
            if isinstance(d, dict):
                out.append(str(d.get("name") or DAY_NAMES[i % len(DAY_NAMES)]))
            else:
                out.append(str(d))
        return out
    count = _coerce_int(
        cfg.get("days_per_week"), DEFAULT_DAYS_PER_WEEK
    )
    count = max(1, min(count, MAX_DAYS_PER_WEEK))
    return DAY_NAMES[:count]


def normalize(cfg):
    """Đưa cấu hình về dạng chuẩn, bỏ qua giá trị lạ thay vì báo lỗi."""
    cfg = dict(cfg or {})
    days = _day_list(cfg)
    periods = _coerce_int(cfg.get("periods_per_day"), DEFAULT_PERIODS_PER_DAY)
    morning = _coerce_int(cfg.get("morning_count"), DEFAULT_MORNING_COUNT)
    weeks = _coerce_int(cfg.get("weeks"), DEFAULT_WEEKS)
    periods = max(1, min(periods, MAX_PERIODS_PER_DAY))
    weeks = max(1, min(weeks, MAX_WEEKS))
    morning = max(0, min(morning, periods))
    return {
        "weeks": weeks,
        "days": days,
        "periods_per_day": periods,
        "morning_count": morning,
    }


def validate(cfg):
    """Danh sách lỗi của cấu hình do người dùng khai, tiếng Việt."""
    cfg = dict(cfg or {})
    errors = []
    days = cfg.get("days")
    if isinstance(days, list):
        if not days:
            errors.append("Phải chọn ít nhất một ngày học trong tuần.")
        elif len(days) > MAX_DAYS_PER_WEEK:
            errors.append("Một tuần chỉ có tối đa %d ngày." % MAX_DAYS_PER_WEEK)
        unknown = [str(d) for d in days if str(d) not in DAY_NAMES]
        if unknown:
            errors.append(
                "Ngày học không hợp lệ: %s. Chỉ nhận %s."
                % (", ".join(unknown), ", ".join(DAY_NAMES))
            )
    elif days is not None:
        errors.append("Danh sách ngày học phải là một mảng.")

    if "days_per_week" in cfg and cfg["days_per_week"] not in (None, ""):
        value = _coerce_int(cfg.get("days_per_week"), None)
        if value is None or value < 1 or value > MAX_DAYS_PER_WEEK:
            errors.append(
                "Số ngày học mỗi tuần phải từ 1 đến %d." % MAX_DAYS_PER_WEEK
            )

    periods = _coerce_int(cfg.get("periods_per_day"), None)
    if "periods_per_day" in cfg and cfg["periods_per_day"] not in (None, ""):
        if periods is None or periods < 1 or periods > MAX_PERIODS_PER_DAY:
            errors.append(
                "Số tiết mỗi ngày phải từ 1 đến %d." % MAX_PERIODS_PER_DAY
            )

    if "morning_count" in cfg and cfg["morning_count"] not in (None, ""):
        morning = _coerce_int(cfg.get("morning_count"), None)
        if morning is None or morning < 0:
            errors.append("Số tiết buổi sáng phải là số không âm.")
        elif periods is not None and 1 <= periods <= MAX_PERIODS_PER_DAY and morning > periods:
            errors.append(
                "Số tiết buổi sáng (%d) không được lớn hơn số tiết mỗi ngày (%d)."
                % (morning, periods)
            )

    if "weeks" in cfg and cfg["weeks"] not in (None, ""):
        weeks = _coerce_int(cfg.get("weeks"), None)
        if weeks is None or weeks < 1 or weeks > MAX_WEEKS:
            errors.append("Số tuần phải từ 1 đến %d." % MAX_WEEKS)

    return errors


def build(cfg):
    """Sinh danh sách tiết học từ cấu hình đã chuẩn hoá."""
    cfg = normalize(cfg)
    horizon = []
    index = 0
    for week in range(cfg["weeks"]):
        for position, name in enumerate(cfg["days"]):
            day = DAY_NAMES.index(name) if name in DAY_NAMES else position
            for period in range(cfg["periods_per_day"]):
                horizon.append(
                    {
                        "index": index,
                        "week": week,
                        "day": day,
                        "period": period,
                        "day_name": name,
                        "is_morning": period < cfg["morning_count"],
                    }
                )
                index += 1
    return horizon


def total_slots(cfg):
    cfg = normalize(cfg)
    return cfg["weeks"] * len(cfg["days"]) * cfg["periods_per_day"]


def summary(cfg):
    """Cấu hình kèm số liệu dẫn xuất để hiển thị."""
    normalized = normalize(cfg)
    return {
        "weeks": normalized["weeks"],
        "days": normalized["days"],
        "day_labels": [DAY_LABELS.get(d, d) for d in normalized["days"]],
        "days_per_week": len(normalized["days"]),
        "periods_per_day": normalized["periods_per_day"],
        "morning_count": normalized["morning_count"],
        "total_slots": total_slots(normalized),
    }

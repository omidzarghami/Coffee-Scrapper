from __future__ import annotations

from datetime import date, datetime


def gregorian_to_jalali(year: int, month: int, day: int) -> tuple[int, int, int]:
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = year - 1 if month > 2 else year
    days = (
        355666
        + (365 * year)
        + ((gy2 + 3) // 4)
        - ((gy2 + 99) // 100)
        + ((gy2 + 399) // 400)
        + day
        + g_d_m[month - 1]
    )
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + (days % 31)
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def to_jalali_str(value: date | datetime | str | None) -> str:
    if value is None:
        today = date.today()
        jy, jm, jd = gregorian_to_jalali(today.year, today.month, today.day)
        return f"{jy:04d}/{jm:02d}/{jd:02d}"

    if isinstance(value, str):
        raw = value.strip()
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            parsed = datetime.strptime(raw[:10], "%Y-%m-%d")
        value = parsed.date()
    elif isinstance(value, datetime):
        value = value.date()

    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"

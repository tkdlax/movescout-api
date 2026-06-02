"""Bailey-style fiscal weeks: Sunday–Saturday, labeled by week-ending Saturday."""

from datetime import date, timedelta


def week_ending_saturday(d: date) -> date:
    """Return the Saturday at the end of the Sunday–Saturday week containing ``d``."""
    days_since_sunday = (d.weekday() + 1) % 7
    sunday = d - timedelta(days=days_since_sunday)
    return sunday + timedelta(days=6)


def fiscal_week_number(d: date, fiscal_year: int) -> int:
    """Fiscal week index for ``fiscal_year`` (week 1 contains Jan 1)."""
    week1_end = week_ending_saturday(date(fiscal_year, 1, 1))
    sat_end = week_ending_saturday(d)
    return ((sat_end - week1_end).days // 7) + 1


def fiscal_week_end_label(week: int, fiscal_year: int) -> str:
    """Column header date: week-ending Saturday as M/D/YY (e.g. 5/16/26)."""
    week1_end = week_ending_saturday(date(fiscal_year, 1, 1))
    sat = week1_end + timedelta(weeks=week - 1)
    return f"{sat.month}/{sat.day}/{sat.strftime('%y')}"

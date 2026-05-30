from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class SalesReportParams:
    move_type: str
    start: str
    end: str
    location: str
    goal: float
    sales_rep_name: str | None
    default_filter: int
    fiscal_year: int
    callback_url: str | None = None


def _format_report_date(value: date) -> str:
    return value.strftime(f"%b {value.day}, %Y")


def _fiscal_year_from_start(start: str, fallback: int) -> int:
    for part in start.split(","):
        part = part.strip()
        if part.isdigit() and len(part) == 4:
            return int(part)
    return fallback


def normalize_sales_report_params(
    *,
    move_type: str = "Interstate",
    start: str | None = None,
    end: str | None = None,
    location: str = "Bailey's Moving & Storage",
    goal: float = 0.40,
    sales_rep_name: str | None = None,
    default_filter: int = 3,
    callback_url: str | None = None,
) -> SalesReportParams:
    today = date.today()
    resolved_start = start or f"Jan 1, {today.year}"
    resolved_end = end or _format_report_date(today)
    fiscal_year = _fiscal_year_from_start(resolved_start, today.year)
    return SalesReportParams(
        move_type=move_type,
        start=resolved_start,
        end=resolved_end,
        location=location,
        goal=goal,
        sales_rep_name=sales_rep_name,
        default_filter=default_filter,
        fiscal_year=fiscal_year,
        callback_url=callback_url,
    )


def sales_report_params_to_dict(params: SalesReportParams) -> dict:
    return asdict(params)


def sales_report_params_from_dict(data: dict) -> SalesReportParams:
    return SalesReportParams(
        move_type=data["move_type"],
        start=data["start"],
        end=data["end"],
        location=data["location"],
        goal=float(data["goal"]),
        sales_rep_name=data.get("sales_rep_name"),
        default_filter=int(data.get("default_filter", 3)),
        fiscal_year=int(data["fiscal_year"]),
        callback_url=data.get("callback_url"),
    )


def build_report_filename(params: SalesReportParams) -> str:
    slug = params.move_type.lower().replace("/", "-").replace(" ", "-")
    stamp = date.today().strftime("%Y%m%d")
    return f"sales-{slug}-{stamp}.html"

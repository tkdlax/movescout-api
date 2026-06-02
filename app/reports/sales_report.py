from collections import defaultdict
from datetime import date
from typing import Any

from app.reports.fiscal_week import fiscal_week_end_label

DISPOSITION_MAP = {
    37: "Attempted Contact",
    38: "Booked",
    39: "Survey Completed",
    40: "Duplicate",
    41: "Inactive",
    42: "Lost",
    43: "New",
    44: "Pending",
    45: "Ready to book",
    46: "Survey Scheduled",
}
MOVE_TYPE_MAP = {
    119: "Interstate",
    124: "International",
    125: "Cross Border",
    128: "Alaska",
    129: "Hawaii",
    130: "Local/Intra",
}

DISPLAY_BUCKETS = ["Booked", "Ready to Book", "Lost", "Pending", "Survey Scheduled"]


def bucket(disposition: str) -> str:
    if disposition == "Booked":
        return "Booked"
    if disposition == "Ready to book":
        return "Ready to Book"
    if disposition == "Lost":
        return "Lost"
    if disposition in ("Survey Scheduled", "Survey Completed"):
        return "Survey Scheduled"
    return "Pending"


def tally(rows: list[dict[str, Any]]) -> dict[str, dict[int, dict[str, int]]]:
    result: dict[str, dict[int, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    for row in rows:
        result[row["rep"]][row["week"]][row["bucket"]] += 1
    return result


def total_in(t: dict[str, dict[int, dict[str, int]]], rep: str, weeks: list[int]) -> int:
    return sum(sum(t[rep].get(week, {}).values()) for week in weeks)


def booked_in(t: dict[str, dict[int, dict[str, int]]], rep: str, weeks: list[int]) -> int:
    return sum(t[rep].get(week, {}).get("Booked", 0) for week in weeks)


def bucket_in(
    t: dict[str, dict[int, dict[str, int]]], rep: str, weeks: list[int], bucket_name: str
) -> int:
    return sum(t[rep].get(week, {}).get(bucket_name, 0) for week in weeks)


def closing_rate(booked: int, total: int) -> float | None:
    return booked / total if total else None


def n(value: int) -> str:
    return str(value) if value else ""


def delta_html(delta: int) -> str:
    if delta > 0:
        return f'<span class="pos">+{delta}</span>'
    if delta < 0:
        return f'<span class="neg">{delta}</span>'
    return '<span class="neu">—</span>'


def rate_td(rate: float | None, goal: float, css_extra: str = "") -> str:
    if rate is None:
        return f'<td class="rate {css_extra}">—</td>'
    cls = "good" if rate >= goal else "bad"
    return f'<td class="rate {cls} {css_extra}">{rate:.0%}</td>'


def pct_td(rate: float | None, css_extra: str = "") -> str:
    if rate is None:
        return f'<td class="rate {css_extra}">—</td>'
    return f'<td class="rate {css_extra}">{rate:.0%}</td>'


def week_start(week: int, fiscal_year: int) -> str:
    """Week-ending Saturday label for column headers (Bailey report format)."""
    return fiscal_week_end_label(week, fiscal_year)


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', system-ui, Arial, sans-serif;
  font-size: 11px; color: #1a1a1a; background: #fff;
}
.page { padding: 18px 22px; max-width: 1280px; margin: 0 auto; }

.rpt-header {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 14px; padding-bottom: 10px;
  border-bottom: 3px solid #00617f;
}
.rpt-title h1 { font-size: 20px; font-weight: 700; color: #00617f; }
.rpt-title h2 { font-size: 13px; font-weight: 400; color: #555; margin-top: 3px; }
.rpt-meta    { font-size: 10px; color: #888; text-align: right; line-height: 1.8; }

table { width: 100%; border-collapse: collapse; margin-bottom: 18px; font-size: 10.5px; }
th {
  background: #1a7a96; color: #fff;
  padding: 5px 7px; text-align: center;
  font-size: 9.5px; font-weight: 600;
  white-space: nowrap; border: 1px solid #1568800;
}
th.lft    { text-align: left; }
th.grp    { background: #00617f; font-size: 9px; text-transform: uppercase; letter-spacing: .5px; }
th.div    { border-left: 2px solid #4db8d4 !important; }
td.div    { border-left: 2px solid #c5e4ed !important; }

tr.rep td {
  background: #dff0f7; font-weight: 700;
  border-top: 2px solid #8ecfe3; border-bottom: 1px solid #b8dfe9;
  padding: 5px 7px;
}
tr.rep td.name { padding-left: 10px; }

tr.sub td {
  background: #fff; font-size: 10px; color: #444;
  padding: 3px 7px; border-bottom: 1px solid #edf5f8;
}
tr.sub:nth-child(even) td { background: #f5fafc; }
tr.sub td.name { padding-left: 26px; font-style: italic; color: #555; }

td { text-align: center; border-left: 1px solid #e2e2e2; }
td.name { text-align: left; min-width: 155px; border-left: none; }
td.num  { font-variant-numeric: tabular-nums; }

td.rate         { font-weight: 700; text-align: center; }
td.rate.good    { color: #1a7a3a; }
td.rate.bad     { color: #c0392b; }
td.rate.goal    { font-weight: 400; color: #666; }

.pos { color: #1a7a3a; font-weight: 700; }
.neg { color: #c0392b; font-weight: 700; }
.neu { color: #aaa; }

tr.total-leads td {
  background: #00617f; color: #fff; font-weight: 700;
  padding: 5px 7px; border-top: 2px solid #004d63;
}
tr.total-bookings td {
  background: #1a7a96; color: #fff; font-weight: 700;
  padding: 5px 7px;
}
tr.total-leads td.name,
tr.total-bookings td.name { text-align: left; padding-left: 10px; }

.summary { display: flex; gap: 14px; margin-top: 4px; flex-wrap: wrap; }
.card {
  flex: 1; min-width: 200px;
  border: 1px solid #c5e4ed; border-radius: 5px; overflow: hidden;
}
.card-hdr {
  background: #00617f; color: #fff;
  font-size: 10px; font-weight: 600;
  padding: 6px 12px; text-transform: uppercase; letter-spacing: .5px;
}
.card table  { margin: 0; font-size: 11px; }
.card td     { border: none; background: #fff; padding: 4px 12px; text-align: left; }
.card td.val { font-weight: 700; text-align: right; min-width: 60px; }
.card tr:nth-child(even) td { background: #f0f8fb; }

@media print {
  body { font-size: 9px; }
  .page { padding: 8px 12px; max-width: none; }
  tr.rep td, tr.sub td, tr.total-leads td, tr.total-bookings td { page-break-inside: avoid; }
}
"""


def build_html(
    rows: list[dict[str, Any]],
    move_type: str,
    location: str,
    goal: float,
    fiscal_year: int | None = None,
) -> str:
    if not rows:
        return "<p>No data found for this move type.</p>"

    if fiscal_year is None:
        fiscal_year = max(row["year"] for row in rows)

    t = tally(rows)
    all_weeks = sorted({row["week"] for row in rows})
    max_w = all_weeks[-1]

    recent3 = all_weeks[-3:] if len(all_weeks) >= 3 else all_weeks
    twelve_wks = [week for week in all_weeks if week >= max_w - 11]
    ytd_wks = all_weeks

    def sort_key(rep: str) -> tuple[bool, int]:
        return (rep == "Unassigned", -total_in(t, rep, ytd_wks))

    reps = sorted(t.keys(), key=sort_key)

    def parent_rate(weeks: list[int]) -> float | None:
        booked = sum(booked_in(t, rep, weeks) for rep in t)
        total = sum(total_in(t, rep, weeks) for rep in t)
        return closing_rate(booked, total)

    p12_rate = parent_rate(twelve_wks)
    pytd_rate = parent_rate(ytd_wks)

    parent_pend_ytd = sum(bucket_in(t, rep, ytd_wks, "Pending") for rep in t)
    parent_total_ytd = sum(total_in(t, rep, ytd_wks) for rep in t)
    parent_pend_pct = closing_rate(parent_pend_ytd, parent_total_ytd)

    wk_hdrs = "".join(
        f'<th rowspan="2">Wk {week}<br>'
        f'<span style="font-weight:300;font-size:8.5px">'
        f"{week_start(week, fiscal_year)}"
        f"</span></th>"
        for week in recent3
    )

    body_html = ""
    for rep in reps:
        wk_tots = [sum(t[rep].get(week, {}).values()) for week in recent3]
        delta = wk_tots[-1] - wk_tots[-2] if len(wk_tots) >= 2 else 0

        tot_12w = total_in(t, rep, twelve_wks)
        bkd_12w = booked_in(t, rep, twelve_wks)
        rate_12w = closing_rate(bkd_12w, tot_12w)

        tot_ytd = total_in(t, rep, ytd_wks)
        bkd_ytd = booked_in(t, rep, ytd_wks)
        rate_ytd = closing_rate(bkd_ytd, tot_ytd)

        pend_ytd = bucket_in(t, rep, ytd_wks, "Pending")
        rep_pend_pct = closing_rate(pend_ytd, tot_ytd)

        wk_tds = "".join(f'<td class="num">{n(value)}</td>' for value in wk_tots)

        body_html += f"""
<tr class="rep">
  <td class="name">{rep}</td>
  {wk_tds}
  <td class="num">{delta_html(delta)}</td>
  <td class="num div">{n(tot_12w)}</td>
  {rate_td(rate_12w, goal)}
  {rate_td(p12_rate, goal)}
  <td class="rate goal">{goal:.0%}</td>
  {pct_td(rep_pend_pct, "div")}
  {pct_td(parent_pend_pct)}
  <td class="num div">{n(tot_ytd)}</td>
  {rate_td(rate_ytd, goal)}
  {rate_td(pytd_rate, goal)}
  <td class="rate goal">{goal:.0%}</td>
</tr>"""

        for bucket_name in DISPLAY_BUCKETS:
            b_wks = [t[rep].get(week, {}).get(bucket_name, 0) for week in recent3]
            b_delta = b_wks[-1] - b_wks[-2] if len(b_wks) >= 2 else 0
            b_12w = bucket_in(t, rep, twelve_wks, bucket_name)
            b_tds = "".join(f'<td class="num">{n(value)}</td>' for value in b_wks)

            body_html += f"""
<tr class="sub">
  <td class="name">{bucket_name}</td>
  {b_tds}
  <td class="num">{delta_html(b_delta)}</td>
  <td class="num div">{n(b_12w)}</td>
  <td colspan="8"></td>
</tr>"""

    all_wk_tots = [sum(sum(t[rep].get(week, {}).values()) for rep in t) for week in recent3]
    bkd_wk_tots = [sum(t[rep].get(week, {}).get("Booked", 0) for rep in t) for week in recent3]
    tot_delta = all_wk_tots[-1] - all_wk_tots[-2] if len(all_wk_tots) >= 2 else 0
    bkd_delta = bkd_wk_tots[-1] - bkd_wk_tots[-2] if len(bkd_wk_tots) >= 2 else 0
    ytd_total_all = sum(total_in(t, rep, ytd_wks) for rep in t)
    ytd_booked_all = sum(booked_in(t, rep, ytd_wks) for rep in t)

    all_tds = "".join(f'<td class="num">{value}</td>' for value in all_wk_tots)
    bkd_tds = "".join(f'<td class="num">{value}</td>' for value in bkd_wk_tots)

    body_html += f"""
<tr class="total-leads">
  <td class="name">TOTAL WEEKLY LEADS — {fiscal_year}</td>
  {all_tds}
  <td class="num">{delta_html(tot_delta)}</td>
  <td class="num div" colspan="9">{ytd_total_all}</td>
</tr>
<tr class="total-bookings">
  <td class="name">{move_type.upper()} BOOKINGS — {fiscal_year}</td>
  {bkd_tds}
  <td class="num">{delta_html(bkd_delta)}</td>
  <td class="num div" colspan="9">{ytd_booked_all}</td>
</tr>"""

    last_w = recent3[-1] if recent3 else None
    unassigned_recent = sum(t.get("Unassigned", {}).get(last_w, {}).values()) if last_w else 0
    total_recent = sum(sum(t[rep].get(last_w, {}).values()) for rep in t) if last_w else 1
    unassigned_pct_str = f"{unassigned_recent / total_recent:.0%}" if total_recent else "—"

    avg_weekly = ytd_total_all / len(ytd_wks) if ytd_wks else 0
    active_reps = len([rep for rep in t if rep != "Unassigned"])
    opp_per_rep = avg_weekly / active_reps if active_reps else 0

    pending_12w = sum(bucket_in(t, rep, twelve_wks, "Pending") for rep in t)
    pytd_str = f"{pytd_rate:.0%}" if pytd_rate else "—"

    wk_range = f"Weeks {recent3[0]}–{recent3[-1]}" if recent3 else ""
    today = date.today().strftime("%B %d, %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{location} — {move_type} Performance Report</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="page">

<div class="rpt-header">
  <div class="rpt-title">
    <h1>{location}</h1>
    <h2>Move Type: {move_type} &nbsp;|&nbsp; {wk_range} &nbsp;|&nbsp; Fiscal Year {fiscal_year}</h2>
  </div>
  <div class="rpt-meta">
    Generated: {today}<br>
    Closing Rate Goal: <strong>{goal:.0%}</strong>
  </div>
</div>

<table>
<colgroup>
  <col style="width:160px">
  {''.join('<col style="width:54px">' for _ in recent3)}
  <col style="width:54px">
  <col style="width:52px">
  <col style="width:62px">
  <col style="width:62px">
  <col style="width:46px">
  <col style="width:54px">
  <col style="width:54px">
  <col style="width:52px">
  <col style="width:62px">
  <col style="width:62px">
  <col style="width:46px">
</colgroup>
<thead>
  <tr>
    <th class="lft" rowspan="2">Salesperson</th>
    {wk_hdrs}
    <th rowspan="2">Change</th>
    <th class="grp div" colspan="4">12-Week</th>
    <th class="grp div" colspan="2">YTD Pendings</th>
    <th class="grp div" colspan="4">Year-to-Date</th>
  </tr>
  <tr>
    <th class="div">Total</th><th>Close%</th><th>Co.&nbsp;Avg</th><th>Goal</th>
    <th class="div">Rep&nbsp;%</th><th>Co.&nbsp;Avg</th>
    <th class="div">Total</th><th>Close%</th><th>Co.&nbsp;Avg</th><th>Goal</th>
  </tr>
</thead>
<tbody>
{body_html}
</tbody>
</table>

<div class="summary">
  <div class="card">
    <div class="card-hdr">Unassigned Leads</div>
    <table>
      <tr><td>Most recent week</td><td class="val">{unassigned_pct_str}</td></tr>
    </table>
  </div>
  <div class="card">
    <div class="card-hdr">Weekly Opportunities</div>
    <table>
      <tr><td>Avg per week (12-wk)</td><td class="val">{avg_weekly:.0f}</td></tr>
      <tr><td>Per salesperson</td><td class="val">{opp_per_rep:.0f}</td></tr>
    </table>
  </div>
  <div class="card">
    <div class="card-hdr">Pipeline Summary</div>
    <table>
      <tr><td>Active Pendings (12-wk)</td><td class="val">{pending_12w}</td></tr>
      <tr><td>YTD Bookings</td><td class="val">{ytd_booked_all}</td></tr>
      <tr><td>YTD Closing Rate</td><td class="val">{pytd_str}</td></tr>
    </table>
  </div>
</div>

</div>
</body>
</html>"""

"""Build the Excel companion report visualize/report.xlsx from the tables the notebook exports.

Every derived number (shares, gaps from the average, spreads, flags) is an Excel formula so the workbook
stays live; hard-coded inputs come from reports/*.csv and each table names its source file. Thresholds a
reader may want to change sit in blue input cells.

Run after the notebook:  python src/build_report_excel.py
"""
from __future__ import annotations

import json
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.marker import DataPoint
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.workbook.properties import CalcProperties

from config import LABELS, REPORTS, ROOT, VISUALIZE

OUTPUT = VISUALIZE / "report.xlsx"
KAGGLE_URL = "https://www.kaggle.com/datasets/aiexplorer77/digital-burnout-and-productivity-analytics"

FONT = "Arial"
INK, INK_2, MUTED = "0B0B0B", "4F5260", "8A8D98"
RED, BLUE, RED_DARK, BLUE_DARK = "E34948", "2A78D6", "C23B37", "1C5CAB"
HEAD_FILL = PatternFill("solid", fgColor="EEF3FB")
TOTAL_FILL = PatternFill("solid", fgColor="F4F5F7")
INPUT_FILL = PatternFill("solid", fgColor="DCE9FA")
GRID = Side(style="thin", color="E3E4E8")
BOX = Border(bottom=GRID)
BETTER, MID, WORSE = "8DB9EE", "F3F3F1", "EE9593"
KPI_BY_INDEX = {
    "digital_overload": "Screen time, % late-night device use, notifications per day",
    "focus_capacity": "Deep-work hours, task completion rate, distractions per day",
    "psych_strain": "Emotional exhaustion, job satisfaction, attrition",
    "recovery_deficit": "Sleep hours, stress, physical activity",
    "environment_quality": "Workspace quality, internet stability",
}
NUM_SIGNED = "+0.00;-0.00;0.00"


def font(**kw) -> Font:
    return Font(name=FONT, **{"size": 10, "color": INK, **kw})


def put(ws, ref: str, value, fmt: str | None = None, **style):
    c = ws[ref]
    c.value = value
    c.font = style.pop("font", font())
    for k, v in style.items():
        setattr(c, k, v)
    if fmt:
        c.number_format = fmt
    return c


def title(ws, text: str, sub: str) -> None:
    put(ws, "A1", text, font=font(size=15, bold=True))
    put(ws, "A2", sub, font=font(size=10, italic=True, color=INK_2))
    ws.sheet_view.showGridLines = False


def section(ws, row: int, text: str, sub: str | None = None) -> int:
    put(ws, f"A{row}", text, font=font(size=12, bold=True, color=BLUE_DARK))
    if sub:
        put(ws, f"A{row + 1}", sub, font=font(size=9.5, italic=True, color=INK_2))
        return row + 2
    return row + 1


def header(ws, row: int, labels: list[str], col0: int = 1) -> None:
    for i, text in enumerate(labels):
        c = ws.cell(row=row, column=col0 + i, value=text)
        c.font = font(bold=True, color=INK_2)
        c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal="center" if i else "left", vertical="center", wrap_text=True)
        c.border = BOX
    ws.row_dimensions[row].height = 30


def cell(ws, row: int, col: int, value, fmt: str | None = None, color: str = INK, bold: bool = False,
         wrap: bool = False, align: str | None = None, fill: PatternFill | None = None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font(color=color, bold=bold)
    c.border = BOX
    if fmt:
        c.number_format = fmt
    if wrap or align:
        c.alignment = Alignment(wrap_text=wrap, horizontal=align, vertical="top" if wrap else "center")
    if fill:
        c.fill = fill
    return c


def widths(ws, spec: dict[str, float]) -> None:
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


def note(ws, row: int, text: str, col: int = 1) -> None:
    ws.cell(row=row, column=col, value=text).font = font(size=9, italic=True, color=MUTED)


def input_cell(ws, ref: str, value, fmt: str, label: str) -> None:
    lab_col = get_column_letter(ws[ref].column - 1)
    put(ws, f"{lab_col}{ws[ref].row}", label, font=font(color=INK_2))
    put(ws, ref, value, fmt, font=font(color="0000FF", bold=True), fill=INPUT_FILL, alignment=Alignment(horizontal="center"))


def diverging(ws, rng: str, lo: float, hi: float, reverse: bool = False) -> None:
    a, b = (WORSE, BETTER) if reverse else (BETTER, WORSE)
    ws.conditional_formatting.add(rng, ColorScaleRule(start_type="num", start_value=lo, start_color=a,
                                                      mid_type="num", mid_value=0, mid_color=MID,
                                                      end_type="num", end_value=hi, end_color=b))


def sequential(ws, rng: str) -> None:
    ws.conditional_formatting.add(rng, ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                                                      end_type="max", end_color="6DA7EC"))


def bar_chart(title_text: str, horizontal: bool = True, height: float = 7.5, width: float = 16) -> BarChart:
    ch = BarChart()
    ch.type = "bar" if horizontal else "col"
    ch.title = title_text
    ch.style = 10
    ch.height, ch.width = height, width
    ch.gapWidth = 60
    ch.legend.position = "b"
    ch.y_axis.majorGridlines = None
    return ch


def solid(series, color: str) -> None:
    series.graphicalProperties.solidFill = color
    series.graphicalProperties.line.noFill = True


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    meta = json.loads((REPORTS / "segment_meta.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(REPORTS / "03_segment_summary.csv", index_col=0)
    problem = pd.read_csv(REPORTS / "03_segment_problem_scores.csv", index_col=0)
    flags_seg = pd.read_csv(REPORTS / "03_segment_red_flags.csv", index_col=0)
    raw = pd.read_csv(REPORTS / "04_segment_raw_means.csv", index_col=0)
    wc = pd.read_csv(REPORTS / "04_within_group_correlation.csv")
    drivers = pd.read_csv(REPORTS / "02_driver_correlation.csv", index_col=0)
    red = pd.read_csv(REPORTS / "02_red_flags.csv", index_col=0)
    playbook = pd.read_csv(REPORTS / "05_playbook.csv", index_col=0)
    seg_by_code = {s["code"]: s for s in meta["segments"]}
    codes = list(summary.index)
    problem_cols = list(problem.columns)
    group_of = drivers["group"].to_dict()

    wb = Workbook()
    wb._named_styles["Normal"].font = Font(name=FONT, size=10)
    wb.calculation = CalcProperties(fullCalcOnLoad=True)

    # ------------------------------------------------------------------ Groups
    ws = wb.active
    ws.title = "Groups"
    SEG = "Groups"
    title(ws, "Six employee groups",
          "K-Means on 5 million employees · ordered by priority for support · gaps from the average are formulas")
    r0 = section(ws, 4, "Overview", "Source: reports/03_segment_summary.csv (exported by the notebook). The 'All' row is weighted by group size.")
    header(ws, r0, ["Code", "Group", "Risk level", "Employees", "Share", "Burnout avg", "Burnout gap",
                    "Productivity avg", "Productivity gap", "% burnout 70+", "% low productivity",
                    "Warning signs / person", "Risk score"])
    first, last = r0 + 1, r0 + len(codes)
    tot = last + 1
    seg_row = {}
    for i, code in enumerate(codes):
        r = first + i
        seg_row[code] = r
        row = summary.loc[code]
        cell(ws, r, 1, code, bold=True)
        cell(ws, r, 2, row["name"], wrap=True)
        cell(ws, r, 3, row["risk level"])
        cell(ws, r, 4, int(row["employees"]), "#,##0")
        cell(ws, r, 5, f"=D{r}/$D${tot}", "0.0%")
        cell(ws, r, 6, round(float(row["burnout mean"]), 4), "0.0")
        cell(ws, r, 7, f"=F{r}-$F${tot}", "+0.0;-0.0;0.0")
        cell(ws, r, 8, round(float(row["productivity mean"]), 4), "0.0")
        cell(ws, r, 9, f"=H{r}-$H${tot}", "+0.0;-0.0;0.0")
        cell(ws, r, 10, round(float(row["% burnout 70+"]) / 100, 6), "0.0%")
        cell(ws, r, 11, round(float(row["% low productivity"]) / 100, 6), "0.0%")
        cell(ws, r, 12, round(float(row["warning signs per person"]), 4), "0.00")
        cell(ws, r, 13, round(float(row["risk score"]), 4), "0.00")
    cell(ws, tot, 1, "All", bold=True, fill=TOTAL_FILL)
    cell(ws, tot, 2, "All employees", fill=TOTAL_FILL)
    cell(ws, tot, 3, "", fill=TOTAL_FILL)
    cell(ws, tot, 4, f"=SUM(D{first}:D{last})", "#,##0", bold=True, fill=TOTAL_FILL)
    cell(ws, tot, 5, f"=SUM(E{first}:E{last})", "0.0%", fill=TOTAL_FILL)
    for col, fmt in {6: "0.0", 8: "0.0", 10: "0.0%", 11: "0.0%", 12: "0.00"}.items():
        L = get_column_letter(col)
        cell(ws, tot, col, f"=SUMPRODUCT($D${first}:$D${last},{L}{first}:{L}{last})/$D${tot}", fmt, bold=True, fill=TOTAL_FILL)
    for col in (7, 9, 13):
        cell(ws, tot, col, "", fill=TOTAL_FILL)
    diverging(ws, f"G{first}:G{last}", -12, 12)
    diverging(ws, f"I{first}:I{last}", -22, 22, reverse=True)
    note(ws, tot + 1, "Risk score = how far burnout is above average + how far productivity is below average (in standard deviations). High productivity does not cancel out high burnout.")

    ch = bar_chart("Average burnout risk and productivity by group", horizontal=False, height=8, width=18)
    ch.add_data(Reference(ws, min_col=6, min_row=r0, max_row=last), titles_from_data=True)
    ch.add_data(Reference(ws, min_col=8, min_row=r0, max_row=last), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=first, max_row=last))
    solid(ch.series[0], RED)
    solid(ch.series[1], BLUE)
    ch.y_axis.scaling.min, ch.y_axis.scaling.max = 0, 100
    ch.y_axis.title = "Score (0-100)"
    ws.add_chart(ch, f"A{tot + 3}")

    pr0 = section(ws, tot + 21, "Problem profile of each group",
                  "Standard deviations from the all-employee average; positive (red) = worse than average. Source: reports/03_segment_problem_scores.csv.")
    header(ws, pr0, ["Code", "Group", *problem_cols])
    prob_row = {}
    for i, code in enumerate(codes):
        r = pr0 + 1 + i
        prob_row[code] = r
        cell(ws, r, 1, code, bold=True)
        cell(ws, r, 2, f"=B{seg_row[code]}", color=INK_2, wrap=True)
        for j, pc in enumerate(problem_cols):
            cell(ws, r, 3 + j, round(float(problem.loc[code, pc]), 4), NUM_SIGNED, align="center")
    diverging(ws, f"C{pr0 + 1}:{get_column_letter(2 + len(problem_cols))}{pr0 + len(codes)}", -1.2, 1.2)
    widths(ws, {"A": 9, "B": 34, "C": 14, "D": 14, "E": 14, "F": 14, "G": 14, "H": 15, "I": 15, "J": 13, "K": 15, "L": 15, "M": 11})
    ws.freeze_panes = f"C{r0 + 1}"

    # ------------------------------------------------------------------ Workplace problems
    ws2 = wb.create_sheet("Workplace problems", 0)
    title(ws2, "Workplace problems: what goes with burnout and low productivity",
          "Pearson correlations on 5 million employees · common warning signs")
    input_cell(ws2, "C4", 0.05, "0.00", "Minimum |r| to count as a link")
    a0 = section(ws2, 6, "Correlation of each factor with the two outcomes",
                 "Source: reports/02_driver_correlation.csv. The 'direction' columns are formulas using the threshold in C4.")
    header(ws2, a0, ["Factor", "Factor group", "r with burnout", "Direction (burnout)", "r with productivity", "Direction (productivity)"])
    d_sorted = drivers.reindex(drivers["burnout_risk"].sort_values(ascending=False).index)
    for i, (_, row) in enumerate(d_sorted.iterrows()):
        r = a0 + 1 + i
        cell(ws2, r, 1, row["factor"])
        cell(ws2, r, 2, row["group"], color=INK_2)
        cell(ws2, r, 3, round(float(row["burnout_risk"]), 4), NUM_SIGNED, align="center")
        cell(ws2, r, 4, f'=IF(ABS(C{r})<$C$4,"–",IF(C{r}>0,"Higher burnout","Lower burnout"))', color=INK_2)
        cell(ws2, r, 5, round(float(row["productivity_score"]), 4), NUM_SIGNED, align="center")
        cell(ws2, r, 6, f'=IF(ABS(E{r})<$C$4,"–",IF(E{r}>0,"Higher productivity","Lower productivity"))', color=INK_2)
    a_last = a0 + len(d_sorted)
    diverging(ws2, f"C{a0 + 1}:C{a_last}", -0.55, 0.55)
    diverging(ws2, f"E{a0 + 1}:E{a_last}", -0.55, 0.55, reverse=True)
    for k, (col, ttl, harmful_pos) in enumerate([(3, "Correlation with burnout risk", True), (5, "Correlation with productivity", False)]):
        ch = bar_chart(ttl, height=10.5, width=13)
        ch.add_data(Reference(ws2, min_col=col, min_row=a0, max_row=a_last), titles_from_data=True)
        ch.set_categories(Reference(ws2, min_col=1, min_row=a0 + 1, max_row=a_last))
        ch.legend = None
        ser = ch.series[0]
        ser.graphicalProperties.line.noFill = True
        for i, (_, row) in enumerate(d_sorted.iterrows()):
            v = float(row["burnout_risk" if col == 3 else "productivity_score"])
            dp = DataPoint(idx=i)
            solid(dp, RED_DARK if (v > 0) == harmful_pos else BLUE_DARK)
            ser.dPt.append(dp)
        ch.x_axis.scaling.orientation = "maxMin"
        ws2.add_chart(ch, f"{'H' if k == 0 else 'O'}{a0}")

    b0 = section(ws2, a_last + 3, "Common warning signs",
                 "Source: reports/02_red_flags.csv. Share = employees / total on the 'Groups' sheet.")
    header(ws2, b0, ["Warning sign", "Employees", "Share"])
    for i, (flag, row) in enumerate(red.iterrows()):
        r = b0 + 1 + i
        cell(ws2, r, 1, flag)
        cell(ws2, r, 2, int(row["employees"]), "#,##0")
        cell(ws2, r, 3, f"=B{r}/{SEG}!$D${tot}", "0.0%")
    b_last = b0 + len(red)
    ws2.conditional_formatting.add(f"C{b0 + 1}:C{b_last}", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color=BLUE))
    note(ws2, b_last + 1, "Thresholds (for example sleep under 6 hours, stress of 8+) are analysis choices, defined in src/config.py.")
    widths(ws2, {"A": 32, "B": 18, "C": 14, "D": 20, "E": 16, "F": 22})
    ws2.freeze_panes = f"A{a0 + 1}"

    # ------------------------------------------------------------------ Warning signs by group
    ws3 = wb.create_sheet("Warning signs by group")
    title(ws3, "Warning signs by group",
          "Which signs are concentrated in a few groups, and which are at the same level everywhere (→ company-wide measures)")
    input_cell(ws3, "C4", 5, "0.0", "Max gap for 'all groups' (pp)")
    c0 = section(ws3, 6, "Share of each group", "Source: reports/03_segment_red_flags.csv. The 'Gap' and 'Scope' columns are formulas.")
    seg_cols = [c for c in flags_seg.columns if c in codes]
    header(ws3, c0, ["Warning sign", *seg_cols, "All", "Gap (pp)", "Scope of action"])
    last_seg = get_column_letter(1 + len(seg_cols))
    gap_col = get_column_letter(3 + len(seg_cols))
    scope_col = get_column_letter(4 + len(seg_cols))
    for i, (flag, row) in enumerate(flags_seg.iterrows()):
        r = c0 + 1 + i
        cell(ws3, r, 1, flag)
        for j, code in enumerate(seg_cols):
            cell(ws3, r, 2 + j, round(float(row[code]) / 100, 6), "0.0%", align="center")
        cell(ws3, r, 2 + len(seg_cols), round(float(row["All"]) / 100, 6), "0.0%", align="center", bold=True)
        cell(ws3, r, 3 + len(seg_cols), f"=(MAX(B{r}:{last_seg}{r})-MIN(B{r}:{last_seg}{r}))*100", "0.0", align="center")
        cell(ws3, r, 4 + len(seg_cols), f'=IF({gap_col}{r}<$C$4,"Company-wide","By group")')
    c_last = c0 + len(flags_seg)
    sequential(ws3, f"B{c0 + 1}:{get_column_letter(2 + len(seg_cols))}{c_last}")
    ws3.conditional_formatting.add(f"A{c0 + 1}:{scope_col}{c_last}",
                                   FormulaRule(formula=[f'${scope_col}{c0 + 1}="Company-wide"'], font=Font(name=FONT, bold=True, color=RED_DARK)))
    note(ws3, c_last + 1, "Rows in bold red have almost the same rate in every group, so grouping does not help to target them; they call for company-wide measures.")
    widths(ws3, {"A": 32, **{get_column_letter(2 + j): 10 for j in range(len(seg_cols) + 1)}, gap_col: 12, scope_col: 18})
    ws3.freeze_panes = f"B{c0 + 1}"

    # ------------------------------------------------------------------ Groups within a risk level
    ws4 = wb.create_sheet("Groups within a risk level")
    title(ws4, "Comparing groups that share a risk level",
          "Does the same risk level mean the same problem? Outcomes, problem profile, behaviour and correlations inside each group")
    input_cell(ws4, "C4", 0.05, "0.00", "Min |r| to flag a sign change")
    input_cell(ws4, "C5", 0.10, "0.00", "Min |r| for a reliable lever")
    levels: dict[str, list[str]] = {}
    for s_ in meta["segments"]:
        levels.setdefault(s_["level"], []).append(s_["code"])
    row = 7
    for lvl, groups in levels.items():
        if len(groups) < 2:
            put(ws4, f"A{row}", f"The '{lvl}' level has only {groups[0]}; see the 'Groups' sheet for its profile.", font=font(italic=True, color=INK_2))
            row += 2
            continue
        row = risk_block(ws4, row, lvl, groups, seg_by_code, seg_row, prob_row, problem_cols, raw, wc, group_of, tot, SEG)
    widths(ws4, {"A": 30, "B": 16, "C": 13, "D": 13, "E": 13, "F": 13, "G": 13, "H": 13, "I": 13, "J": 13, "K": 13, "L": 22, "M": 22})
    ws4.freeze_panes = "B7"

    # ------------------------------------------------------------------ Actions
    ws5 = wb.create_sheet("Actions")
    title(ws5, "Starting points for action", "The actions are hypotheses to test with a comparison group, then measure again with the listed KPIs")
    g0 = section(ws5, 4, "By group (ordered by priority)", "Source: reports/05_playbook.csv. Share links to the 'Groups' sheet.")
    header(ws5, g0, ["Priority", "Code", "Group", "Risk level", "Share", "Main problems", "Strengths", "Suggested actions", "KPIs to track"])
    for i, code in enumerate(codes):
        r = g0 + 1 + i
        sg = seg_by_code[code]
        pb = playbook.loc[code]
        kpis = "; ".join(KPI_BY_INDEX[p["index"]] for p in sg["problems"]) or "Keep current levels; use as a comparison group"
        cell(ws5, r, 1, i + 1, align="center")
        cell(ws5, r, 2, code, bold=True)
        cell(ws5, r, 3, sg["name"], wrap=True)
        cell(ws5, r, 4, sg["level"], wrap=True)
        cell(ws5, r, 5, f"={SEG}!E{seg_row[code]}", "0.0%")
        cell(ws5, r, 6, pb["main problems"].replace("; ", "\n"), wrap=True)
        cell(ws5, r, 7, pb["strengths"].replace("; ", "\n"), wrap=True)
        cell(ws5, r, 8, "\n".join(f"• {a}" for a in sg["actions"]), wrap=True)
        cell(ws5, r, 9, kpis, wrap=True)
        ws5.row_dimensions[r].height = 16 * max(2, len(sg["actions"]) + 1)
    cw0 = section(ws5, g0 + len(codes) + 3, "Company-wide", "Warning signs at almost the same rate in every group (see 'Warning signs by group').")
    header(ws5, cw0, ["Warning sign", "Share", "Gap between groups (pp)", "Company-wide action"])
    for i, it in enumerate(meta["company_wide"]):
        r = cw0 + 1 + i
        cell(ws5, r, 1, it["flag"])
        cell(ws5, r, 2, it["rate"] / 100, "0.0%")
        cell(ws5, r, 3, it["spread_pp"], "0.0", align="center")
        cell(ws5, r, 4, it["action"], wrap=True)
        ws5.row_dimensions[r].height = 30
    widths(ws5, {"A": 30, "B": 9, "C": 30, "D": 22, "E": 10, "F": 32, "G": 28, "H": 70, "I": 40})
    ws5.freeze_panes = f"C{g0 + 1}"

    # ------------------------------------------------------------------ Method & notes
    ws6 = wb.create_sheet("Method")
    title(ws6, "Method and limitations", "Short summary; code and details are in the notebook")
    kt = next(r for r in meta["k_table"] if r["k"] == meta["k"])
    rows = [
        ("Data", f"{meta['n_rows']:,} employees × 34 columns; synthetic dataset from Kaggle"),
        ("Source", KAGGLE_URL),
        ("Step 1", "Combine 25 measures into 5 problem scores: " + ", ".join(meta["index_labels"].values())),
        ("Step 2", "Weight each score by |r| with burnout and with productivity (both outcomes count equally)"),
        ("Step 3", f"Choose k = {meta['k']}: most stable (ARI of 0.8 or more across 5 runs) and best outcome separation among k = 3-6"),
        ("Step 4", "K-Means on the full data; checked against Gaussian Mixture and Ward clustering"),
        ("Stability across 5 runs (ARI)", round(kt["stability"], 3)),
        ("Stability with equal weights (ARI)", round(kt["stability_equal"], 3)),
        ("300k sample vs full data (ARI)", round(meta["ari_sample_vs_full"], 3)),
        ("K-Means vs Gaussian Mixture (ARI)", round(meta["ari_gmm"], 3)),
        ("K-Means vs Ward (ARI)", round(meta["ari_ward"], 3)),
        ("Silhouette", round(meta["silhouette"], 3)),
        ("eta² productivity / burnout", f"{meta['eta2']['productivity_score']:.3f} / {meta['eta2']['burnout_risk']:.3f}"),
        ("Limitation 1", "The data is synthetic: the input factors are almost unrelated to each other, which is rare in real data. Re-run on real HR data before making decisions."),
        ("Limitation 2", "Correlation is not causation."),
        ("Limitation 3", "The low silhouette means there are no natural clusters; the groups are a practical way to divide the risk space."),
        ("Limitation 4", "Correlations inside a group can change sign because of how the groups were formed (selection effect / Berkson's paradox)."),
        ("How to use this file", "The workbook uses formulas and recalculates when opened. Blue bold cells on a light-blue fill are inputs you can change."),
    ]
    header(ws6, 4, ["Item", "Detail"])
    for i, (k, v) in enumerate(rows):
        r = 5 + i
        cell(ws6, r, 1, k, bold=True)
        c = cell(ws6, r, 2, v, "0.000" if isinstance(v, float) else None, wrap=True, align="left")
        if k == "Source":
            c.hyperlink = KAGGLE_URL
            c.font = font(color=BLUE_DARK, underline="single")
    widths(ws6, {"A": 38, "B": 110})

    # ------------------------------------------------------------------ Summary (first sheet)
    ws0 = wb.create_sheet("Summary", 0)
    title(ws0, "Burnout and productivity: what problems do 5 million employees report?",
          "Companion to the analysis notebook · synthetic data from Kaggle · key figures link to the 'Groups' sheet")
    header(ws0, 4, ["Key figure", "Value"])
    kpis = [
        ("Employees", f"={SEG}!D{tot}", "#,##0"),
        ("Average burnout risk (0-100)", f"={SEG}!F{tot}", "0.0"),
        ("Average productivity score (0-100)", f"={SEG}!H{tot}", "0.0"),
        ("Share with burnout risk 70+", f"={SEG}!J{tot}", "0.0%"),
        ("Share in the low productivity category", f"={SEG}!K{tot}", "0.0%"),
        ("Warning signs per person (out of 11)", f"={SEG}!L{tot}", "0.00"),
        ("Productivity gap, highest vs lowest group", f"=MAX({SEG}!H{first}:H{last})-MIN({SEG}!H{first}:H{last})", "0.0"),
        ("Burnout gap, highest vs lowest group", f"=MAX({SEG}!F{first}:F{last})-MIN({SEG}!F{first}:F{last})", "0.0"),
    ]
    for i, (k, f, fmt) in enumerate(kpis):
        cell(ws0, 5 + i, 1, k)
        cell(ws0, 5 + i, 2, f, fmt, bold=True, align="right")
    n1 = seg_by_code[codes[0]]
    n4 = max((s_ for s_ in meta["segments"] if s_["level"] == "High"), key=lambda s_: s_["productivity"])
    top_b = drivers["burnout_risk"].sort_values(ascending=False).head(2)
    top_p = drivers["productivity_score"].sort_values(ascending=False).head(2)
    fl = red["share %"]
    insights = [
        f"Burnout and productivity are linked to different factors. Burnout goes with {drivers.loc[top_b.index[0], 'factor'].lower()} (r {top_b.iloc[0]:.2f}) "
        f"and {drivers.loc[top_b.index[1], 'factor'].lower()} ({top_b.iloc[1]:.2f}); productivity goes with {drivers.loc[top_p.index[0], 'factor'].lower()} "
        f"({top_p.iloc[0]:.2f}) and {drivers.loc[top_p.index[1], 'factor'].lower()} ({top_p.iloc[1]:.2f}).",
        f"Common problems: {fl.iloc[0]:.0f}% use devices late at night, {fl.loc['Sleep under 6 h']:.0f}% sleep under 6 hours, and about 30% report high stress or high emotional exhaustion.",
        "The outcomes barely differ by job title or work mode (less than 0.1 points between occupations); the differences are in individual behaviour.",
        f"{n1['code']} ({n1['name'].lower()}) has the highest risk: burnout {n1['burnout']:.1f}, productivity {n1['productivity']:.1f}.",
        f"The 'High' level ({', '.join(levels['High'])}) contains three different main problems; {n4['code']} combines high productivity ({n4['productivity']:.1f}) with high burnout ({n4['burnout']:.1f}).",
        "Short sleep and high stress are at the same level in every group, so they need company-wide measures.",
    ]
    i0 = section(ws0, 15, "Main findings")
    for i, t in enumerate(insights):
        c = ws0.cell(row=i0 + i, column=1, value=f"{i + 1}. {t}")
        c.font = font()
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws0.merge_cells(start_row=i0 + i, start_column=1, end_row=i0 + i, end_column=6)
        ws0.row_dimensions[i0 + i].height = 30
    s0 = section(ws0, i0 + len(insights) + 1, "Sheets in this file")
    guide = [
        ("Workplace problems", "Which factors go with burnout and productivity; common warning signs"),
        ("Groups", "The six employee groups: size, outcomes, problem profile"),
        ("Warning signs by group", "Which signs are concentrated in some groups and which are shared by all"),
        ("Groups within a risk level", "How groups at the same risk level differ; correlations inside each group"),
        ("Actions", "Suggested actions and KPIs for each group and for the whole company"),
        ("Method", "How the groups were built, validation figures and limitations"),
    ]
    for i, (sh, desc) in enumerate(guide):
        c = cell(ws0, s0 + i, 1, sh, bold=True)
        c.hyperlink = f"#'{sh}'!A1"
        c.font = font(bold=True, color=BLUE_DARK, underline="single")
        cell(ws0, s0 + i, 2, desc, color=INK_2)
        ws0.merge_cells(start_row=s0 + i, start_column=2, end_row=s0 + i, end_column=6)
    widths(ws0, {"A": 44, "B": 16, "C": 16, "D": 16, "E": 16, "F": 16})

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Saved -> {OUTPUT.relative_to(ROOT)} · sheets: {', '.join(wb.sheetnames)}")


def risk_block(ws, row, lvl, groups, seg_by_code, seg_row, prob_row, problem_cols, raw, wc, group_of, tot, SEG) -> int:
    """One comparison block for a risk level with two or more groups; returns the next free row."""
    n = len(groups)
    gcols = [get_column_letter(2 + i) for i in range(n)]
    segs = [seg_by_code[g] for g in groups]
    causes = "; ".join(f"{s_['code']}: {s_['problems'][0]['text'] if s_['problems'] else 'strength - ' + s_['strengths'][0]['text']}" for s_ in segs)
    put(ws, f"A{row}", f"'{lvl}' risk level · {', '.join(groups)}", font=font(size=13, bold=True, color=RED_DARK))
    put(ws, f"A{row + 1}", f"Main issue of each group → {causes}.", font=font(color=INK_2))
    row += 3

    # (a) outcomes, linked to the Groups sheet
    row = section(ws, row, "a. Outcomes", "Linked to the 'Groups' sheet. The last column is the gap between the highest and lowest group.")
    header(ws, row, ["Measure", *groups, "All", "Gap between groups"])
    metrics = [("Share of employees", "E", "0.0%"), ("Burnout avg", "F", "0.0"), ("% burnout 70+", "J", "0.0%"),
               ("Productivity avg", "H", "0.0"), ("% low productivity", "K", "0.0%"), ("Warning signs / person", "L", "0.00")]
    for i, (lab_, col, fmt) in enumerate(metrics):
        r = row + 1 + i
        cell(ws, r, 1, lab_)
        for j, g in enumerate(groups):
            cell(ws, r, 2 + j, f"={SEG}!{col}{seg_row[g]}", fmt, align="center")
        cell(ws, r, 2 + n, f"={SEG}!{col}{tot}", fmt, align="center", bold=True)
        cell(ws, r, 3 + n, f"=MAX({gcols[0]}{r}:{gcols[-1]}{r})-MIN({gcols[0]}{r}:{gcols[-1]}{r})", fmt, align="center")
    row += len(metrics) + 2

    # (b) problem profile + chart
    row = section(ws, row, "b. Problem profile (standard deviations, positive = worse)", "Linked to the problem-profile table on the 'Groups' sheet.")
    header(ws, row, ["Problem score", *groups])
    b_first = row + 1
    for i, pc in enumerate(problem_cols):
        r = b_first + i
        cell(ws, r, 1, pc)
        for j, g in enumerate(groups):
            cell(ws, r, 2 + j, f"={SEG}!{get_column_letter(3 + i)}{prob_row[g]}", NUM_SIGNED, align="center")
    b_last = b_first + len(problem_cols) - 1
    diverging(ws, f"B{b_first}:{gcols[-1]}{b_last}", -1.2, 1.2)
    row = b_last + 3

    # (c) behaviours sorted by spread
    row = section(ws, row, "c. Behaviours that differ most",
                  "Source: reports/04_segment_raw_means.csv. Gap (SD) = (highest - lowest group) / all-employee standard deviation.")
    header(ws, row, ["Factor", *groups, "All", "SD", "Gap (SD)", "Factor group"])
    drivers_ = [d for d in raw.index if d in group_of]
    zs = raw.loc[drivers_, groups].sub(raw.loc[drivers_, "All"], axis=0).div(raw.loc[drivers_, "SD"], axis=0)
    order = (zs.max(axis=1) - zs.min(axis=1)).sort_values(ascending=False).index
    c_first = row + 1
    sd_col, sp_col = get_column_letter(3 + n), get_column_letter(4 + n)
    for i, d in enumerate(order):
        r = c_first + i
        cell(ws, r, 1, LABELS[d])
        for j, g in enumerate(groups):
            cell(ws, r, 2 + j, round(float(raw.loc[d, g]), 4), "0.00", align="center")
        cell(ws, r, 2 + n, round(float(raw.loc[d, "All"]), 4), "0.00", align="center", bold=True)
        cell(ws, r, 3 + n, round(float(raw.loc[d, "SD"]), 4), "0.00", color=INK_2, align="center")
        cell(ws, r, 4 + n, f"=(MAX({gcols[0]}{r}:{gcols[-1]}{r})-MIN({gcols[0]}{r}:{gcols[-1]}{r}))/{sd_col}{r}", "0.00", align="center")
        cell(ws, r, 5 + n, group_of[d], color=INK_2)
    c_last = c_first + len(order) - 1
    ws.conditional_formatting.add(f"{sp_col}{c_first}:{sp_col}{c_last}", DataBarRule(start_type="num", start_value=0, end_type="max", color=BLUE))
    row = c_last + 3

    # (d) correlations inside each group
    row = section(ws, row, "d. Correlations inside each group",
                  "Source: reports/04_within_group_correlation.csv. Bold italic cells with a border: opposite sign to all employees (selection effect). "
                  "Last two columns: factors with the same direction in every group (formulas using C4 and C5).")
    labels = [*(f"{g} · burnout" for g in groups), "All · burnout", *(f"{g} · productivity" for g in groups), "All · productivity",
              "Reliable lever (burnout)", "Reliable lever (productivity)"]
    header(ws, row, ["Factor", *labels])
    wide = wc.pivot(index="driver", columns="group")
    keep = [d for d in drivers_ if (wide.loc[d, [(o, g) for o in ("burnout_risk", "productivity_score") for g in [*groups, "All"]]].abs() >= 0.05).any()]
    keep.sort(key=lambda d: -max(abs(wide.loc[d, ("burnout_risk", "All")]), abs(wide.loc[d, ("productivity_score", "All")])))
    d_first = row + 1
    b_cols = [get_column_letter(2 + j) for j in range(n)]
    b_all = get_column_letter(2 + n)
    p_cols = [get_column_letter(3 + n + j) for j in range(n)]
    p_all = get_column_letter(3 + 2 * n)
    lev_b, lev_p = get_column_letter(4 + 2 * n), get_column_letter(5 + 2 * n)
    for i, d in enumerate(keep):
        r = d_first + i
        cell(ws, r, 1, LABELS[d])
        for j, g in enumerate(groups):
            cell(ws, r, 2 + j, round(float(wide.loc[d, ("burnout_risk", g)]), 4), NUM_SIGNED, align="center")
            cell(ws, r, 3 + n + j, round(float(wide.loc[d, ("productivity_score", g)]), 4), NUM_SIGNED, align="center")
        cell(ws, r, 2 + n, round(float(wide.loc[d, ("burnout_risk", "All")]), 4), NUM_SIGNED, align="center", bold=True)
        cell(ws, r, 3 + 2 * n, round(float(wide.loc[d, ("productivity_score", "All")]), 4), NUM_SIGNED, align="center", bold=True)
        for cols_, ref, out_col, pos_txt, neg_txt in [(b_cols, b_all, lev_b, "✓ higher burnout", "✓ lower burnout"),
                                                       (p_cols, p_all, lev_p, "✓ higher productivity", "✓ lower productivity")]:
            conds = [f"ABS({ref}{r})>=$C$4"] + [f"ABS({c}{r})>=$C$5" for c in cols_] + [f"SIGN({c}{r})=SIGN({ref}{r})" for c in cols_]
            cell(ws, r, column_index_from_string(out_col), f'=IF(AND({",".join(conds)}),IF({ref}{r}>0,"{pos_txt}","{neg_txt}"),"")', color=INK_2)
    d_last = d_first + len(keep) - 1
    diverging(ws, f"B{d_first}:{b_all}{d_last}", -0.55, 0.55)
    diverging(ws, f"{p_cols[0]}{d_first}:{p_all}{d_last}", -0.55, 0.55, reverse=True)
    ring = Side(style="thin", color=INK)
    for cols_, ref in [(b_cols, b_all), (p_cols, p_all)]:
        tl = f"{cols_[0]}{d_first}"
        ws.conditional_formatting.add(f"{cols_[0]}{d_first}:{cols_[-1]}{d_last}", FormulaRule(
            formula=[f"AND(ABS({tl})>=$C$4,OR(ABS(${ref}{d_first})<0.005,SIGN({tl})<>SIGN(${ref}{d_first})))"],
            font=Font(name=FONT, bold=True, italic=True), border=Border(left=ring, right=ring, top=ring, bottom=ring)))
    note(ws, d_last + 1, "Why do some cells change sign? The groups were formed from these same measures, so inside a group the measures are tied to each "
                         "other and some correlations weaken or reverse. Only factors with the same direction in every group should guide decisions.")
    return d_last + 4


if __name__ == "__main__":
    main()

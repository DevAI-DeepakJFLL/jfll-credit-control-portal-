"""
Production-grade Excel Generation Engine for Ageing Report Automation.
Produces FINAL AGEING REPORT.xlsx with native Excel formulas and Sheet2 summary.
"""
import io
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from backend.app.automations.ageing_report.models import CustomerAgeingSummary

# Corporate Theme Colors
NAVY_HEADER = "1F4E78"
ACCENT_BLUE = "2271B1"
LIGHT_GRAY_FILL = "F2F2F2"
SUBTOTAL_BG = "E7EEF8"
WHITE = "FFFFFF"
BORDER_GRAY = "D9D9D9"

HEADER_COLUMNS = [
    ("FU Person", 14),
    ("Sales Person", 22),
    ("Branch", 14),
    ("Customer", 38),
    ("Payment Terms", 15),
    ("Outstanding", 18),
    ("Receive", 15),
    ("Balance", 18),
    ("Advance", 15),
    ("Remark", 32),
    ("0-30", 16),
    ("31-45", 16),
    ("46-60", 16),
    ("61-90", 16),
    ("91-180", 16),
    ("181-240", 16),
    ("241-365", 16),
    ("above 365", 16),
    ("Grand Total", 18),
    ("", 4),              # Col 20: Empty spacer column
    ("This IATA", 16),
    ("Last IATA", 16),
    ("ON A/C", 18)
]

def generate_ageing_report_excel(
    customers: List[CustomerAgeingSummary],
    batch_title: str = "Ageing Report"
) -> io.BytesIO:
    """
    Generates a production-grade multi-sheet Excel file matching FINAL AGEING REPORT.xlsx:
    - Sheet 'FINAL': Full customer table with Row 1 =SUBTOTAL(9, ...) and Row 3+ =SUM(...) formulas.
    - Sheet 'Sheet2': Follow-Up Person and Branch rollup summary.
    """
    wb = openpyxl.Workbook()
    # Remove default empty sheet
    wb.remove(wb.active)

    # 1. Sheet: FINAL
    ws_final = wb.create_sheet(title="FINAL")
    ws_final.views.sheetView[0].showGridLines = True

    # Styling elements
    font_bold = Font(name="Calibri", size=11, bold=True)
    font_bold_white = Font(name="Calibri", size=11, bold=True, color=WHITE)
    font_regular = Font(name="Calibri", size=11)
    font_subtotal = Font(name="Calibri", size=11, bold=True, color="0D233A")
    fill_header = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
    fill_subtotal = PatternFill(start_color=SUBTOTAL_BG, end_color=SUBTOTAL_BG, fill_type="solid")
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    thin_border_side = Side(border_style="thin", color=BORDER_GRAY)
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    num_fmt_curr = "#,##0.00"

    num_rows = len(customers)
    last_row = max(3, num_rows + 2)

    # Row 1: Executive Subtotal Banner
    ws_final.row_dimensions[1].height = 24
    subtotal_cols = {
        6: "F",   # Outstanding
        7: "G",   # Receive
        8: "H",   # Balance
        9: "I",   # Advance
        11: "K",  # 0-30
        12: "L",  # 31-45
        13: "M",  # 46-60
        14: "N",  # 61-90
        15: "O",  # 91-180
        16: "P",  # 181-240
        17: "Q",  # 241-365
        18: "R",  # above 365
        19: "S",  # Grand Total
        21: "U",  # This IATA
        22: "V",  # Last IATA
        23: "W"   # ON A/C
    }

    for c_idx in range(1, len(HEADER_COLUMNS) + 1):
        cell = ws_final.cell(row=1, column=c_idx)
        cell.fill = fill_subtotal
        cell.border = border_cell
        if c_idx in subtotal_cols:
            col_letter = subtotal_cols[c_idx]
            cell.value = f"=SUBTOTAL(9,{col_letter}3:{col_letter}{last_row})"
            cell.font = font_subtotal
            cell.alignment = align_right
            cell.number_format = num_fmt_curr
        else:
            cell.value = None

    # Row 2: Headers
    ws_final.row_dimensions[2].height = 26
    for c_idx, (header_name, col_width) in enumerate(HEADER_COLUMNS, start=1):
        cell = ws_final.cell(row=2, column=c_idx, value=header_name)
        cell.font = font_bold_white
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_cell
        ws_final.column_dimensions[get_column_letter(c_idx)].width = col_width

    # Rows 3 to N: Customer Data Records
    for idx, c in enumerate(customers):
        r = idx + 3
        ws_final.row_dimensions[r].height = 20

        # Text fields
        ws_final.cell(row=r, column=1, value=c.fu_person).alignment = align_left
        ws_final.cell(row=r, column=2, value=c.sales_person).alignment = align_left
        ws_final.cell(row=r, column=3, value=c.branch).alignment = align_left
        ws_final.cell(row=r, column=4, value=c.customer_name).alignment = align_left
        ws_final.cell(row=r, column=5, value=c.payment_terms).alignment = align_left

        # Formula: Outstanding =SUM(L{r}:R{r})
        c_out = ws_final.cell(row=r, column=6, value=f"=SUM(L{r}:R{r})")
        c_out.alignment = align_right
        c_out.number_format = num_fmt_curr
        c_out.font = font_bold

        # Receive
        c_rec = ws_final.cell(row=r, column=7, value=c.received)
        c_rec.alignment = align_right
        c_rec.number_format = num_fmt_curr

        # Formula: Balance =+F{r}-G{r}
        c_bal = ws_final.cell(row=r, column=8, value=f"=+F{r}-G{r}")
        c_bal.alignment = align_right
        c_bal.number_format = num_fmt_curr
        c_bal.font = font_bold

        # Advance
        c_adv = ws_final.cell(row=r, column=9, value=c.advance if c.advance != 0 else None)
        c_adv.alignment = align_right
        c_adv.number_format = num_fmt_curr

        # Remark
        ws_final.cell(row=r, column=10, value=c.remark or "").alignment = align_left

        # 8 Buckets: K (11) through R (18)
        buckets = [
            c.bucket_0_30,
            c.bucket_31_45,
            c.bucket_46_60,
            c.bucket_61_90,
            c.bucket_91_180,
            c.bucket_181_240,
            c.bucket_241_365,
            c.bucket_above_365
        ]
        for b_idx, b_val in enumerate(buckets, start=11):
            cell_b = ws_final.cell(row=r, column=b_idx, value=b_val)
            cell_b.alignment = align_right
            cell_b.number_format = num_fmt_curr

        # Formula: Grand Total =SUM(K{r}:R{r})
        c_grand = ws_final.cell(row=r, column=19, value=f"=SUM(K{r}:R{r})")
        c_grand.alignment = align_right
        c_grand.number_format = num_fmt_curr
        c_grand.font = font_bold

        # Col 20: Spacer
        ws_final.cell(row=r, column=20, value=None)

        # Formula: This IATA =L{r}
        c_this = ws_final.cell(row=r, column=21, value=f"=L{r}")
        c_this.alignment = align_right
        c_this.number_format = num_fmt_curr

        # Formula: Last IATA =M{r}
        c_last = ws_final.cell(row=r, column=22, value=f"=M{r}")
        c_last.alignment = align_right
        c_last.number_format = num_fmt_curr

        # ON A/C
        c_onac = ws_final.cell(row=r, column=23, value=c.on_ac if c.on_ac != 0 else None)
        c_onac.alignment = align_right
        c_onac.number_format = num_fmt_curr

        # Set borders for all row cells
        for c_idx in range(1, len(HEADER_COLUMNS) + 1):
            ws_final.cell(row=r, column=c_idx).border = border_cell

    # Freeze panes at A3 so top 2 rows remain visible during scrolling
    ws_final.freeze_panes = "A3"
    # Auto-filter enabled on Row 2
    ws_final.auto_filter.ref = f"A2:W{last_row}"

    # 2. Sheet: Sheet2 (Rollup Summary)
    ws_s2 = wb.create_sheet(title="Sheet2")
    ws_s2.views.sheetView[0].showGridLines = True

    # Build FU summaries
    import collections
    fu_summary = collections.defaultdict(lambda: {"out": 0.0, "rec": 0.0, "bal": 0.0})
    fu_branch_summary = collections.defaultdict(lambda: collections.defaultdict(lambda: {"out": 0.0, "rec": 0.0, "bal": 0.0}))

    for c in customers:
        fu = c.fu_person or "Other"
        b = c.branch or "Mumbai"
        fu_summary[fu]["out"] += c.outstanding
        fu_summary[fu]["rec"] += c.received
        fu_summary[fu]["bal"] += c.balance

        fu_branch_summary[fu][b]["out"] += c.outstanding
        fu_branch_summary[fu][b]["rec"] += c.received
        fu_branch_summary[fu][b]["bal"] += c.balance

    # Section 1: FU Person Rollup
    ws_s2.cell(row=3, column=1, value="Row Labels").font = font_bold
    ws_s2.cell(row=3, column=2, value=" Outstanding").font = font_bold
    ws_s2.cell(row=3, column=3, value=" Receive").font = font_bold
    ws_s2.cell(row=3, column=4, value=" Balance").font = font_bold

    cur_r = 4
    for fu_name in ["Nikita", "Siddhesh", "Vaibhav", "Other"]:
        if fu_name in fu_summary:
            data = fu_summary[fu_name]
            ws_s2.cell(row=cur_r, column=1, value=fu_name).font = font_bold
            c1 = ws_s2.cell(row=cur_r, column=2, value=data["out"])
            c2 = ws_s2.cell(row=cur_r, column=3, value=data["rec"])
            c3 = ws_s2.cell(row=cur_r, column=4, value=data["bal"])
            for cell in (c1, c2, c3):
                cell.number_format = num_fmt_curr
                cell.alignment = align_right
            cur_r += 1

    # Grand Total row
    ws_s2.cell(row=cur_r, column=1, value="Grand Total").font = font_bold
    ws_s2.cell(row=cur_r, column=2, value=f"=SUM(B4:B{cur_r-1})").font = font_bold
    ws_s2.cell(row=cur_r, column=3, value=f"=SUM(C4:C{cur_r-1})").font = font_bold
    ws_s2.cell(row=cur_r, column=4, value=f"=SUM(D4:D{cur_r-1})").font = font_bold
    for col_i in (2, 3, 4):
        c_gt = ws_s2.cell(row=cur_r, column=col_i)
        c_gt.number_format = num_fmt_curr
        c_gt.alignment = align_right

    cur_r += 2

    # Section 2: FU Person broken down by Branch
    ws_s2.cell(row=cur_r, column=1, value="Row Labels").font = font_bold
    ws_s2.cell(row=cur_r, column=2, value=" Outstanding").font = font_bold
    ws_s2.cell(row=cur_r, column=3, value=" Receive").font = font_bold
    ws_s2.cell(row=cur_r, column=4, value=" Balance").font = font_bold
    cur_r += 1

    start_breakdown_r = cur_r
    for fu_name in ["Nikita", "Siddhesh", "Vaibhav", "Other"]:
        if fu_name in fu_branch_summary:
            ws_s2.cell(row=cur_r, column=1, value=fu_name).font = font_bold
            f_data = fu_summary[fu_name]
            c1 = ws_s2.cell(row=cur_r, column=2, value=f_data["out"])
            c2 = ws_s2.cell(row=cur_r, column=3, value=f_data["rec"])
            c3 = ws_s2.cell(row=cur_r, column=4, value=f_data["bal"])
            for cell in (c1, c2, c3):
                cell.font = font_bold
                cell.number_format = num_fmt_curr
                cell.alignment = align_right
            cur_r += 1

            for b_name, b_data in sorted(fu_branch_summary[fu_name].items()):
                ws_s2.cell(row=cur_r, column=1, value=f"  {b_name}")
                cb1 = ws_s2.cell(row=cur_r, column=2, value=b_data["out"])
                cb2 = ws_s2.cell(row=cur_r, column=3, value=b_data["rec"])
                cb3 = ws_s2.cell(row=cur_r, column=4, value=b_data["bal"])
                for cell in (cb1, cb2, cb3):
                    cell.number_format = num_fmt_curr
                    cell.alignment = align_right
                cur_r += 1

    # Final Grand Total for breakdown
    ws_s2.cell(row=cur_r, column=1, value="Grand Total").font = font_bold
    tot_out = sum(fu_summary[f]["out"] for f in fu_summary)
    tot_rec = sum(fu_summary[f]["rec"] for f in fu_summary)
    tot_bal = sum(fu_summary[f]["bal"] for f in fu_summary)
    c1 = ws_s2.cell(row=cur_r, column=2, value=tot_out)
    c2 = ws_s2.cell(row=cur_r, column=3, value=tot_rec)
    c3 = ws_s2.cell(row=cur_r, column=4, value=tot_bal)
    for cell in (c1, c2, c3):
        cell.font = font_bold
        cell.number_format = num_fmt_curr
        cell.alignment = align_right

    # Format column widths on Sheet2
    ws_s2.column_dimensions["A"].width = 24
    ws_s2.column_dimensions["B"].width = 20
    ws_s2.column_dimensions["C"].width = 16
    ws_s2.column_dimensions["D"].width = 20

    # Save to in-memory buffer
    output_stream = io.BytesIO()
    wb.save(output_stream)
    output_stream.seek(0)
    return output_stream

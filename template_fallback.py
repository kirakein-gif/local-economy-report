from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

SUMMARY_SHEETS = ["1-1. 총괄(공사)", "1-2. 총괄(용역)", "1-3. 총괄(물품)"]
REVIEW_SHEET = "1-4. 기초자료(지역경제활성화)"

BLUE = "2563EB"
NAVY = "172033"
LINE = "D9E2EF"
SOFT = "EFF6FF"
WHITE = "FFFFFF"
MUTED = "667085"
GREEN = "059669"


def _base_font(size=10, bold=False, color=NAVY):
    return Font(name="맑은 고딕", size=size, bold=bold, color=color)


def _thin_border():
    s = Side(style="thin", color=LINE)
    return Border(left=s, right=s, top=s, bottom=s)


def _style_cell(cell, fill=None, bold=False, color=NAVY, align="center", size=10):
    cell.font = _base_font(size, bold, color)
    cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
    cell.border = _thin_border()
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)


def _setup_summary(ws, title, material=False):
    max_col = 29 if material else 13
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_col)
    ws["A1"] = title
    ws["A1"].font = _base_font(15, True, NAVY)
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 30

    for c, w in {1:6, 2:12, 3:22, 4:12, 5:12}.items():
        ws.column_dimensions[get_column_letter(c)].width = w
    for c in range(6, max_col + 1):
        ws.column_dimensions[get_column_letter(c)].width = 11

    base_headers = ["순", "지역", "기관명", "급별", "목적물"]
    for c, text in enumerate(base_headers, 1):
        ws.cell(4, c).value = text
        _style_cell(ws.cell(4, c), BLUE, True, WHITE)

    groups = [(6, "충남도내(관내)"), (8, "충남도내(관외)"), (10, "타시도"), (12, "합계")]
    if material:
        groups += [(14, "교육용-관내"), (16, "교육용-관외"), (18, "교육용-타시도"), (20, "교육용-합계"),
                   (22, "도서-관내"), (24, "도서-관외"), (26, "도서-타시도"), (28, "도서-합계")]
    for start, name in groups:
        ws.cell(4, start).value = f"{name}\n건수"
        ws.cell(4, start + 1).value = f"{name}\n금액"
        _style_cell(ws.cell(4, start), SOFT, True, BLUE)
        _style_cell(ws.cell(4, start + 1), SOFT, True, BLUE)

    data_row = 6 if material else 5
    for c in range(1, max_col + 1):
        _style_cell(ws.cell(data_row, c), WHITE, False, NAVY)
    ws.row_dimensions[4].height = 42
    ws.row_dimensions[data_row].height = 26
    ws.freeze_panes = f"A{data_row}"
    ws.sheet_view.showGridLines = False


def _setup_review(ws):
    headers = ["순", "지역", "기관명", "급별", "목적물", "계약방법", "견적/경쟁방법", "계약명", "계약일자", "계약금액", "업체명", "주소", "소재지", "구입목적", "비고"]
    ws.merge_cells("A1:O1")
    ws["A1"] = "붙임1-4. 지역경제활성화 추진 실적"
    ws["A1"].font = _base_font(15, True, NAVY)
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 30
    ws.merge_cells("A4:I4")
    ws["A4"] = "검토가 필요한 항목을 확인한 후 파일을 다시 업로드하세요."
    ws["A4"].font = _base_font(9, False, MUTED)
    ws.merge_cells("J4:O4")
    ws["J4"] = "지역경제활성화 자동 집계 시스템"
    ws["J4"].font = _base_font(9, False, MUTED)
    ws["J4"].alignment = Alignment(horizontal="right")

    for c, text in enumerate(headers, 1):
        ws.cell(6, c).value = text
        _style_cell(ws.cell(6, c), BLUE, True, WHITE)
    ws.row_dimensions[6].height = 34
    for c in range(1, 16):
        _style_cell(ws.cell(7, c), WHITE, False, NAVY)
    ws.row_dimensions[7].height = 24
    widths = [6,10,20,10,10,14,18,42,13,14,22,42,16,18,24]
    for c, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(c)].width = width
    ws.freeze_panes = "A7"
    ws.auto_filter.ref = "A6:O7"
    ws.sheet_view.showGridLines = False


def build_fallback_workbook():
    wb = Workbook()
    ws = wb.active
    ws.title = SUMMARY_SHEETS[0]
    _setup_summary(ws, "붙임 1-1. 지역경제활성화 추진 실적(총괄+공사)")
    ws2 = wb.create_sheet(SUMMARY_SHEETS[1])
    _setup_summary(ws2, "붙임 1-2. 지역경제활성화 추진 실적(총괄+용역)")
    ws3 = wb.create_sheet(SUMMARY_SHEETS[2])
    _setup_summary(ws3, "붙임 1-3. 지역경제활성화 추진 실적(총괄+물품)", material=True)
    ws4 = wb.create_sheet(REVIEW_SHEET)
    _setup_review(ws4)
    return wb


def load_halfyear_template_safe(template_path):
    """정상 템플릿이면 사용하고, 배포 중 바이너리가 손상됐으면 즉시 내장 기본양식으로 복구합니다."""
    try:
        p = Path(template_path)
        if p.exists() and p.stat().st_size > 10000:
            wb = load_workbook(p)
            required = set(SUMMARY_SHEETS + [REVIEW_SHEET])
            if required.issubset(set(wb.sheetnames)):
                return wb
    except Exception:
        pass
    return build_fallback_workbook()

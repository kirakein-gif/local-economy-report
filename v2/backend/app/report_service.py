import os
from copy import copy
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

from .excel_service import (
    COMPETITION_METHODS,
    CONTRACT_METHODS,
    PURCHASE_PURPOSES,
    apply_address_overrides,
    combine_workbooks,
    extract_source_metadata,
    format_money,
    records_from_source,
)

REVIEW_SHEET = "1-4. 기초자료(지역경제활성화)"


def _template_path():
    configured = os.getenv("HALFYEAR_TEMPLATE_PATH", "").strip()
    if configured:
        return Path(configured)

    container_path = Path("/app/templates/halfy_report_template.xlsx")
    if container_path.exists():
        return container_path

    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "halfy_report_template.xlsx"


def _load_halfyear_template():
    path = _template_path()
    if not path.exists():
        raise FileNotFoundError(f"반기보고서 공식 템플릿 파일을 찾을 수 없습니다: {path}")
    return load_workbook(path)


def _find_last_data_row(ws, start_row=7, scan_limit=5000):
    last = start_row - 1
    limit = min(ws.max_row, scan_limit)
    blank_run = 0
    for row in range(start_row, limit + 1):
        has_value = any(
            ws.cell(row, col).value not in (None, "")
            for col in range(1, min(ws.max_column, 15) + 1)
        )
        if has_value:
            last = row
            blank_run = 0
        else:
            blank_run += 1
            if last >= start_row and blank_run >= 100:
                break
    return last


def _clear_data_values(ws, end_row):
    for row in range(7, max(7, end_row) + 1):
        for col in range(1, 16):
            ws.cell(row, col).value = None


def _reset_review_validations(ws, end_row):
    ws.data_validations.dataValidation = []
    end_row = max(end_row, 1000)
    validations = [
        ("D", ["학교(유)", "학교(초)", "학교(중)", "학교(고)", "학교(특수)", "교육지원청", "직속기관"]),
        ("E", ["공사", "용역", "물품"]),
        ("F", CONTRACT_METHODS),
        ("G", COMPETITION_METHODS),
        ("M", ["충남도내(관내)", "충남도내(관외)", "타시도"]),
        ("N", PURCHASE_PURPOSES),
    ]
    for col, items in validations:
        validation = DataValidation(
            type="list",
            formula1='"' + ",".join(items) + '"',
            allow_blank=True,
        )
        ws.add_data_validation(validation)
        validation.add(f"{col}7:{col}{end_row}")


def _amount_label(target_amount):
    if target_amount >= 10000 and target_amount % 10000 == 0:
        return f"{target_amount // 10000:,}만원"
    return f"{target_amount:,}원"


def _review_title(report_year, report_label, target_amount, start_date, end_date):
    return (
        f"붙임1-4. {report_year}년 {report_label} 지역경제활성화 추진 실적"
        f"[기준(건당 {_amount_label(target_amount)} 이상), "
        f"{start_date.year}. {start_date.month}. {start_date.day}. ~ "
        f"{end_date.year}. {end_date.month}. {end_date.day}.]"
    )


def _apply_template_row_style(ws, row, template_row=7):
    if row == template_row:
        return
    ws.row_dimensions[row].height = ws.row_dimensions[template_row].height
    for col in range(1, 16):
        src = ws.cell(template_row, col)
        dst = ws.cell(row, col)
        if src.has_style:
            dst._style = copy(src._style)
        if src.number_format:
            dst.number_format = src.number_format
        dst.alignment = copy(src.alignment)


def _write_review_records(ws, records, target_region, institution_name, school_level):
    for index, record in enumerate(records, start=1):
        row = index + 6
        _apply_template_row_style(ws, row)
        values = [
            index,
            target_region,
            institution_name,
            school_level,
            record.get("목적물", ""),
            record.get("계약방법", ""),
            record.get("견적경쟁방법", ""),
            record.get("계약명", ""),
            record.get("계약일자", ""),
            format_money(record.get("계약금액", 0)),
            record.get("업체명", ""),
            record.get("주소", ""),
            record.get("소재지", ""),
            record.get("구입목적", ""),
            record.get("비고", ""),
        ]
        for col, value in enumerate(values, start=1):
            ws.cell(row, col).value = value
        ws.cell(row, 10).number_format = "#,##0"
        if isinstance(ws.cell(row, 9).value, datetime):
            ws.cell(row, 9).number_format = "yyyy-mm-dd"


def build_review_workbook(
    file_payloads,
    target_amount,
    target_region,
    business_addresses=None,
    row_addresses=None,
    report_year=2026,
    report_label="상반기",
    start_date=date(2026, 1, 1),
    end_date=date(2026, 7, 31),
):
    df, headers = combine_workbooks(file_payloads)
    filled_count = apply_address_overrides(
        df,
        headers,
        business_addresses=business_addresses,
        row_addresses=row_addresses,
    )
    institution_name, school_level = extract_source_metadata(df, headers)
    records = records_from_source(df, headers, target_amount, target_region)

    workbook = _load_halfyear_template()
    for name in list(workbook.sheetnames):
        if name != REVIEW_SHEET:
            workbook.remove(workbook[name])

    ws = workbook[REVIEW_SHEET]
    old_last = _find_last_data_row(ws)
    _clear_data_values(ws, max(old_last, len(records) + 6))
    ws["A1"] = _review_title(
        report_year, report_label, target_amount, start_date, end_date
    )
    ws["A4"] = (
        "◑ 자료관리목록 업로드 → 주소 보완 → 검토용 기초자료 생성 → "
        "사용자 검토 → 최종 반기보고서 생성"
    )
    ws["J4"] = "지역경제활성화 자동 집계 시스템 · Cloud Run v2"
    _write_review_records(ws, records, target_region, institution_name, school_level)
    _reset_review_validations(ws, len(records) + 6)
    ws.auto_filter.ref = f"A6:O{max(7, len(records) + 6)}"
    ws.freeze_panes = "A7"

    output = BytesIO()
    workbook.save(output)

    unresolved = sum(1 for record in records if not str(record.get("주소", "")).strip())
    return {
        "bytes": output.getvalue(),
        "record_count": len(records),
        "filled_address_count": filled_count,
        "unresolved_address_count": unresolved,
        "institution": institution_name,
        "school_level": school_level,
    }

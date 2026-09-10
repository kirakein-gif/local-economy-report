import json
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .address_service import (
    MAX_BULK_BUSINESSES,
    bulk_lookup_addresses,
    get_api_key,
    lookup_address,
)
from .cache import address_cache
from .excel_service import CHUNGNAM_REGIONS, DEFAULT_TARGET_AMOUNT, inspect_workbooks
from .manual_store import backend_name as manual_backend_name
from .manual_store import save_manual_address
from .report_service import build_final_halfyear_report, build_review_workbook

APP_VERSION = "2.0.0-alpha.4"
MAX_FILES = 20
MAX_FILE_BYTES = 30 * 1024 * 1024
MAX_TOTAL_BYTES = 120 * 1024 * 1024


class AddressLookupRequest(BaseModel):
    biz_no: str
    force_refresh: bool = False


class AddressBulkLookupRequest(BaseModel):
    biz_numbers: list[str] = Field(default_factory=list)
    force_refresh: bool = False


class ManualAddressSaveRequest(BaseModel):
    biz_no: str
    address: str
    company_name: str = ""


app = FastAPI(
    title="지역경제활성화 자동 집계 시스템 API",
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Content-Disposition",
        "X-Record-Count",
        "X-Filled-Address-Count",
        "X-Unresolved-Address-Count",
        "X-Region",
        "X-Institution",
        "X-Corrected-Location-Count",
        "X-Purpose-Correction-Count",
    ],
)


async def _read_upload_payloads(files):
    if not files:
        raise HTTPException(status_code=400, detail="엑셀 파일을 1개 이상 선택해 주세요.")
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"한 번에 최대 {MAX_FILES}개 파일까지 업로드할 수 있습니다.",
        )

    payloads = []
    total_bytes = 0
    for upload in files:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in {".xlsx", ".xls"}:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다: {upload.filename}",
            )

        content = await upload.read()
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"파일 1개는 30MB를 넘을 수 없습니다: {upload.filename}",
            )

        total_bytes += len(content)
        if total_bytes > MAX_TOTAL_BYTES:
            raise HTTPException(
                status_code=413,
                detail="전체 업로드 용량은 120MB를 넘을 수 없습니다.",
            )
        payloads.append(content)

    return payloads


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "local-economy-report-v2",
        "version": APP_VERSION,
        "address_cache": address_cache.status(),
        "manual_address_backend": manual_backend_name(),
        "public_data_api_configured": bool(get_api_key()),
    }


@app.get("/api/config")
def config():
    return {
        "regions": CHUNGNAM_REGIONS,
        "default_target_amount": DEFAULT_TARGET_AMOUNT,
        "version": APP_VERSION,
        "max_bulk_businesses": MAX_BULK_BUSINESSES,
        "address_cache": address_cache.status(),
        "manual_address_backend": manual_backend_name(),
        "public_data_api_configured": bool(get_api_key()),
        "default_report": {
            "year": 2026,
            "label": "상반기",
            "start_date": "2026-01-01",
            "end_date": "2026-07-31",
        },
    }


@app.post("/api/address/lookup")
def address_lookup(payload: AddressLookupRequest):
    result = lookup_address(payload.biz_no, force_refresh=payload.force_refresh)
    if result.get("invalid"):
        raise HTTPException(status_code=422, detail="10자리 사업자등록번호가 필요합니다.")
    return result


@app.post("/api/address/bulk")
def address_bulk_lookup(payload: AddressBulkLookupRequest):
    if not payload.biz_numbers:
        raise HTTPException(status_code=400, detail="조회할 사업자등록번호가 없습니다.")

    try:
        return bulk_lookup_addresses(
            payload.biz_numbers,
            force_refresh=payload.force_refresh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/manual/save")
def manual_address_save(payload: ManualAddressSaveRequest):
    try:
        return save_manual_address(
            payload.biz_no,
            payload.address,
            payload.company_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/prepare/inspect")
async def prepare_inspect(
    files: list[UploadFile] = File(...),
    target_amount: int = Form(DEFAULT_TARGET_AMOUNT),
    region_mode: str = Form("auto"),
    manual_region: str = Form(""),
):
    if target_amount < 0:
        raise HTTPException(status_code=400, detail="기준 금액은 0원 이상이어야 합니다.")

    payloads = await _read_upload_payloads(files)
    selected_region = manual_region if region_mode == "manual" else ""

    try:
        return inspect_workbooks(
            payloads,
            target_amount=target_amount,
            manual_region=selected_region,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"엑셀 분석 중 오류가 발생했습니다: {exc}",
        ) from exc


@app.post("/api/prepare/review")
async def prepare_review(
    files: list[UploadFile] = File(...),
    target_amount: int = Form(DEFAULT_TARGET_AMOUNT),
    region_mode: str = Form("auto"),
    manual_region: str = Form(""),
    address_overrides_json: str = Form("{}"),
    report_year: int = Form(2026),
    report_label: str = Form("상반기"),
    start_date: str = Form("2026-01-01"),
    end_date: str = Form("2026-07-31"),
):
    if target_amount < 0:
        raise HTTPException(status_code=400, detail="기준 금액은 0원 이상이어야 합니다.")

    payloads = await _read_upload_payloads(files)

    try:
        overrides = json.loads(address_overrides_json or "{}")
        if not isinstance(overrides, dict):
            raise ValueError("주소 보완 데이터 형식이 올바르지 않습니다.")
        business_addresses = overrides.get("business", {}) or {}
        row_addresses = overrides.get("rows", {}) or {}
        if not isinstance(business_addresses, dict) or not isinstance(row_addresses, dict):
            raise ValueError("주소 보완 데이터 형식이 올바르지 않습니다.")

        report_start = date.fromisoformat(start_date)
        report_end = date.fromisoformat(end_date)
        if report_end < report_start:
            raise ValueError("보고 종료일은 시작일보다 빠를 수 없습니다.")

        inspection = inspect_workbooks(
            payloads,
            target_amount=target_amount,
            manual_region=manual_region if region_mode == "manual" else "",
        )
        target_region = inspection["target_region"]

        result = build_review_workbook(
            payloads,
            target_amount=target_amount,
            target_region=target_region,
            business_addresses=business_addresses,
            row_addresses=row_addresses,
            report_year=report_year,
            report_label=report_label,
            start_date=report_start,
            end_date=report_end,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"검토용 Excel 생성 중 오류가 발생했습니다: {exc}",
        ) from exc

    filename = f"{report_year}_{report_label}_{target_region}_지역경제활성화_검토용.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        BytesIO(result["bytes"]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "X-Record-Count": str(result["record_count"]),
            "X-Filled-Address-Count": str(result["filled_address_count"]),
            "X-Unresolved-Address-Count": str(result["unresolved_address_count"]),
        },
    )


@app.post("/api/final/report")
async def final_report(file: UploadFile = File(...)):
    payloads = await _read_upload_payloads([file])
    try:
        result = build_final_halfyear_report(payloads[0])
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"최종 반기보고서 생성 중 오류가 발생했습니다: {exc}",
        ) from exc

    region = result.get("region", "") or "지역"
    institution = result.get("institution", "") or "기관"
    year = result.get("year", "") or "반기"
    label = result.get("label", "반기")
    filename = f"{year}_{label}_{region}_{institution}_지역경제활성화_최종보고서.xlsx"
    encoded_filename = quote(filename)
    purpose_corrections = int(result.get("blank_purpose", 0)) + int(result.get("invalid_purpose", 0))

    return StreamingResponse(
        BytesIO(result["bytes"]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "X-Record-Count": str(result["record_count"]),
            "X-Region": quote(region),
            "X-Institution": quote(institution),
            "X-Corrected-Location-Count": str(result.get("corrected_location", 0)),
            "X-Purpose-Correction-Count": str(purpose_corrections),
        },
    )


STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "message": "지역경제활성화 v2 API가 실행 중입니다.",
            "docs": "/docs",
        }

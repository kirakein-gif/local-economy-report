from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .excel_service import CHUNGNAM_REGIONS, DEFAULT_TARGET_AMOUNT, inspect_workbooks

APP_VERSION = "2.0.0-alpha.1"
MAX_FILES = 20
MAX_FILE_BYTES = 30 * 1024 * 1024
MAX_TOTAL_BYTES = 120 * 1024 * 1024

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
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "local-economy-report-v2",
        "version": APP_VERSION,
    }


@app.get("/api/config")
def config():
    return {
        "regions": CHUNGNAM_REGIONS,
        "default_target_amount": DEFAULT_TARGET_AMOUNT,
        "version": APP_VERSION,
    }


@app.post("/api/prepare/inspect")
async def prepare_inspect(
    files: list[UploadFile] = File(...),
    target_amount: int = Form(DEFAULT_TARGET_AMOUNT),
    region_mode: str = Form("auto"),
    manual_region: str = Form(""),
):
    if not files:
        raise HTTPException(status_code=400, detail="엑셀 파일을 1개 이상 선택해 주세요.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"한 번에 최대 {MAX_FILES}개 파일까지 업로드할 수 있습니다.")
    if target_amount < 0:
        raise HTTPException(status_code=400, detail="기준 금액은 0원 이상이어야 합니다.")

    payloads = []
    total_bytes = 0

    for upload in files:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in {".xlsx", ".xls"}:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {upload.filename}")

        content = await upload.read()
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail=f"파일 1개는 30MB를 넘을 수 없습니다: {upload.filename}")

        total_bytes += len(content)
        if total_bytes > MAX_TOTAL_BYTES:
            raise HTTPException(status_code=413, detail="전체 업로드 용량은 120MB를 넘을 수 없습니다.")
        payloads.append(content)

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
        raise HTTPException(status_code=500, detail=f"엑셀 분석 중 오류가 발생했습니다: {exc}") from exc


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

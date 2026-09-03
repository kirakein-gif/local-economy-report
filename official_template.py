import base64
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

BASE_DIR = Path(__file__).resolve().parent
PART_DIR = BASE_DIR / "template_parts"
REQUIRED_SHEETS = [
    "1-1. 총괄(공사)",
    "1-2. 총괄(용역)",
    "1-3. 총괄(물품)",
    "1-4. 기초자료(지역경제활성화)",
]


def load_official_halfyear_template():
    """사용자가 제공한 확정 양식을 보존한 내장 템플릿을 복원합니다.

    원본 확정 양식의 앞 100행 범위를 그대로 보존한 검증본을 4개 Base64
    조각으로 저장해 두고 실행 시 메모리에서 XLSX로 복원합니다. 이렇게 하면
    GitHub/Streamlit 배포 과정에서 바이너리 xlsx 파일이 손상되어도 양식이
    변하지 않습니다.
    """
    chunks = []
    for i in range(1, 5):
        path = PART_DIR / f"official_{i:02d}.b64"
        if not path.exists():
            raise FileNotFoundError(f"공식 반기양식 내장 데이터가 없습니다: {path.name}")
        chunks.append(path.read_text(encoding="utf-8").strip())

    try:
        raw = base64.b64decode("".join(chunks), validate=True)
        wb = load_workbook(BytesIO(raw))
    except Exception as exc:
        raise RuntimeError(f"공식 반기양식을 복원하지 못했습니다: {exc}") from exc

    if not set(REQUIRED_SHEETS).issubset(set(wb.sheetnames)):
        raise RuntimeError("공식 반기양식의 4개 시트를 확인하지 못했습니다.")

    ws1 = wb["1-1. 총괄(공사)"]
    ws3 = wb["1-3. 총괄(물품)"]
    ws4 = wb["1-4. 기초자료(지역경제활성화)"]
    if ws1["F2"].value != "총괄" or ws3["N2"].value != "구입목적별 " or "<작성방법>" not in str(ws4["A2"].value or ""):
        raise RuntimeError("복원된 반기양식이 확정 양식 구조와 일치하지 않습니다.")

    return wb

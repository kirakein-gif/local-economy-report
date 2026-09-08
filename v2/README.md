# 지역경제활성화 자동 집계 시스템 v2

기존 Streamlit 운영판을 유지하면서 React + FastAPI + Google Cloud Run 구조로 전환하기 위한 별도 버전입니다.

## 현재 구현 범위

- React 업무앱형 UI
- 여러 Excel 파일 업로드
- 지역 자동 감지 / 직접 선택
- 계약금액 기준 설정
- 보고 대상 건수 계산
- 주소 누락 건수 계산
- API 조회 가능 업체 추출
- 나라장터 → 학교장터(S2B) → 공정위 → 지역화폐 주소 조회
- 단건 / 일괄 FastAPI 주소조회 API
- 성공 결과 24시간 캐시, 실패 결과 15분 캐시
- Firestore 공유 캐시 선택 지원
- 주소조회 출처별 결과 및 캐시 재사용 건수 UI 표시
- FastAPI 헬스체크 및 설정 API
- 단일 Docker 컨테이너 구성

## 주소 캐시 구조

로컬 개발에서는 기본적으로 프로세스 메모리 캐시를 사용합니다.

Cloud Run 운영에서는 다음 환경변수를 사용해 Firestore 공유 캐시를 켭니다.

```text
ADDRESS_CACHE_BACKEND=firestore
ADDRESS_CACHE_COLLECTION=local_economy_address_cache
ADDRESS_LOOKUP_WORKERS=2
```

Cloud Run 인스턴스가 여러 개 생겨도 Firestore에 저장된 업체 주소를 재사용하므로 동일 업체에 대한 공공 API 중복 호출을 줄일 수 있습니다.

공공데이터포털 서비스키는 소스에 넣지 않고 다음 환경변수 또는 Secret Manager로 주입합니다.

```text
DATAGOKR=...
```

## 주요 API

- `GET /api/health`
- `GET /api/config`
- `POST /api/prepare/inspect`
- `POST /api/address/lookup`
- `POST /api/address/bulk`

일괄 주소조회는 한 번에 최대 200개 업체까지 받으며, 병렬 조회 수는 기본 2개로 제한합니다.

## 다음 연결 대상

1. 조회된 주소를 업로드 원본 데이터에 실제 반영
2. 사용자 수동 주소 보완 UI 및 공유 저장소 이전
3. 검토용 Excel 생성
4. 기존 `excel_reports.py`의 반기보고서 4시트 최종 생성 연결
5. 실제 Cloud Run 시험 배포
6. 동시 사용자 부하 테스트 후 concurrency / max instances 조정

## 전환 원칙

- `main` 브랜치의 현재 Streamlit 운영판은 유지합니다.
- v2 기능은 `cloudrun-v2` 브랜치에서 별도로 개발합니다.
- 기존 Streamlit 결과와 v2 결과가 일치하는지 단계별로 비교합니다.
- 충분히 검증되기 전까지 대표 접속 주소는 변경하지 않습니다.

## 1차 Cloud Run 권장값

- 리전: asia-northeast3 (서울)
- CPU: 1 vCPU
- 메모리: 1 GiB
- 인스턴스당 동시 요청: 4
- 최대 인스턴스: 20
- 요청 제한시간: 300초
- 주소 병렬조회 workers: 2

초기값이며 실제 엑셀 크기, API 호출량, 피크 동시 사용자 수를 측정한 뒤 조정합니다.

# 지역경제활성화 자동 집계 시스템 v2

기존 Streamlit 운영판을 유지하면서 React + FastAPI + Google Cloud Run 구조로 전환하기 위한 별도 버전입니다.

## 현재 구현 범위

- React 업무앱형 UI
- 여러 Excel 파일 업로드
- 지역 자동 감지 / 직접 선택
- 계약금액 기준 설정
- 보고 대상 건수 계산
- 주소 누락 건수 계산
- API 조회 가능 후보 건수 계산
- 주소 완성률 표시
- FastAPI 헬스체크 및 설정 API
- 단일 Docker 컨테이너 구성

## 다음 연결 대상

1. 기존 address_api.py 주소조회 로직을 Streamlit 의존성 없이 서비스 계층으로 이전
2. API 결과 공유 캐시 적용
3. 수동 주소 보완 화면 연결
4. 검토용 Excel 생성 연결
5. 기존 excel_reports.py의 반기보고서 4시트 최종 생성 연결
6. 동시 사용자 부하 테스트 후 Cloud Run concurrency / max instances 조정

## 전환 원칙

- main 브랜치의 현재 Streamlit 운영판은 유지합니다.
- v2 기능은 cloudrun-v2 브랜치에서 별도로 개발합니다.
- 기존 Streamlit 결과와 v2 결과가 일치하는지 단계별로 비교합니다.
- 충분히 검증되기 전까지 대표 접속 주소는 변경하지 않습니다.

## 1차 Cloud Run 권장값

- 리전: asia-northeast3 (서울)
- CPU: 1 vCPU
- 메모리: 1 GiB
- 인스턴스당 동시 요청: 4
- 최대 인스턴스: 20
- 요청 제한시간: 300초

이 값은 초기값이며 실제 엑셀 크기, API 호출량, 피크 동시 사용자 수를 측정한 뒤 조정합니다.

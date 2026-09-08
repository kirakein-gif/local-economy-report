import { useEffect, useMemo, useState } from "react";

const fallbackRegions = [
  "천안", "아산", "공주", "보령", "서산", "논산", "계룡", "당진",
  "금산", "부여", "서천", "청양", "홍성", "예산", "태안",
];

function formatNumber(value) {
  return new Intl.NumberFormat("ko-KR").format(Number(value || 0));
}

export default function App() {
  const [mode, setMode] = useState("prepare");
  const [files, setFiles] = useState([]);
  const [regions, setRegions] = useState(fallbackRegions);
  const [regionMode, setRegionMode] = useState("auto");
  const [manualRegion, setManualRegion] = useState("천안");
  const [targetAmount, setTargetAmount] = useState(500000);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/config")
      .then((response) => response.json())
      .then((data) => {
        if (Array.isArray(data.regions)) {
          setRegions(data.regions);
          setManualRegion(data.regions[0] || "천안");
        }
        if (data.default_target_amount) {
          setTargetAmount(data.default_target_amount);
        }
      })
      .catch(() => {});
  }, []);

  const totalSize = useMemo(
    () => files.reduce((sum, file) => sum + file.size, 0),
    [files]
  );

  async function inspectFiles() {
    if (!files.length) {
      setError("자료관리목록 엑셀 파일을 선택해 주세요.");
      return;
    }

    setBusy(true);
    setError("");
    setResult(null);

    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    form.append("target_amount", String(targetAmount));
    form.append("region_mode", regionMode);
    form.append("manual_region", manualRegion);

    try {
      const response = await fetch("/api/prepare/inspect", {
        method: "POST",
        body: form,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "파일 분석에 실패했습니다.");
      }
      setResult(data);
    } catch (err) {
      setError(err.message || "처리 중 오류가 발생했습니다.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">▦</div>
          <div>
            <strong>지역경제활성화</strong>
            <span>자동 집계 시스템</span>
          </div>
        </div>

        <div className="side-label">업무 메뉴</div>
        <button
          className={mode === "prepare" ? "nav-button active" : "nav-button"}
          onClick={() => setMode("prepare")}
        >
          <span>01</span>
          자료 집계 · 검토파일
        </button>
        <button
          className={mode === "final" ? "nav-button active" : "nav-button"}
          onClick={() => setMode("final")}
        >
          <span>02</span>
          반기보고서 최종작성
        </button>

        <div className="sidebar-spacer" />
        <div className="side-note">
          <b>v2 Cloud Run 전환판</b>
          <span>기존 Streamlit 운영판과 분리 개발 중</span>
        </div>
      </aside>

      <main className="main">
        <section className="hero">
          <div>
            <div className="eyebrow">CHUNGNAM · LOCAL ECONOMY</div>
            <h1>
              {mode === "prepare"
                ? "지역경제 활성화 계약자료 주소 정리"
                : "반기보고서 최종작성"}
            </h1>
            <p>
              {mode === "prepare"
                ? "계약자료를 업로드하면 대상 계약과 주소 보완 필요 건을 빠르게 확인합니다."
                : "검토 완료 파일을 이용한 최종 보고서 생성 기능을 연결할 예정입니다."}
            </p>
          </div>
          <div className="hero-status">
            <span className="status-dot" />
            Cloud Run 자동확장 구조
          </div>
        </section>

        {mode === "prepare" ? (
          <>
            <section className="grid two">
              <article className="card">
                <div className="card-head">
                  <div>
                    <span className="step">STEP 01</span>
                    <h2>자료 입력</h2>
                  </div>
                  <div className="icon-box">↥</div>
                </div>

                <label className="dropzone">
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    multiple
                    onChange={(event) => setFiles(Array.from(event.target.files || []))}
                  />
                  <strong>엑셀 파일을 선택하거나 끌어 놓으세요</strong>
                  <span>자료관리목록 Excel · 여러 파일 동시 선택 가능</span>
                </label>

                <div className="file-summary">
                  <span>선택 파일 <b>{files.length}개</b></span>
                  <span>총 용량 <b>{(totalSize / 1024 / 1024).toFixed(1)} MB</b></span>
                </div>
              </article>

              <article className="card">
                <div className="card-head">
                  <div>
                    <span className="step">STEP 02</span>
                    <h2>집계 기준</h2>
                  </div>
                  <div className="icon-box">⌁</div>
                </div>

                <div className="field">
                  <label>지역 선택 방식</label>
                  <div className="segmented">
                    <button
                      className={regionMode === "auto" ? "selected" : ""}
                      onClick={() => setRegionMode("auto")}
                    >
                      자동 선택
                    </button>
                    <button
                      className={regionMode === "manual" ? "selected" : ""}
                      onClick={() => setRegionMode("manual")}
                    >
                      직접 선택
                    </button>
                  </div>
                </div>

                <div className="field">
                  <label>대상 지역</label>
                  <select
                    value={manualRegion}
                    disabled={regionMode === "auto"}
                    onChange={(event) => setManualRegion(event.target.value)}
                  >
                    {regions.map((region) => (
                      <option value={region} key={region}>{region}</option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label>계약금액 기준</label>
                  <div className="money-input">
                    <input
                      type="number"
                      min="0"
                      step="10000"
                      value={targetAmount}
                      onChange={(event) => setTargetAmount(Number(event.target.value || 0))}
                    />
                    <span>원 이상</span>
                  </div>
                </div>
              </article>
            </section>

            <section className="action-row">
              <div>
                <strong>첫 번째 기능 연결 완료</strong>
                <span>업로드 파일을 서버에서 실제 분석하여 대상 건수와 주소 누락률을 계산합니다.</span>
              </div>
              <button className="primary" disabled={busy} onClick={inspectFiles}>
                {busy ? "분석 중..." : "파일 분석 시작"}
              </button>
            </section>

            {error && <div className="alert error">{error}</div>}

            {result && (
              <section className="results">
                <div className="result-title">
                  <div>
                    <span className="step">ANALYSIS</span>
                    <h2>분석 결과</h2>
                  </div>
                  <span className="pill">{result.target_region} 기준</span>
                </div>
                <div className="metric-grid">
                  <div className="metric">
                    <span>전체 데이터</span>
                    <strong>{formatNumber(result.row_count)}</strong>
                    <small>행</small>
                  </div>
                  <div className="metric">
                    <span>보고 대상</span>
                    <strong>{formatNumber(result.report_count)}</strong>
                    <small>건</small>
                  </div>
                  <div className="metric">
                    <span>주소 보완 필요</span>
                    <strong>{formatNumber(result.missing_address_count)}</strong>
                    <small>건</small>
                  </div>
                  <div className="metric">
                    <span>주소 완성률</span>
                    <strong>{result.address_completion_percent}</strong>
                    <small>%</small>
                  </div>
                </div>
                <div className="result-foot">
                  자동 감지 지역: <b>{result.auto_region}</b> · API 조회 후보:
                  <b> {formatNumber(result.api_lookup_candidate_count)}건</b> · 기준 금액:
                  <b> {formatNumber(result.target_amount)}원</b>
                </div>
              </section>
            )}
          </>
        ) : (
          <section className="empty-card">
            <div className="empty-icon">02</div>
            <h2>반기보고서 최종작성</h2>
            <p>다음 단계에서 기존 excel_reports.py의 4시트 보고서 생성 로직을 FastAPI로 연결합니다.</p>
          </section>
        )}
      </main>
    </div>
  );
}

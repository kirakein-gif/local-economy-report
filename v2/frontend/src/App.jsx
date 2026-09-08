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
  const [config, setConfig] = useState(null);
  const [busy, setBusy] = useState(false);
  const [addressBusy, setAddressBusy] = useState(false);
  const [addressResult, setAddressResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/config")
      .then((response) => response.json())
      .then((data) => {
        setConfig(data);
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
    setAddressResult(null);

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

  async function lookupAddresses() {
    const candidates = result?.lookup_candidates || [];
    if (!candidates.length) {
      setError("API로 조회할 주소 미확인 업체가 없습니다.");
      return;
    }

    setAddressBusy(true);
    setAddressResult(null);
    setError("");

    try {
      const response = await fetch("/api/address/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          biz_numbers: candidates.map((item) => item.biz_no),
          force_refresh: false,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "주소 조회에 실패했습니다.");
      }
      setAddressResult(data);
    } catch (err) {
      setError(err.message || "주소 조회 중 오류가 발생했습니다.");
    } finally {
      setAddressBusy(false);
    }
  }

  const cacheName = config?.address_cache?.active === "firestore" ? "Firestore 공유 캐시" : "메모리 캐시";

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
          <span>{cacheName}</span>
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
                <strong>계약자료 1차 분석</strong>
                <span>보고 대상, 주소 누락, API 조회 가능 업체를 먼저 확인합니다.</span>
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
                  <b> {formatNumber(result.api_lookup_candidate_count)}개 업체</b> · 기준 금액:
                  <b> {formatNumber(result.target_amount)}원</b>
                </div>

                <div className="address-action">
                  <div>
                    <span className="step">STEP 03</span>
                    <h3>공공 API 주소 조회</h3>
                    <p>나라장터 → 학교장터(S2B) → 공정위 → 지역화폐 순으로 조회합니다.</p>
                  </div>
                  <button
                    className="primary"
                    disabled={addressBusy || !result.api_lookup_candidate_count}
                    onClick={lookupAddresses}
                  >
                    {addressBusy
                      ? "주소 조회 중..."
                      : "주소 조회 시작 · " + formatNumber(result.api_lookup_candidate_count) + "개 업체"}
                  </button>
                </div>

                {addressResult && (
                  <div className="address-result">
                    <div className="address-summary">
                      <div>
                        <span>주소 확인</span>
                        <strong>{formatNumber(addressResult.found_count)}개</strong>
                      </div>
                      <div>
                        <span>미확인</span>
                        <strong>{formatNumber(addressResult.not_found_count)}개</strong>
                      </div>
                      <div>
                        <span>캐시 재사용</span>
                        <strong>{formatNumber(addressResult.cache_hit_count)}개</strong>
                      </div>
                      <div>
                        <span>캐시 방식</span>
                        <strong>{addressResult.cache?.active === "firestore" ? "공유" : "로컬"}</strong>
                      </div>
                    </div>
                    <div className="source-line">
                      나라장터 <b>{formatNumber(addressResult.source_counts?.["나라장터"])}</b>
                      <span>·</span>
                      학교장터 <b>{formatNumber(addressResult.source_counts?.["학교장터(S2B)"])}</b>
                      <span>·</span>
                      공정위 <b>{formatNumber(addressResult.source_counts?.["공정위 통신판매사업자"])}</b>
                      <span>·</span>
                      지역화폐 <b>{formatNumber(addressResult.source_counts?.["지역화폐 가맹점"])}</b>
                    </div>
                    <p className="next-note">
                      다음 단계에서 확인된 주소를 원본 데이터에 반영하고 검토용 Excel 다운로드까지 연결합니다.
                    </p>
                  </div>
                )}
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

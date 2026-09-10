import { useMemo, useState } from "react";

function formatNumber(value) {
  return new Intl.NumberFormat("ko-KR").format(Number(value || 0));
}

function downloadNameFromHeader(headerValue) {
  if (!headerValue) return "지역경제활성화_검토용.xlsx";
  const match = headerValue.match(/filename\*=UTF-8''([^;]+)/i);
  if (!match) return "지역경제활성화_검토용.xlsx";
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return "지역경제활성화_검토용.xlsx";
  }
}

export default function PrepareWorkflow({ config }) {
  const regions = config?.regions || [
    "천안", "아산", "공주", "보령", "서산", "논산", "계룡", "당진",
    "금산", "부여", "서천", "청양", "홍성", "예산", "태안",
  ];
  const [files, setFiles] = useState([]);
  const [regionMode, setRegionMode] = useState("auto");
  const [manualRegion, setManualRegion] = useState(regions[0] || "천안");
  const [targetAmount, setTargetAmount] = useState(config?.default_target_amount || 500000);
  const [result, setResult] = useState(null);
  const [addressResult, setAddressResult] = useState(null);
  const [manualAddresses, setManualAddresses] = useState({});
  const [saveStatus, setSaveStatus] = useState({});
  const [busy, setBusy] = useState(false);
  const [addressBusy, setAddressBusy] = useState(false);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewInfo, setReviewInfo] = useState(null);
  const [error, setError] = useState("");

  const totalSize = useMemo(
    () => files.reduce((sum, file) => sum + file.size, 0),
    [files]
  );

  const foundByBiz = useMemo(() => {
    const map = {};
    for (const item of addressResult?.results || []) {
      if (item.found && item.biz_no && item.address) map[item.biz_no] = item.address;
    }
    return map;
  }, [addressResult]);

  const unresolvedCandidates = useMemo(() => {
    return (result?.manual_candidates || []).filter((candidate) => {
      if (!candidate.biz_no) return true;
      return !foundByBiz[candidate.biz_no];
    });
  }, [result, foundByBiz]);

  const enteredManualCount = unresolvedCandidates.filter((item) =>
    String(manualAddresses[item.lookup_key] || "").trim()
  ).length;

  async function inspectFiles() {
    if (!files.length) {
      setError("자료관리목록 엑셀 파일을 선택해 주세요.");
      return;
    }

    setBusy(true);
    setError("");
    setResult(null);
    setAddressResult(null);
    setManualAddresses({});
    setSaveStatus({});
    setReviewInfo(null);

    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    form.append("target_amount", String(targetAmount));
    form.append("region_mode", regionMode);
    form.append("manual_region", manualRegion);

    try {
      const response = await fetch("/api/prepare/inspect", { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "파일 분석에 실패했습니다.");
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
      setAddressResult({
        found_count: 0,
        cache_hit_count: 0,
        manual_hit_count: 0,
        source_counts: {},
        results: [],
      });
      return;
    }

    setAddressBusy(true);
    setError("");
    setReviewInfo(null);
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
      if (!response.ok) throw new Error(data.detail || "주소 조회에 실패했습니다.");
      setAddressResult(data);
    } catch (err) {
      setError(err.message || "주소 조회 중 오류가 발생했습니다.");
    } finally {
      setAddressBusy(false);
    }
  }

  async function saveManual(candidate) {
    const address = String(manualAddresses[candidate.lookup_key] || "").trim();
    if (!candidate.biz_no || !address) return;

    setSaveStatus((current) => ({ ...current, [candidate.lookup_key]: "saving" }));
    try {
      const response = await fetch("/api/manual/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          biz_no: candidate.biz_no,
          address,
          company_name: candidate.company || "",
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "주소 저장에 실패했습니다.");
      setSaveStatus((current) => ({
        ...current,
        [candidate.lookup_key]: data.backend === "firestore" ? "shared" : "local",
      }));
    } catch (err) {
      setSaveStatus((current) => ({ ...current, [candidate.lookup_key]: "error" }));
      setError(err.message || "주소 저장 중 오류가 발생했습니다.");
    }
  }

  async function createReviewWorkbook() {
    if (!files.length || !result) return;

    const business = { ...foundByBiz };
    const rows = {};
    for (const candidate of unresolvedCandidates) {
      const address = String(manualAddresses[candidate.lookup_key] || "").trim();
      if (!address) continue;
      if (candidate.biz_no) business[candidate.biz_no] = address;
      else rows[String(candidate.row_id)] = address;
    }

    const report = config?.default_report || {
      year: 2026,
      label: "상반기",
      start_date: "2026-01-01",
      end_date: "2026-07-31",
    };

    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    form.append("target_amount", String(targetAmount));
    form.append("region_mode", regionMode);
    form.append("manual_region", manualRegion);
    form.append("address_overrides_json", JSON.stringify({ business, rows }));
    form.append("report_year", String(report.year));
    form.append("report_label", report.label);
    form.append("start_date", report.start_date);
    form.append("end_date", report.end_date);

    setReviewBusy(true);
    setError("");
    setReviewInfo(null);
    try {
      const response = await fetch("/api/prepare/review", { method: "POST", body: form });
      if (!response.ok) {
        let detail = "검토용 Excel 생성에 실패했습니다.";
        try {
          const data = await response.json();
          detail = data.detail || detail;
        } catch {}
        throw new Error(detail);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = downloadNameFromHeader(response.headers.get("Content-Disposition"));
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);

      setReviewInfo({
        recordCount: Number(response.headers.get("X-Record-Count") || 0),
        filledCount: Number(response.headers.get("X-Filled-Address-Count") || 0),
        unresolvedCount: Number(response.headers.get("X-Unresolved-Address-Count") || 0),
      });
    } catch (err) {
      setError(err.message || "검토용 Excel 생성 중 오류가 발생했습니다.");
    } finally {
      setReviewBusy(false);
    }
  }

  return (
    <>
      <section className="grid two">
        <article className="card">
          <div className="card-head">
            <div><span className="step">STEP 01</span><h2>자료 입력</h2></div>
            <div className="icon-box">↥</div>
          </div>
          <label className="dropzone">
            <input
              type="file"
              accept=".xlsx,.xls"
              multiple
              onChange={(event) => {
                setFiles(Array.from(event.target.files || []));
                setResult(null);
                setAddressResult(null);
                setReviewInfo(null);
              }}
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
            <div><span className="step">STEP 02</span><h2>집계 기준</h2></div>
            <div className="icon-box">⌁</div>
          </div>
          <div className="field">
            <label>지역 선택 방식</label>
            <div className="segmented">
              <button className={regionMode === "auto" ? "selected" : ""} onClick={() => setRegionMode("auto")}>자동 선택</button>
              <button className={regionMode === "manual" ? "selected" : ""} onClick={() => setRegionMode("manual")}>직접 선택</button>
            </div>
          </div>
          <div className="field">
            <label>대상 지역</label>
            <select value={manualRegion} disabled={regionMode === "auto"} onChange={(event) => setManualRegion(event.target.value)}>
              {regions.map((region) => <option value={region} key={region}>{region}</option>)}
            </select>
          </div>
          <div className="field">
            <label>계약금액 기준</label>
            <div className="money-input">
              <input type="number" min="0" step="10000" value={targetAmount} onChange={(event) => setTargetAmount(Number(event.target.value || 0))} />
              <span>원 이상</span>
            </div>
          </div>
        </article>
      </section>

      <section className="action-row">
        <div><strong>계약자료 1차 분석</strong><span>보고 대상, 주소 누락, API 조회 가능 업체를 확인합니다.</span></div>
        <button className="primary" disabled={busy} onClick={inspectFiles}>{busy ? "분석 중..." : "파일 분석 시작"}</button>
      </section>

      {error && <div className="alert error">{error}</div>}

      {result && (
        <section className="results">
          <div className="result-title">
            <div><span className="step">ANALYSIS</span><h2>분석 결과</h2></div>
            <span className="pill">{result.target_region} 기준</span>
          </div>
          <div className="metric-grid">
            <div className="metric"><span>전체 데이터</span><strong>{formatNumber(result.row_count)}</strong><small>행</small></div>
            <div className="metric"><span>보고 대상</span><strong>{formatNumber(result.report_count)}</strong><small>건</small></div>
            <div className="metric"><span>주소 보완 필요</span><strong>{formatNumber(result.missing_address_count)}</strong><small>건</small></div>
            <div className="metric"><span>주소 완성률</span><strong>{result.address_completion_percent}</strong><small>%</small></div>
          </div>
          <div className="result-foot">
            기관: <b>{result.institution || "자동 확인 실패"}</b> · 자동 감지 지역: <b>{result.auto_region}</b> · API 조회 후보: <b>{formatNumber(result.api_lookup_candidate_count)}개 업체</b> · 기준 금액: <b>{formatNumber(result.target_amount)}원</b>
          </div>

          <div className="address-action">
            <div><span className="step">STEP 03</span><h3>공공 API · 저장주소 조회</h3><p>저장주소를 먼저 확인한 뒤 나라장터 → 학교장터 → 공정위 → 지역화폐 순으로 조회합니다.</p></div>
            <button className="primary" disabled={addressBusy || !!addressResult} onClick={lookupAddresses}>
              {addressBusy ? "주소 조회 중..." : addressResult ? "주소 조회 완료" : `주소 조회 시작 · ${formatNumber(result.api_lookup_candidate_count)}개 업체`}
            </button>
          </div>

          {addressResult && (
            <>
              <div className="address-result">
                <div className="address-summary">
                  <div><span>주소 확인</span><strong>{formatNumber(addressResult.found_count)}개</strong></div>
                  <div><span>미확인</span><strong>{formatNumber(unresolvedCandidates.length)}개</strong></div>
                  <div><span>캐시 재사용</span><strong>{formatNumber(addressResult.cache_hit_count)}개</strong></div>
                  <div><span>저장주소 재사용</span><strong>{formatNumber(addressResult.manual_hit_count)}개</strong></div>
                </div>
                <div className="source-line">
                  저장주소 <b>{formatNumber(addressResult.source_counts?.["사용자 저장주소"])}</b><span>·</span>
                  나라장터 <b>{formatNumber(addressResult.source_counts?.["나라장터"])}</b><span>·</span>
                  학교장터 <b>{formatNumber(addressResult.source_counts?.["학교장터(S2B)"])}</b><span>·</span>
                  공정위 <b>{formatNumber(addressResult.source_counts?.["공정위 통신판매사업자"])}</b><span>·</span>
                  지역화폐 <b>{formatNumber(addressResult.source_counts?.["지역화폐 가맹점"])}</b>
                </div>
              </div>

              {unresolvedCandidates.length > 0 && (
                <div className="manual-panel">
                  <div className="manual-head">
                    <div><span className="step">STEP 04</span><h3>주소 미확인 업체 직접 보완</h3><p>입력 주소는 이번 검토파일에 반영되며, 사업자번호가 있으면 공유 저장할 수 있습니다.</p></div>
                    <span className="manual-progress">입력 {enteredManualCount}/{unresolvedCandidates.length}</span>
                  </div>
                  <div className="manual-list">
                    {unresolvedCandidates.map((candidate) => {
                      const status = saveStatus[candidate.lookup_key];
                      const value = manualAddresses[candidate.lookup_key] || "";
                      return (
                        <div className="manual-row" key={candidate.lookup_key}>
                          <div className="company-cell"><strong>{candidate.company || "업체명 확인불가"}</strong><span>{candidate.biz_no || "사업자번호 확인불가"}</span></div>
                          <input className="address-input" value={value} placeholder="확인한 업체 주소를 입력하세요" onChange={(event) => { setManualAddresses((current) => ({ ...current, [candidate.lookup_key]: event.target.value })); setReviewInfo(null); }} />
                          <div className="manual-buttons">
                            {candidate.biz_no && <a className="secondary-link" href={`https://bizno.net/?query=${encodeURIComponent(candidate.biz_no)}`} target="_blank" rel="noreferrer">업체조회</a>}
                            <button className="secondary" disabled={!candidate.biz_no || !String(value).trim() || status === "saving"} onClick={() => saveManual(candidate)}>
                              {status === "saving" ? "저장 중" : status === "shared" ? "공유 저장됨" : status === "local" ? "로컬 저장됨" : status === "error" ? "저장 재시도" : "주소 기억"}
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="review-panel">
                <div><span className="step">STEP 05</span><h3>검토용 기초자료 생성</h3><p>확인된 주소를 빈 주소에 반영한 뒤 공식 1-4 서식으로 생성합니다.</p></div>
                <button className="primary" disabled={reviewBusy} onClick={createReviewWorkbook}>{reviewBusy ? "Excel 생성 중..." : "검토용 Excel 다운로드"}</button>
              </div>

              {reviewInfo && (
                <div className={reviewInfo.unresolvedCount ? "alert warn" : "alert success"}>
                  검토용 파일 생성 완료 · 대상 {formatNumber(reviewInfo.recordCount)}건 · 주소 반영 {formatNumber(reviewInfo.filledCount)}건 · 주소 미확인 {formatNumber(reviewInfo.unresolvedCount)}건
                </div>
              )}
            </>
          )}
        </section>
      )}
    </>
  );
}

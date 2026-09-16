import { useMemo, useRef, useState } from "react";

const AMOUNT_PRESETS = [
  { value: 0, label: "0원" },
  { value: 100000, label: "10만원" },
  { value: 500000, label: "50만원" },
  { value: 1000000, label: "100만원" },
  { value: 10000000, label: "1,000만원" },
];

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

function isExcelFile(file) {
  return /\.(xlsx|xls)$/i.test(file?.name || "");
}

function Icon({ type, size = 28 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.9,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
  };

  if (type === "document") {
    return <svg {...common}><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h3M9 11h6M9 15h6M9 19h4"/></svg>;
  }
  if (type === "upload") {
    return <svg {...common} viewBox="0 0 64 54"><path d="M20 41H16a12 12 0 0 1-1-24 17 17 0 0 1 33-1 12 12 0 0 1 1 25h-5"/><path d="M32 48V27m-9 8 9-9 9 9"/></svg>;
  }
  if (type === "filter") {
    return <svg {...common}><path d="M4 5h16l-6.5 7.2V19l-3 1v-7.8z"/></svg>;
  }
  if (type === "pin") {
    return <svg {...common}><path d="M20 10c0 5.4-8 11-8 11S4 15.4 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.6"/></svg>;
  }
  if (type === "search") {
    return <svg {...common}><circle cx="10.5" cy="10.5" r="5.5"/><path d="m15 15 4.5 4.5"/></svg>;
  }
  if (type === "reuse") {
    return <svg {...common}><path d="M20 8a8 8 0 0 0-13-3L5 7"/><path d="M5 3v4h4M4 16a8 8 0 0 0 13 3l2-2"/><path d="M19 21v-4h-4"/></svg>;
  }
  if (type === "pencil") {
    return <svg {...common}><path d="m4 20 4.2-1 10.3-10.3-3.2-3.2L5 15.8z"/><path d="m13.8 7 3.2 3.2"/></svg>;
  }
  return null;
}

export default function PrepareWorkflow({ config }) {
  const regions = config?.regions || [
    "천안", "아산", "공주", "보령", "서산", "논산", "계룡", "당진",
    "금산", "부여", "서천", "청양", "홍성", "예산", "태안",
  ];
  const [files, setFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const dragCounter = useRef(0);
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

  const amountSliderIndex = useMemo(() => {
    let best = 0;
    let distance = Infinity;
    AMOUNT_PRESETS.forEach((preset, index) => {
      const current = Math.abs(preset.value - targetAmount);
      if (current < distance) {
        distance = current;
        best = index;
      }
    });
    return best;
  }, [targetAmount]);

  function clearDerivedState() {
    setResult(null);
    setAddressResult(null);
    setManualAddresses({});
    setSaveStatus({});
    setReviewInfo(null);
  }

  function changeTargetAmount(value) {
    setTargetAmount(Math.max(0, Number(value) || 0));
    clearDerivedState();
  }

  function applyFiles(fileList) {
    const incoming = Array.from(fileList || []);
    const valid = incoming.filter(isExcelFile);
    if (incoming.length && valid.length !== incoming.length) {
      setError("Excel 파일(.xlsx, .xls)만 업로드할 수 있습니다.");
    } else {
      setError("");
    }
    setFiles(valid);
    clearDerivedState();
  }

  function handleDragEnter(event) {
    event.preventDefault();
    event.stopPropagation();
    dragCounter.current += 1;
    setDragActive(true);
  }

  function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    dragCounter.current -= 1;
    if (dragCounter.current <= 0) {
      dragCounter.current = 0;
      setDragActive(false);
    }
  }

  function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = "copy";
  }

  function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    dragCounter.current = 0;
    setDragActive(false);
    applyFiles(event.dataTransfer.files);
  }

  async function inspectFiles() {
    if (!files.length) {
      setError("자료관리목록 엑셀 파일을 선택해 주세요.");
      return;
    }

    setBusy(true);
    setError("");
    clearDerivedState();

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
      <section className="grid two streamlit-top-grid">
        <article className="card top-card upload-card-rich">
          <div className="panel-heading">
            <div className="panel-heading-icon blue"><Icon type="document" /></div>
            <div>
              <h2>자료 입력</h2>
              <p>계약자료 엑셀 파일을 업로드하세요. 여러 파일을 한 번에 선택할 수 있습니다.</p>
            </div>
          </div>

          <label
            className={dragActive ? "dropzone rich-dropzone dragging" : "dropzone rich-dropzone"}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept=".xlsx,.xls"
              multiple
              onChange={(event) => {
                applyFiles(event.target.files);
                event.target.value = "";
              }}
            />
            <div className="upload-cloud"><Icon type="upload" size={64} /></div>
            <strong>{files.length ? `Excel 파일 ${files.length}개 선택됨` : "여기에 파일을 드래그하거나 클릭하여 업로드하세요"}</strong>
            <span>{files.length ? "클릭하거나 다른 파일을 끌어 놓으면 선택 파일을 교체합니다." : "Excel 파일(.xlsx, .xls)을 여러 개 선택할 수 있습니다."}</span>
            <span className="fake-file-button">파일 선택하기</span>
          </label>

          <div className="upload-checks-react">
            <span>✓ 파일을 드래그해서 놓아도 업로드할 수 있습니다.</span>
            <span>✓ 선택한 파일은 현재 작업 중에만 임시 사용됩니다.</span>
          </div>
          <div className="file-summary">
            <span>선택 파일 <b>{files.length}개</b></span>
            <span>총 용량 <b>{(totalSize / 1024 / 1024).toFixed(1)} MB</b></span>
          </div>
        </article>

        <article className="card top-card conditions-card">
          <div className="panel-heading compact">
            <div className="panel-heading-icon navy"><Icon type="filter" /></div>
            <div>
              <h2>검색 조건</h2>
              <p>지역과 집계 기준 금액을 선택합니다.</p>
            </div>
          </div>

          <div className="condition-section">
            <label className="condition-label">기준 지역</label>
            <div className="segmented region-segmented">
              <button className={regionMode === "auto" ? "selected" : ""} onClick={() => { setRegionMode("auto"); clearDerivedState(); }}>자동 선택</button>
              <button className={regionMode === "manual" ? "selected" : ""} onClick={() => { setRegionMode("manual"); clearDerivedState(); }}>직접 선택</button>
            </div>
            <select value={manualRegion} disabled={regionMode === "auto"} onChange={(event) => { setManualRegion(event.target.value); clearDerivedState(); }}>
              {regions.map((region) => <option value={region} key={region}>{region}</option>)}
            </select>
            {regionMode === "auto" && <div className="auto-region-note">파일 업로드 후 주소를 기준으로 자동 선택합니다.</div>}
          </div>

          <div className="condition-section amount-section">
            <div className="condition-label-row">
              <label className="condition-label">집계 기준 금액 <span>(원 이상)</span></label>
              <b>{formatNumber(targetAmount)}원</b>
            </div>

            <div className="amount-presets">
              {AMOUNT_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  className={targetAmount === preset.value ? "active" : ""}
                  onClick={() => changeTargetAmount(preset.value)}
                >
                  {preset.label}
                </button>
              ))}
            </div>

            <div className="amount-slider-wrap">
              <input
                className="amount-slider"
                type="range"
                min="0"
                max={AMOUNT_PRESETS.length - 1}
                step="1"
                value={amountSliderIndex}
                onChange={(event) => changeTargetAmount(AMOUNT_PRESETS[Number(event.target.value)].value)}
              />
              <div className="slider-labels">
                {AMOUNT_PRESETS.map((preset) => <span key={preset.value}>{preset.label}</span>)}
              </div>
            </div>

            <div className="direct-amount">
              <span>직접 금액 입력</span>
              <div className="money-input compact-money">
                <input type="number" min="0" step="10000" value={targetAmount} onChange={(event) => changeTargetAmount(event.target.value)} />
                <span>원</span>
              </div>
            </div>
          </div>
        </article>
      </section>

      <section className={files.length ? "action-row analysis-action ready" : "action-row analysis-action waiting"}>
        <div>
          <strong>{files.length ? "자료 분석 준비 완료" : "자료 업로드 대기"}</strong>
          <span>{files.length ? `선택 파일 ${files.length}개 · ${formatNumber(targetAmount)}원 이상 계약을 분석합니다.` : "파일을 선택하면 보고 대상과 주소 보완 대상을 확인합니다."}</span>
        </div>
        <button className="primary" disabled={busy || !files.length} onClick={inspectFiles}>{busy ? "분석 중..." : "파일 분석 시작"}</button>
      </section>

      {error && <div className="alert error">{error}</div>}

      {result && (
        <section className="results visual-results">
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

          <div className="workflow-section-head">
            <div className="workflow-pin"><Icon type="pin" size={32} /></div>
            <div><h3>주소 보완</h3><p>저장된 주소와 공공 API를 활용해 자동으로 채운 뒤, 남은 업체만 직접 입력합니다.</p></div>
          </div>

          <div className="address-workflow-grid">
            <article className="workflow-card blue-card">
              <div className="workflow-card-title"><span className="step-number">1</span><h3>자동 주소 조회</h3></div>
              <p>저장주소를 먼저 확인하고 나라장터 → 학교장터 → 공정위 → 지역화폐 순으로 조회합니다.</p>
              <button className="workflow-action blue-action" disabled={addressBusy || !!addressResult} onClick={lookupAddresses}>
                <Icon type="search" size={20} />
                {addressBusy ? "주소 조회 중..." : addressResult ? "주소 조회 완료" : `주소 조회 시작 · ${formatNumber(result.api_lookup_candidate_count)}개 업체`}
              </button>
              <div className="workflow-stat">조회 대상 <b>{formatNumber(result.api_lookup_candidate_count)}개 업체</b></div>
            </article>

            <article className="workflow-card green-card">
              <div className="workflow-card-title"><span className="step-number">2</span><h3>저장주소 재사용</h3></div>
              <p>이전에 확인한 업체 주소와 Firestore 캐시를 자동으로 불러와 반복 조회를 줄입니다.</p>
              <div className="workflow-action green-action static"><Icon type="reuse" size={20} />자동 재사용</div>
              <div className="workflow-stat">{addressResult ? <>이번 실행 재사용 <b>{formatNumber((addressResult.cache_hit_count || 0) + (addressResult.manual_hit_count || 0))}개</b></> : <>조회 후 재사용 건수를 표시합니다.</>}</div>
            </article>

            <article className="workflow-card orange-card">
              <div className="workflow-card-title"><span className="step-number">3</span><h3>남은 주소 직접 입력</h3></div>
              <p>자동 조회로 찾지 못한 업체만 직접 확인하고 주소를 저장해 다음 작업에 재사용합니다.</p>
              <div className="workflow-action orange-action static"><Icon type="pencil" size={20} />{addressResult ? `주소 미확인 ${formatNumber(unresolvedCandidates.length)}개` : "자동 조회 후 활성화"}</div>
              <div className="workflow-stat">{addressResult ? <>직접 입력 필요 <b>{formatNumber(unresolvedCandidates.length)}개 업체</b></> : <>먼저 자동 주소 조회를 실행하세요.</>}</div>
            </article>
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

import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

const AMOUNT_PRESETS = [
  { value: 0, label: "0원" },
  { value: 100000, label: "10만원" },
  { value: 500000, label: "50만원" },
  { value: 1000000, label: "100만원" },
  { value: 10000000, label: "1,000만원" },
];

const EMPTY_PROGRESS = {
  completed: 0,
  total: 0,
  percent: 0,
  currentBiz: "",
  currentSource: "",
  found: 0,
};

function formatNumber(value) {
  return new Intl.NumberFormat("ko-KR").format(Number(value || 0));
}

function downloadNameFromHeader(headerValue, fallback) {
  if (!headerValue) return fallback;
  const match = headerValue.match(/filename\*=UTF-8''([^;]+)/i);
  if (!match) return fallback;
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return fallback;
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
  if (type === "pencil") {
    return <svg {...common}><path d="m4 20 4.2-1 10.3-10.3-3.2-3.2L5 15.8z"/><path d="m13.8 7 3.2 3.2"/></svg>;
  }
  if (type === "download") {
    return <svg {...common}><path d="M12 3v12m-5-5 5 5 5-5"/><path d="M5 20h14"/></svg>;
  }
  if (type === "check") {
    return <svg {...common}><path d="m5 12 4 4L19 6"/></svg>;
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
  const [addressProgress, setAddressProgress] = useState(EMPTY_PROGRESS);
  const [manualAddresses, setManualAddresses] = useState({});
  const [saveStatus, setSaveStatus] = useState({});
  const [busy, setBusy] = useState(false);
  const [addressBusy, setAddressBusy] = useState(false);
  const [quarterBusy, setQuarterBusy] = useState(false);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewInfo, setReviewInfo] = useState(null);
  const [error, setError] = useState("");
  const [sideTarget, setSideTarget] = useState(null);

  useEffect(() => {
    setSideTarget(document.getElementById("side-workflow-slot"));
  }, []);

  const totalSize = useMemo(
    () => files.reduce((sum, file) => sum + file.size, 0),
    [files]
  );

  const candidateByBiz = useMemo(() => {
    const map = {};
    for (const item of result?.lookup_candidates || []) {
      if (item.biz_no) map[item.biz_no] = item;
    }
    return map;
  }, [result]);

  const foundByBiz = useMemo(() => {
    const map = {};
    for (const item of addressResult?.results || []) {
      if (item.found && item.biz_no && item.address) map[item.biz_no] = item.address;
    }
    return map;
  }, [addressResult]);

  const savedSuggestionByBiz = useMemo(() => {
    const map = {};
    for (const item of addressResult?.results || []) {
      if (item.manual_suggestion && item.biz_no && item.saved_address) {
        map[item.biz_no] = {
          address: item.saved_address,
          company: item.saved_company_name || "",
        };
      }
    }
    return map;
  }, [addressResult]);

  const unresolvedCandidates = useMemo(() => {
    return (result?.manual_candidates || [])
      .filter((candidate) => {
        if (!candidate.biz_no) return true;
        return !foundByBiz[candidate.biz_no];
      })
      .map((candidate) => ({
        ...candidate,
        saved_address: candidate.biz_no ? (savedSuggestionByBiz[candidate.biz_no]?.address || "") : "",
        saved_company_name: candidate.biz_no ? (savedSuggestionByBiz[candidate.biz_no]?.company || "") : "",
      }));
  }, [result, foundByBiz, savedSuggestionByBiz]);

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

  const progressCandidate = addressProgress.currentBiz
    ? candidateByBiz[addressProgress.currentBiz]
    : null;
  const progressCompany = progressCandidate?.company || addressProgress.currentBiz || "";

  function clearDerivedState() {
    setResult(null);
    setAddressResult(null);
    setAddressProgress(EMPTY_PROGRESS);
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

  function currentAddressOverrides() {
    const business = { ...foundByBiz };
    const rows = {};
    for (const candidate of unresolvedCandidates) {
      const address = String(manualAddresses[candidate.lookup_key] || "").trim();
      if (!address) continue;
      if (candidate.biz_no) business[candidate.biz_no] = address;
      else rows[String(candidate.row_id)] = address;
    }
    return { business, rows };
  }

  function appendCommonReportFields(form) {
    files.forEach((file) => form.append("files", file));
    form.append("target_amount", String(targetAmount));
    form.append("region_mode", regionMode);
    form.append("manual_region", manualRegion);
    form.append("address_overrides_json", JSON.stringify(currentAddressOverrides()));
  }

  async function saveResponseFile(response, fallbackName) {
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = downloadNameFromHeader(response.headers.get("Content-Disposition"), fallbackName);
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
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
      setAddressProgress({ ...EMPTY_PROGRESS, percent: 100 });
      setAddressResult({
        found_count: 0,
        cache_hit_count: 0,
        negative_cache_hit_count: 0,
        manual_hit_count: 0,
        manual_suggestion_count: 0,
        source_counts: {},
        elapsed_ms: 0,
        results: [],
      });
      return;
    }

    setAddressBusy(true);
    setAddressResult(null);
    setAddressProgress({
      ...EMPTY_PROGRESS,
      total: candidates.length,
    });
    setError("");
    setReviewInfo(null);

    try {
      const response = await fetch("/api/address/bulk-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          biz_numbers: candidates.map((item) => item.biz_no),
          force_refresh: false,
        }),
      });
      if (!response.ok) {
        let detail = "주소 조회에 실패했습니다.";
        try {
          const data = await response.json();
          detail = data.detail || detail;
        } catch {}
        throw new Error(detail);
      }
      if (!response.body) throw new Error("주소 조회 진행정보를 받을 수 없습니다.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalResult = null;

      const handleEvent = (event) => {
        if (event.type === "start") {
          setAddressProgress((current) => ({
            ...current,
            total: Number(event.total || candidates.length),
          }));
        } else if (event.type === "source") {
          setAddressProgress((current) => ({
            ...current,
            currentBiz: event.biz_no || "",
            currentSource: event.source || "",
          }));
        } else if (event.type === "complete") {
          const completed = Number(event.completed || 0);
          const total = Number(event.total || candidates.length);
          setAddressProgress((current) => ({
            ...current,
            completed,
            total,
            percent: total ? Math.round((completed / total) * 100) : 100,
            currentBiz: event.biz_no || current.currentBiz,
            currentSource: event.cache_hit ? "공공 API 캐시" : (event.source || current.currentSource),
            found: current.found + (event.found ? 1 : 0),
          }));
        } else if (event.type === "result") {
          finalResult = event.data;
          setAddressResult(event.data);
          setAddressProgress((current) => ({
            ...current,
            completed: current.total || candidates.length,
            total: current.total || candidates.length,
            percent: 100,
            currentSource: "조회 완료",
          }));
        } else if (event.type === "error") {
          throw new Error(event.detail || "주소 조회에 실패했습니다.");
        }
      };

      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.trim()) continue;
          handleEvent(JSON.parse(line));
        }
        if (done) break;
      }
      if (buffer.trim()) handleEvent(JSON.parse(buffer));
      if (!finalResult) throw new Error("주소 조회 결과를 받지 못했습니다.");
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

  async function createQuarterReport() {
    if (!files.length || !result) return;
    const form = new FormData();
    appendCommonReportFields(form);

    setQuarterBusy(true);
    setError("");
    try {
      const response = await fetch("/api/prepare/quarter", { method: "POST", body: form });
      if (!response.ok) {
        let detail = "분기보고서 생성에 실패했습니다.";
        try {
          const data = await response.json();
          detail = data.detail || detail;
        } catch {}
        throw new Error(detail);
      }
      await saveResponseFile(response, `지역경제활성화_실적보고(${result.target_region}기준).xlsx`);
    } catch (err) {
      setError(err.message || "분기보고서 생성 중 오류가 발생했습니다.");
    } finally {
      setQuarterBusy(false);
    }
  }

  async function createReviewWorkbook() {
    if (!files.length || !result) return;

    const report = config?.default_report || {
      year: 2026,
      label: "상반기",
      start_date: "2026-01-01",
      end_date: "2026-07-31",
    };

    const form = new FormData();
    appendCommonReportFields(form);
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

      await saveResponseFile(response, "지역경제활성화_검토용.xlsx");
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

  const resultFiles = (
    <section className="output-panel unified-output">
      <div className="result-head">
        <div>
          <p className="result-kicker">OUTPUT</p>
          <h3>결과 파일</h3>
        </div>
        <span className="result-state done">생성 가능</span>
      </div>
      <div className="hint result-guide">
        주소 보완은 선택사항입니다. 지금 바로 생성하거나, 주소를 조회·보완한 뒤 다시 생성할 수 있습니다.
      </div>

      <div className="output-action-stack">
        <div className="output-action-copy">
          <strong>분기별 실적보고서</strong>
          <span>미확인 주소는 타시도로 임시 분류하여 바로 집계합니다.</span>
        </div>
        <button className="primary final-output-action" disabled={quarterBusy} onClick={createQuarterReport}>
          <Icon type="download" size={19} />
          {quarterBusy ? "분기보고서 생성 중..." : "분기보고서 다운로드"}
        </button>

        <div className="output-divider" />

        <div className="output-action-copy">
          <strong>반기 검토용 기초자료</strong>
          <span>현재까지 확인된 주소를 반영해 공식 1-4 기초자료를 생성합니다.</span>
        </div>
        <button className="review-output-action" disabled={reviewBusy} onClick={createReviewWorkbook}>
          <Icon type="download" size={19} />
          {reviewBusy ? "검토용 Excel 생성 중..." : "검토용 Excel 다운로드"}
        </button>
      </div>

      {reviewInfo && (
        <div className={reviewInfo.unresolvedCount ? "alert warn compact-output-alert" : "alert success compact-output-alert"}>
          대상 {formatNumber(reviewInfo.recordCount)}건 · 주소 반영 {formatNumber(reviewInfo.filledCount)}건 · 미확인 {formatNumber(reviewInfo.unresolvedCount)}건
        </div>
      )}
    </section>
  );

  const sidePanel = (
    <section className="side-card side-upload-card">
      <div className="side-title">자료관리목록 불러오기</div>
      <label
        className={dragActive ? "side-dropzone dragging" : "side-dropzone"}
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
        <strong>{files.length ? `Excel ${files.length}개 선택됨` : "Excel을 여기에 놓거나 클릭"}</strong>
        <span>{files.length ? `${(totalSize / 1024 / 1024).toFixed(1)} MB · 다시 선택하면 교체` : "여러 파일 선택 가능"}</span>
      </label>
      <button
        className="primary side-analysis-button"
        disabled={busy || !files.length}
        onClick={inspectFiles}
      >
        {busy ? "자료 분석 중..." : "자료 분석"}
      </button>
      <div className="side-upload-note">선택한 파일은 현재 작업 중에만 임시 사용됩니다.</div>
    </section>
  );

  return (
    <>
      {sideTarget && createPortal(sidePanel, sideTarget)}

      <section className="pre-analysis-grid">
        <article className="card conditions-card compact-conditions-card">
          <div className="panel-heading compact">
            <div className="panel-heading-icon navy"><Icon type="filter" /></div>
            <div>
              <h2>집계 조건</h2>
              <p>분석에 사용할 지역과 금액 기준만 선택합니다.</p>
            </div>
          </div>

          <div className="condition-compact-grid">
            <div className="compact-condition-block">
              <div className="condition-label-row compact-label-row">
                <label className="condition-label">기준 지역</label>
                <b>{regionMode === "auto" ? "자동" : manualRegion}</b>
              </div>
              <div className="segmented region-segmented compact-segmented">
                <button className={regionMode === "auto" ? "selected" : ""} onClick={() => { setRegionMode("auto"); clearDerivedState(); }}>자동선택</button>
                <button className={regionMode === "manual" ? "selected" : ""} onClick={() => { setRegionMode("manual"); clearDerivedState(); }}>직접선택</button>
              </div>
              {regionMode === "manual" && (
                <select className="compact-region-select" value={manualRegion} onChange={(event) => { setManualRegion(event.target.value); clearDerivedState(); }}>
                  {regions.map((region) => <option value={region} key={region}>{region}</option>)}
                </select>
              )}
            </div>

            <div className="compact-condition-block">
              <div className="condition-label-row compact-label-row">
                <label className="condition-label">집계 기준 금액 <span>(원 이상)</span></label>
                <b>{formatNumber(targetAmount)}원</b>
              </div>

              <div className="amount-presets compact-presets">
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

              <div className="direct-amount compact-direct-amount">
                <span>직접입력</span>
                <div className="money-input compact-money">
                  <input type="number" min="0" step="10000" value={targetAmount} onChange={(event) => changeTargetAmount(event.target.value)} />
                  <span>원</span>
                </div>
              </div>
            </div>
          </div>
        </article>

        <aside className="card work-status-card">
          <div className="work-status-head">
            <span className="step">STATUS</span>
            <h2>작업 상황</h2>
          </div>
          <div className="work-status-list">
            <div>
              <span>자료</span>
              <strong>{files.length ? `${files.length}개 파일` : "대기"}</strong>
            </div>
            <div>
              <span>분석</span>
              <strong className={result ? "status-value done" : files.length ? "status-value ready" : "status-value"}>
                {result ? "완료" : files.length ? "실행 가능" : "대기"}
              </strong>
            </div>
            {result ? (
              <>
                <div>
                  <span>보고 대상</span>
                  <strong>{formatNumber(result.report_count)}건</strong>
                </div>
                <div>
                  <span>주소 미확인</span>
                  <strong>{formatNumber(result.missing_address_count)}건</strong>
                </div>
              </>
            ) : (
              <div className="work-status-note">
                왼쪽에서 파일을 올린 뒤 <b>자료 분석</b>을 실행하세요.
              </div>
            )}
          </div>
        </aside>
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
            {result.processing_ms ? <> · 분석 <b>{(Number(result.processing_ms) / 1000).toFixed(1)}초</b></> : null}
          </div>

          <div className="post-analysis-layout">
            <div className="address-workspace">
              <div className="workflow-section-head compact-workflow-head">
                <div className="workflow-pin"><Icon type="pin" size={30} /></div>
                <div>
                  <h3>주소 보완 <span className="optional-label">선택사항</span></h3>
                  <p>공공 API 캐시를 먼저 쓰고, 미확인 업체만 나라장터 → 학교장터 → 공정위 → 지역화폐 순으로 조회합니다.</p>
                </div>
              </div>

              <article className="address-lookup-card">
                <div className="address-lookup-head">
                  <div>
                    <span className="step-number">2</span>
                    <div>
                      <h3>자동 주소 조회</h3>
                      <p>사용자 저장주소는 자동 확정하지 않고 API가 모두 실패했을 때 후보로만 보여줍니다.</p>
                    </div>
                  </div>
                  <span className="lookup-target-badge">대상 {formatNumber(result.api_lookup_candidate_count)}개</span>
                </div>

                <button className="primary lookup-main-button" disabled={addressBusy || !!addressResult} onClick={lookupAddresses}>
                  <Icon type="search" size={20} />
                  {addressBusy ? "공공 API 주소 조회 중..." : addressResult ? "주소 조회 완료" : "자동 주소 조회 시작"}
                </button>

                {addressBusy && (
                  <div className="lookup-progress-panel" aria-live="polite">
                    <div className="lookup-progress-head">
                      <div>
                        <strong>{addressProgress.percent}%</strong>
                        <span>주소 조회 진행률</span>
                      </div>
                      <b>{formatNumber(addressProgress.completed)} / {formatNumber(addressProgress.total)} 업체</b>
                    </div>
                    <div className="lookup-progress-track">
                      <span style={{ width: `${Math.max(0, Math.min(100, addressProgress.percent))}%` }} />
                    </div>
                    <div className="lookup-progress-current">
                      <span className="live-dot" />
                      {addressProgress.currentSource
                        ? <><b>{progressCompany || "업체 확인 중"}</b> · {addressProgress.currentSource}</>
                        : <>Firestore 공공 API 캐시를 확인하고 있습니다.</>}
                    </div>
                    <div className="lookup-progress-sub">
                      API 주소 확인 {formatNumber(addressProgress.found)}개 · 최대 {config?.max_bulk_businesses || 200}개 업체까지 조회
                    </div>
                  </div>
                )}

                {!addressBusy && !addressResult && (
                  <div className="address-trust-note">
                    <span><b>1</b> 공공 API 캐시</span>
                    <span><b>2</b> 공공 API 실시간 조회</span>
                    <span><b>3</b> 사용자 저장주소 확인</span>
                  </div>
                )}
              </article>

              {addressResult && (
                <>
                  <div className="address-result">
                    <div className="address-summary">
                      <div><span>API 주소 확인</span><strong>{formatNumber(addressResult.found_count)}개</strong></div>
                      <div><span>미확인</span><strong>{formatNumber(unresolvedCandidates.length)}개</strong></div>
                      <div><span>API 캐시 재사용</span><strong>{formatNumber(addressResult.cache_hit_count)}개</strong></div>
                      <div><span>사용자 저장주소 후보</span><strong>{formatNumber(addressResult.manual_suggestion_count)}개</strong></div>
                    </div>
                    <div className="source-line">
                      나라장터 <b>{formatNumber(addressResult.source_counts?.["나라장터"])}</b><span>·</span>
                      학교장터 <b>{formatNumber(addressResult.source_counts?.["학교장터(S2B)"])}</b><span>·</span>
                      공정위 <b>{formatNumber(addressResult.source_counts?.["공정위 통신판매사업자"])}</b><span>·</span>
                      지역화폐 <b>{formatNumber(addressResult.source_counts?.["지역화폐 가맹점"])}</b>
                      {addressResult.elapsed_ms ? <><span>·</span> 조회시간 <b>{(Number(addressResult.elapsed_ms) / 1000).toFixed(1)}초</b></> : null}
                    </div>
                  </div>

                  {unresolvedCandidates.length > 0 && (
                    <div className="manual-panel">
                      <div className="manual-head">
                        <div>
                          <span className="step">OPTION</span>
                          <h3>주소 미확인 업체 직접 보완</h3>
                          <p>이전 사용자 저장주소는 자동 적용되지 않습니다. 내용을 확인한 뒤 적용하거나 새 주소를 입력하세요.</p>
                        </div>
                        <span className="manual-progress">입력 {enteredManualCount}/{unresolvedCandidates.length}</span>
                      </div>
                      <div className="manual-list">
                        {unresolvedCandidates.map((candidate) => {
                          const status = saveStatus[candidate.lookup_key];
                          const value = manualAddresses[candidate.lookup_key] || "";
                          return (
                            <div className="manual-row" key={candidate.lookup_key}>
                              <div className="company-cell"><strong>{candidate.company || "업체명 확인불가"}</strong><span>{candidate.biz_no || "사업자번호 확인불가"}</span></div>
                              <div className="address-entry-cell">
                                {candidate.saved_address && (
                                  <div className="saved-address-suggestion">
                                    <div><span>이전 사용자 저장주소</span><strong>{candidate.saved_address}</strong></div>
                                    <button type="button" onClick={() => { setManualAddresses((current) => ({ ...current, [candidate.lookup_key]: candidate.saved_address })); setReviewInfo(null); }}>확인 후 적용</button>
                                  </div>
                                )}
                                <input className="address-input" value={value} placeholder={candidate.saved_address ? "저장주소를 확인하거나 새 주소를 입력하세요" : "확인한 업체 주소를 입력하세요"} onChange={(event) => { setManualAddresses((current) => ({ ...current, [candidate.lookup_key]: event.target.value })); setReviewInfo(null); }} />
                              </div>
                              <div className="manual-buttons">
                                {candidate.biz_no && <a className="secondary-link" href={`https://bizno.net/?query=${encodeURIComponent(candidate.biz_no)}`} target="_blank" rel="noreferrer">업체조회</a>}
                                <button className="secondary" disabled={!candidate.biz_no || !String(value).trim() || status === "saving"} onClick={() => saveManual(candidate)}>
                                  {status === "saving" ? "저장 중" : status === "shared" ? "Firestore 저장됨" : status === "local" ? "로컬 저장됨" : status === "error" ? "저장 재시도" : "주소 기억"}
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            <aside className="result-output-column">
              {resultFiles}
            </aside>
          </div>
        </section>
      )}
    </>
  );
}

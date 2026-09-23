import { useRef, useState } from "react";

function downloadNameFromHeader(headerValue) {
  if (!headerValue) return "지역경제활성화_최종보고서.xlsx";
  const match = headerValue.match(/filename\*=UTF-8''([^;]+)/i);
  if (!match) return "지역경제활성화_최종보고서.xlsx";
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return "지역경제활성화_최종보고서.xlsx";
  }
}

function formatNumber(value) {
  return new Intl.NumberFormat("ko-KR").format(Number(value || 0));
}

function isExcelFile(file) {
  return /\.(xlsx|xls)$/i.test(file?.name || "");
}

export default function FinalReport() {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const dragCounter = useRef(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState(null);

  function applyFile(nextFile) {
    if (nextFile && !isExcelFile(nextFile)) {
      setFile(null);
      setError("Excel 파일(.xlsx, .xls)만 업로드할 수 있습니다.");
      setInfo(null);
      return;
    }
    setFile(nextFile || null);
    setError("");
    setInfo(null);
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
    applyFile(event.dataTransfer.files?.[0] || null);
  }

  async function createFinalReport() {
    if (!file) {
      setError("검토가 끝난 1-4 기초자료 Excel 파일을 선택해 주세요.");
      return;
    }

    setBusy(true);
    setError("");
    setInfo(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const response = await fetch("/api/final/report", {
        method: "POST",
        body: form,
      });

      if (!response.ok) {
        let detail = "최종 반기보고서 생성에 실패했습니다.";
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
      setTimeout(() => URL.revokeObjectURL(url), 1000);

      setInfo({
        recordCount: Number(response.headers.get("X-Record-Count") || 0),
        correctedLocationCount: Number(response.headers.get("X-Corrected-Location-Count") || 0),
        purposeCorrectionCount: Number(response.headers.get("X-Purpose-Correction-Count") || 0),
      });
    } catch (err) {
      setError(err.message || "최종 보고서 생성 중 오류가 발생했습니다.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="final-workflow">
      <div className="workspace-status">
        검토가 끝난 1-4 기초자료 Excel을 선택하면 공식 4시트 보고서를 생성할 수 있습니다.
      </div>

      <div className="final-work-grid">
        <article className="card final-upload-card compact-final-card">
          <div className="compact-card-heading">
            <span className="step">STEP 01</span>
            <h2>1. 검토파일 선택</h2>
            <p>앞 단계에서 내려받아 확인·수정한 검토용 Excel을 사용합니다.</p>
          </div>

          <label
            className={dragActive ? "dropzone final-dropzone compact-dropzone dragging" : "dropzone final-dropzone compact-dropzone"}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(event) => {
                applyFile(event.target.files?.[0] || null);
                event.target.value = "";
              }}
            />
            <strong>{file ? file.name : "검토 완료 Excel을 여기에 놓거나 클릭"}</strong>
            <span>{file ? "클릭하거나 다른 파일을 놓으면 교체됩니다." : "1-4 기초자료가 포함된 검토용 파일"}</span>
          </label>

          <div className="final-file-note">
            {file
              ? <>선택 파일 <b>{file.name}</b><span>{(file.size / 1024 / 1024).toFixed(2)} MB</span></>
              : <>사용자가 수정한 주소·소재지·구입목적 값을 최종값으로 사용합니다.</>}
          </div>
        </article>

        <aside className="card final-result-card">
          <div className="result-head">
            <div>
              <p className="result-kicker">FINAL RESULT</p>
              <h2>최종 4시트 보고서</h2>
            </div>
            <span className={file ? "result-state done" : "result-state"}>
              {file ? "생성 가능" : "파일 대기"}
            </span>
          </div>

          <div className="hint result-guide">
            검토파일의 수정값을 반영하고, 필요한 항목만 보고 기준에 맞게 자동 보정합니다.
          </div>

          <div className="final-sheet-grid">
            <div><b>1-1</b><span>총괄 · 공사</span></div>
            <div><b>1-2</b><span>총괄 · 용역</span></div>
            <div><b>1-3</b><span>총괄 · 물품</span></div>
            <div><b>1-4</b><span>확정 기초자료</span></div>
          </div>

          <div className="final-compact-checks">
            <span>✓ 수정한 검토값을 최종값으로 사용</span>
            <span>✓ 잘못된 소재지는 주소 기준으로 보정</span>
            <span>✓ 물품 구입목적의 빈 값·비정상 값 보정</span>
          </div>

          <button className="primary final-download-button" disabled={busy || !file} onClick={createFinalReport}>
            {busy ? "최종 보고서 생성 중..." : "최종 보고서 다운로드"}
          </button>

          {info && (
            <div className="alert success compact-final-alert">
              생성 완료 · 기초자료 {formatNumber(info.recordCount)}건 · 소재지 보정 {formatNumber(info.correctedLocationCount)}건 · 구입목적 보정 {formatNumber(info.purposeCorrectionCount)}건
            </div>
          )}
        </aside>
      </div>

      {error && <div className="alert error">{error}</div>}
    </section>
  );
}

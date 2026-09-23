import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

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
  const [sideTarget, setSideTarget] = useState(null);

  useEffect(() => {
    setSideTarget(document.getElementById("side-workflow-slot"));
  }, []);

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

  const sidePanel = (
    <section className="side-card side-upload-card">
      <div className="side-title">검토파일 불러오기</div>
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
          onChange={(event) => {
            applyFile(event.target.files?.[0] || null);
            event.target.value = "";
          }}
        />
        <strong>{file ? file.name : "검토 Excel을 놓거나 클릭"}</strong>
        <span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · 다시 선택하면 교체` : "1-4 기초자료 포함 파일"}</span>
      </label>
      <button
        className="primary side-analysis-button"
        disabled={busy || !file}
        onClick={createFinalReport}
      >
        {busy ? "최종 보고서 생성 중..." : "최종 보고서 생성"}
      </button>
      <div className="side-upload-note">검토파일의 수정값을 최종값으로 사용합니다.</div>
    </section>
  );

  return (
    <>
      {sideTarget && createPortal(sidePanel, sideTarget)}

      <section className="final-workflow">
        <article className="card final-result-card final-overview-card">
          <div className="result-head">
            <div>
              <p className="result-kicker">FINAL REPORT</p>
              <h2>최종 4시트 보고서</h2>
            </div>
            <span className={file ? "result-state done" : "result-state"}>
              {file ? "생성 준비 완료" : "검토파일 대기"}
            </span>
          </div>

          <div className="hint result-guide">
            왼쪽에서 검토 완료 Excel을 선택하면 수정값을 반영해 공식 반기보고서 4개 시트를 생성합니다.
          </div>

          <div className="final-sheet-grid">
            <div><b>1-1</b><span>총괄 · 공사</span></div>
            <div><b>1-2</b><span>총괄 · 용역</span></div>
            <div><b>1-3</b><span>총괄 · 물품</span></div>
            <div><b>1-4</b><span>확정 기초자료</span></div>
          </div>

          <div className="final-compact-checks">
            <span>✓ 사용자가 수정한 주소·소재지·구입목적을 최종값으로 사용</span>
            <span>✓ 잘못된 소재지는 주소를 기준으로 자동 보정</span>
            <span>✓ 물품 구입목적의 빈 값·비정상 값은 보고 기준에 맞게 보정</span>
            <span>✓ 공식 반기보고서 서식의 4개 시트를 그대로 생성</span>
          </div>

          {info && (
            <div className="alert success compact-final-alert">
              생성 완료 · 기초자료 {formatNumber(info.recordCount)}건 · 소재지 보정 {formatNumber(info.correctedLocationCount)}건 · 구입목적 보정 {formatNumber(info.purposeCorrectionCount)}건
            </div>
          )}
        </article>

        {error && <div className="alert error">{error}</div>}
      </section>
    </>
  );
}

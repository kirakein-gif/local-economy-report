import { useState } from "react";

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

export default function FinalReport() {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState(null);

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
      URL.revokeObjectURL(url);

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
      <article className="card final-upload-card">
        <div className="card-head">
          <div>
            <span className="step">FINAL · STEP 01</span>
            <h2>검토 완료 파일 업로드</h2>
          </div>
          <div className="icon-box">✓</div>
        </div>

        <p className="final-guide">
          앞 단계에서 내려받은 <b>1-4 기초자료</b>를 확인·수정한 뒤 업로드하세요.
          사용자가 Excel에서 수정한 주소, 소재지, 구입목적 등의 값을 최종값으로 사용합니다.
        </p>

        <label className="dropzone final-dropzone">
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={(event) => {
              setFile(event.target.files?.[0] || null);
              setError("");
              setInfo(null);
            }}
          />
          <strong>{file ? file.name : "검토 완료 Excel 파일을 선택하거나 끌어 놓으세요"}</strong>
          <span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : "1-4 기초자료가 포함된 검토용 파일"}</span>
        </label>
      </article>

      <article className="final-process-card">
        <div className="final-process-head">
          <div>
            <span className="step">FINAL · STEP 02</span>
            <h2>최종 4시트 보고서 생성</h2>
          </div>
          <button className="primary" disabled={busy || !file} onClick={createFinalReport}>
            {busy ? "최종 보고서 생성 중..." : "최종 보고서 다운로드"}
          </button>
        </div>

        <div className="sheet-flow">
          <div><b>1-1</b><span>총괄 + 공사</span></div>
          <em>→</em>
          <div><b>1-2</b><span>총괄 + 용역</span></div>
          <em>→</em>
          <div><b>1-3</b><span>총괄 + 물품</span></div>
          <em>→</em>
          <div><b>1-4</b><span>확정 기초자료</span></div>
        </div>

        <div className="final-checks">
          <span>✓ 사용자가 수정한 검토파일 값을 최종값으로 사용</span>
          <span>✓ 소재지 값이 잘못된 경우 주소를 기준으로 자동 보정</span>
          <span>✓ 물품 구입목적의 빈 값·비정상 값은 보고 기준에 맞게 보정</span>
          <span>✓ 공식 반기보고서 서식의 4개 시트를 그대로 생성</span>
        </div>
      </article>

      {error && <div className="alert error">{error}</div>}

      {info && (
        <div className="alert success">
          최종 보고서 생성 완료 · 기초자료 {formatNumber(info.recordCount)}건 · 소재지 자동 보정 {formatNumber(info.correctedLocationCount)}건 · 구입목적 보정 {formatNumber(info.purposeCorrectionCount)}건
        </div>
      )}
    </section>
  );
}

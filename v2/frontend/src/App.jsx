import { useEffect, useState } from "react";
import FinalReport from "./FinalReport";
import PrepareWorkflow from "./PrepareWorkflow";

const PROGRAM_ICON = "/local-economy-report-icon.png";

export default function App() {
  const [mode, setMode] = useState("prepare");
  const [config, setConfig] = useState(null);

  useEffect(() => {
    fetch("/api/config")
      .then((response) => response.json())
      .then((data) => setConfig(data))
      .catch(() => {});
  }, []);

  const isPrepare = mode === "prepare";
  const version = config?.version || "2.0";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <section className="side-card stage-card">
          <div className="side-title">업무 메뉴</div>
          <button
            className={isPrepare ? "side-step active" : "side-step"}
            onClick={() => setMode("prepare")}
          >
            <span>1</span>
            <div>
              <b>자료 집계 · 검토파일</b>
              <small>분기보고서 · 반기 기초자료</small>
            </div>
          </button>
          <button
            className={!isPrepare ? "side-step active" : "side-step"}
            onClick={() => setMode("final")}
          >
            <span>2</span>
            <div>
              <b>반기보고서 최종작성</b>
              <small>검토파일 → 공식 4시트</small>
            </div>
          </button>
        </section>

        <div className="sidebar-spacer" />

        <div className="sidebar-meta">
          <strong>v{version}</strong>
          <span>제작자: 천안버들유치원 나대현</span>
        </div>
      </aside>

      <main className="main">
        <section className="hero">
          <div className="hero-brand-row">
            <img className="hero-program-icon" src={PROGRAM_ICON} alt="" aria-hidden="true" />
            <div className="hero-copy">
              <div className="eyebrow">LOCAL ECONOMY REPORT</div>
              <h1>
                {isPrepare
                  ? "지역경제활성화 실적 자동 집계"
                  : "반기보고서 최종작성"}
              </h1>
              <p>
                {isPrepare
                  ? "계약자료를 분석해 분기보고서와 반기 검토자료를 빠르게 작성합니다."
                  : "검토가 끝난 기초자료로 공식 1-1~1-4 보고서를 생성합니다."}
              </p>
            </div>
          </div>
        </section>

        {isPrepare ? <PrepareWorkflow config={config} /> : <FinalReport />}
      </main>
    </div>
  );
}

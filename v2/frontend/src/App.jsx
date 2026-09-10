import { useEffect, useState } from "react";
import FinalReport from "./FinalReport";
import PrepareWorkflow from "./PrepareWorkflow";

export default function App() {
  const [mode, setMode] = useState("prepare");
  const [config, setConfig] = useState(null);

  useEffect(() => {
    fetch("/api/config")
      .then((response) => response.json())
      .then((data) => setConfig(data))
      .catch(() => {});
  }, []);

  const cacheName = config?.address_cache?.active === "firestore"
    ? "Firestore 공유 캐시"
    : "메모리 캐시";
  const manualStoreName = config?.manual_address_backend === "firestore"
    ? "수동주소 공유 저장"
    : "수동주소 로컬 저장";

  const isPrepare = mode === "prepare";

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
          className={isPrepare ? "nav-button active" : "nav-button"}
          onClick={() => setMode("prepare")}
        >
          <span>01</span>
          자료 집계 · 검토파일
        </button>
        <button
          className={!isPrepare ? "nav-button active" : "nav-button"}
          onClick={() => setMode("final")}
        >
          <span>02</span>
          반기보고서 최종작성
        </button>

        <div className="sidebar-spacer" />
        <div className="side-note">
          <b>v2 Cloud Run 전환판</b>
          <span>{cacheName}</span>
          <span>{manualStoreName}</span>
          <span>기존 Streamlit 운영판과 분리 개발 중</span>
        </div>
      </aside>

      <main className="main">
        <section className="hero">
          <div>
            <div className="eyebrow">CHUNGNAM · LOCAL ECONOMY</div>
            <h1>
              {isPrepare
                ? "지역경제 활성화 계약자료 주소 정리"
                : "반기보고서 최종작성"}
            </h1>
            <p>
              {isPrepare
                ? "계약자료를 업로드하고 주소를 보완한 뒤 검토용 기초자료를 생성합니다."
                : "검토가 끝난 기초자료를 업로드해 공식 1-1~1-4 최종 보고서를 생성합니다."}
            </p>
          </div>
          <div className="hero-status">
            <span className="status-dot" />
            Cloud Run 자동확장 구조
          </div>
        </section>

        {isPrepare ? <PrepareWorkflow config={config} /> : <FinalReport />}
      </main>
    </div>
  );
}

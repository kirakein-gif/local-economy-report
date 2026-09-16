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
            <span>실적 자동 집계</span>
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
        <div className="developer-note">
          <b>천안버들유치원 · 나대현</b>
          <span>지역경제활성화 실적 자동 집계</span>
        </div>
        <div className="side-note">
          <b>Cloud Run 운영 상태</b>
          <span>{cacheName}</span>
          <span>{manualStoreName}</span>
        </div>
      </aside>

      <main className="main">
        <section className="hero">
          <div>
            <div className="eyebrow">CHUNGNAM · LOCAL ECONOMY</div>
            <h1>
              {isPrepare
                ? "지역경제활성화 실적 자동 집계"
                : "반기보고서 최종작성"}
            </h1>
            <p>
              {isPrepare
                ? "계약자료를 업로드하면 주소를 자동 조회·보완하고 검토용 기초자료까지 생성합니다."
                : "검토가 끝난 기초자료를 업로드해 공식 1-1~1-4 최종 보고서를 생성합니다."}
            </p>
          </div>
          <div className="hero-status">
            <span className="status-dot" />
            Cloud Run 자동확장
          </div>
        </section>

        {isPrepare ? <PrepareWorkflow config={config} /> : <FinalReport />}
      </main>
    </div>
  );
}

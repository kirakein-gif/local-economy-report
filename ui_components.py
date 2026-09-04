import streamlit as st


FILTER_CONTROLS_HTML = r"""
<div class="filter-shell">
  <div class="filter-head">
    <div class="filter-symbol"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M3 4h18l-7 8v8l-4-2v-6z"/></svg></div>
    <div class="filter-heading">검색 조건 <small>(선택)</small></div>
    <div class="filter-note">비워두면 전체 데이터를 대상으로 처리합니다.</div>
  </div>

  <div class="field-title">기준 지역 <span class="info-dot">i</span></div>
  <div class="region-options">
    <button type="button" id="region-auto" class="region-option">
      <span class="radio-mark"></span>
      <span><b>자동 선택</b><small>(가장 많은 주소 지역)</small></span>
    </button>
  <div id="auto-region-box" class="region-box">
    <span>현재 기준 지역</span>
    <b id="auto-region-value">-</b>
    <small id="auto-region-note"></small>
  </div>

    <button type="button" id="region-manual" class="region-option">
      <span class="radio-mark"></span>
      <span><b>직접 선택</b></span>
    </button>
  <div id="manual-region-box" class="manual-region-box">
    <select id="manual-region-select" aria-label="기준 지역 직접 선택"></select>
  </div>

  </div>
  <div class="divider"></div>

  <div class="field-title amount-title">집계 기준 금액 <span>(원 이상)</span> <span class="info-dot">i</span></div>
  <div class="amount-row">
    <button type="button" class="quick" data-value="0">0원</button>
    <button type="button" class="quick" data-value="100000">10만원</button>
    <button type="button" class="quick" data-value="500000">50만원</button>
    <button type="button" class="quick" data-value="1000000">100만원</button>
    <details class="direct-wrap"><summary>직접 금액 입력</summary>
      <label for="direct-amount">직접 입력</label>
      <div class="direct-input-line">
        <input id="direct-amount" type="number" min="0" step="10000" inputmode="numeric" />
        <span>원 이상</span>
      </div>
    </details>
  </div>

  <div class="slider-block">
    <div id="amount-bubble" class="amount-bubble">0원</div>
    <input aria-label="집계 기준 금액" id="amount-range" type="range" min="0" max="100" step="1" value="0" />
    <div class="scale-labels">
      <span style="left:0%">0원</span>
      <span style="left:18%">10만원</span>
      <span style="left:48%">50만원</span>
      <span style="left:68%">100만원</span>
      <span style="left:100%">1,000만원+</span>
    </div>
  </div>
</div>
"""

FILTER_CONTROLS_CSS = r"""
:host{font-family:'Pretendard','Noto Sans KR','Malgun Gothic',sans-serif;color:#10294d;line-height:1.35}
*{box-sizing:border-box}button,input,select{font:inherit}button{cursor:pointer}button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #89baff;outline-offset:3px}
.filter-shell{min-height:426px;background:#fff;border:1px solid #d9e4f0;border-radius:11px;box-shadow:0 3px 5px #10294d06}
.filter-head{display:flex;align-items:center;gap:9px;padding:9px 20px;border-bottom:1px solid #d9e4f0;border-radius:11px 11px 0 0;background:#f4f9ff}
.filter-symbol{font-size:25px;font-weight:900}.filter-heading{font-size:21px;font-weight:850;white-space:nowrap}.filter-heading small{font-size:18px}.filter-note{font-size:13px;color:#496789}
.field-title{font-size:18px;font-weight:800;margin:8px 22px 6px}.info-dot{display:inline-grid;place-items:center;width:17px;height:17px;border-radius:50%;background:#8093ac;color:#fff;font-size:11px;margin-left:5px}
.region-options{display:grid;grid-template-columns:1fr;padding:0 20px;gap:5px}
.region-option{display:flex;align-items:center;gap:12px;background:none;border:0;padding:0;color:#10294d;text-align:left;min-height:24px}
.radio-mark{width:24px;height:24px;border:2px solid #aebed1;border-radius:50%;flex-shrink:0}.region-option.active .radio-mark{border:7px solid #1677f2}
.region-option b{font-size:15px}.region-option small{font-size:14px;color:#496789;margin-left:4px}
.region-box{margin-left:40px;padding:8px 12px;border:1px solid #cfe0f3;border-radius:7px;background:#eef6ff;display:grid;grid-template-columns:auto 1fr;gap:3px 12px;align-items:center;min-height:39px}
.region-box span{font-size:13px;color:#496789}.region-box b{font-size:15px;color:#0870ed}.region-box small{font-size:11px;color:#617a9c;grid-column:1/-1;display:none}
.manual-region-box{margin-left:40px;margin-bottom:8px}.manual-region-box select{width:100%;height:36px;border:1px solid #d2deed;border-radius:7px;padding:0 10px;color:#496789;background:#f8fafc;font-size:14px}.manual-region-box select:disabled{color:#7b8da4}
.divider{height:1px;background:#e3ebf4}.amount-title{margin-top:10px}
.amount-row{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;padding:0 22px}
.quick{height:41px;border:1px solid #d2deed;border-radius:8px;background:#fff;color:#10294d;font-size:16px;font-weight:750}.quick.active{background:#1677f2;border-color:#1677f2;color:#fff}.quick:hover{border-color:#1677f2}
.direct-wrap{grid-column:1/-1;font-size:12px;color:#496789;order:5}.direct-wrap summary{cursor:pointer}.direct-wrap label{display:none}.direct-input-line{display:flex;align-items:center;gap:8px;margin-top:6px}.direct-input-line input{width:100%;min-width:0;padding:7px;border:1px solid #d2deed;border-radius:6px}.direct-input-line span{white-space:nowrap}
.slider-block{position:relative;margin:19px 22px 10px;padding-top:5px}
#amount-range{width:100%;margin:0;height:7px;appearance:none;background:linear-gradient(to right,#1677f2 0 var(--pct,0%),#cfd9e6 var(--pct,0%) 100%);border-radius:999px;cursor:pointer}
#amount-range::-webkit-slider-thumb{appearance:none;width:27px;height:27px;border-radius:50%;background:#fff;border:4px solid #1677f2;box-shadow:0 2px 5px #1677f233}
#amount-range::-moz-range-thumb{width:20px;height:20px;border-radius:50%;background:#fff;border:4px solid #1677f2}
.amount-bubble{position:absolute;top:-22px;transform:translateX(-50%);background:#1677f2;color:#fff;border-radius:4px;padding:2px 6px;font-size:13px;white-space:nowrap}
.scale-labels{position:relative;height:18px;margin-top:9px}.scale-labels span{position:absolute;transform:translateX(-50%);font-size:11px;color:#496789;white-space:nowrap}.scale-labels span:first-child{transform:none}.scale-labels span:last-child{transform:translateX(-100%)}
@media(max-width:450px){.filter-note{display:none}.filter-heading{font-size:19px}.field-title{font-size:16px}.region-option small{font-size:12px}.region-box{margin-left:34px}.scale-labels span{font-size:10px}}
"""

FILTER_CONTROLS_JS = r"""
const POINTS = [[0,0],[18,100000],[48,500000],[68,1000000],[84,3000000],[100,10000000]];

function clamp(v,a,b){ return Math.max(a,Math.min(b,v)); }
function amountFromPos(pos){
  pos=clamp(Number(pos)||0,0,100);
  for(let i=0;i<POINTS.length-1;i++){
    const [p1,a1]=POINTS[i], [p2,a2]=POINTS[i+1];
    if(pos>=p1 && pos<=p2){
      const r=(pos-p1)/(p2-p1);
      return Math.round((a1+(a2-a1)*r)/10000)*10000;
    }
  }
  return 10000000;
}
function posFromAmount(amount){
  amount=Math.max(0,Number(amount)||0);
  if(amount>=10000000) return 100;
  for(let i=0;i<POINTS.length-1;i++){
    const [p1,a1]=POINTS[i], [p2,a2]=POINTS[i+1];
    if(amount>=a1 && amount<=a2){
      const r=(amount-a1)/(a2-a1 || 1);
      return p1+(p2-p1)*r;
    }
  }
  return 100;
}
function fmt(n){ return (Number(n)||0).toLocaleString("ko-KR")+"원"; }

export default function(component){
  const {parentElement,data,setStateValue}=component;
  const autoBtn=parentElement.querySelector("#region-auto");
  const manualBtn=parentElement.querySelector("#region-manual");
  const autoBox=parentElement.querySelector("#auto-region-box");
  const manualBox=parentElement.querySelector("#manual-region-box");
  const manualSelect=parentElement.querySelector("#manual-region-select");
  const autoValue=parentElement.querySelector("#auto-region-value");
  const autoNote=parentElement.querySelector("#auto-region-note");
  const quicks=[...parentElement.querySelectorAll(".quick")];
  const direct=parentElement.querySelector("#direct-amount");
  const range=parentElement.querySelector("#amount-range");
  const bubble=parentElement.querySelector("#amount-bubble");

  const regions=data?.regions || [];
  const mode=data?.region_mode || "auto";
  const manualRegion=data?.manual_region || regions[0] || "";
  const autoRegion=data?.auto_region || "파일 업로드 후 자동 선택";
  const autoCount=Number(data?.auto_count || 0);
  const amount=Math.max(0,Number(data?.amount || 0));

  if(manualSelect.options.length !== regions.length){
    manualSelect.innerHTML="";
    regions.forEach(r=>{ const o=document.createElement("option"); o.value=r; o.textContent=r; manualSelect.appendChild(o); });
  }
  manualSelect.value=manualRegion;
  autoValue.textContent=autoRegion;
  autoNote.textContent=autoCount>0 ? `기존 주소에서 가장 많이 확인된 지역 · ${autoCount.toLocaleString("ko-KR")}건 확인` : "파일 업로드 후 기존 주소를 기준으로 자동 선택됩니다.";

  function paintMode(next){
    autoBtn.classList.toggle("active",next==="auto");
    manualBtn.classList.toggle("active",next==="manual");
    autoBox.style.display="grid";
    manualSelect.disabled=next!=="manual";
    autoBtn.setAttribute("aria-pressed",String(next==="auto"));
    manualBtn.setAttribute("aria-pressed",String(next==="manual"));
    manualBox.classList.toggle("show",next==="manual");
  }
  function paintAmount(next){
    next=Math.max(0,Number(next)||0);
    direct.value=String(Math.round(next));
    const p=posFromAmount(next);
    range.value=String(p);
    range.style.setProperty("--pct",p+"%");
    bubble.textContent=fmt(next);
    bubble.style.left=`clamp(42px, ${p}%, calc(100% - 42px))`;
    quicks.forEach(b=>b.classList.toggle("active",Number(b.dataset.value)===next));
  }

  paintMode(mode);
  paintAmount(amount);

  autoBtn.onclick=()=>{ paintMode("auto"); setStateValue("region_mode","auto"); };
  manualBtn.onclick=()=>{ paintMode("manual"); setStateValue("region_mode","manual"); };
  manualSelect.onchange=()=>setStateValue("manual_region",manualSelect.value);

  quicks.forEach(btn=>{
    btn.onclick=()=>{
      const v=Number(btn.dataset.value);
      paintAmount(v);
      setStateValue("amount",v);
    };
  });

  range.oninput=()=>{
    const p=Number(range.value);
    const v=amountFromPos(p);
    paintAmount(v);
  };
  range.onchange=()=>{
    const v=amountFromPos(Number(range.value));
    setStateValue("amount",v);
  };
  direct.onchange=()=>{
    const v=Math.max(0,Number(direct.value)||0);
    paintAmount(v);
    setStateValue("amount",v);
  };
  direct.onkeydown=(e)=>{ if(e.key==="Enter"){ direct.blur(); } };
}
"""


ADDRESS_WORKFLOW_HTML = r"""
<div class="address-shell">
  <div class="address-head">
    <div class="head-left">
      <div class="pin"><span></span></div>
      <div>
        <div class="address-title">주소 보완</div>
        <div class="address-sub">API와 기존 사용자 주소를 활용하여 주소를 채운 후, 남은 업체는 직접 입력합니다.</div>
      </div>
    </div>
    <div id="missing-card" class="missing-card">
      <div class="doc-icon"></div>
      <div><b id="missing-count">주소 미확인 0건</b><span>(중복 업체를 포함한 전체 미확인 계약 건수)</span></div>
    </div>
  </div>

  <div class="step-grid">
    <section class="step-card blue">
      <div class="step-title"><em>1</em><b>API로 주소 채우기</b></div>
      <p>나라장터 → 학교장터 → 공정위 → 지역화폐 가맹점 순으로 조회<br>사업자번호 10자리 정확일치만 반영 · 개별 조회 24시간 캐시</p>
      <button id="api-btn" class="main-btn blue">⌕&nbsp;&nbsp; API로 주소 채우기</button>
      <div class="count-box blue"><span class="count-icon">▦</span><div><b id="api-count">API 조회대상 0개 업체</b><small>(중복 사업자번호 제거 후 실제 조회할 업체 수)</small></div></div>
    </section>

    <section class="step-card green">
      <div class="step-title"><em>2</em><b>사용자 주소 채우기</b></div>
      <p>공동 주소정보에서 이전에 입력했던 주소를 한꺼번에 불러옵니다.<br>10자리 사업자번호 정확일치만 자동 반영됩니다.</p>
      <button id="bulk-btn" class="main-btn green">▣&nbsp;&nbsp; 이전 주소 한꺼번에 불러오기 · 0개</button>
      <div class="count-box green"><span class="count-icon">♻</span><div><b id="user-count">사용자 주소 보유 0개 업체</b><small>(현재 미확인 업체 중 공동 DB에 주소가 있는 업체 수)</small></div></div>
    </section>

    <section class="step-card orange">
      <div class="step-title"><em>3</em><b>남은 주소 직접 입력</b></div>
      <p>위 과정으로도 주소가 채워지지 않은 업체를 직접 확인하고<br>주소를 입력한 후, 한 번에 적용합니다.</p>
      <button id="manual-btn" class="main-btn orange">✎&nbsp;&nbsp; 주소 미확인 업체 확인 · 0개</button>
      <div class="count-box orange"><span class="count-icon">⇩</span><div><b id="direct-count">직접 입력 필요 0개 업체</b><small>(API와 사용자 주소로도 채워지지 않은 업체 수)</small></div></div>
    </section>
  </div>

  <div class="workflow">
    <div class="workflow-label"><span>i</span><b>작업 순서 안내</b></div>
    <div class="wf"><em>1</em>자료 입력</div><i>→</i>
    <div class="wf"><em>2</em>API로 주소 채우기</div><i>→</i>
    <div class="wf"><em>3</em>사용자 주소 채우기</div><i>→</i>
    <div class="wf"><em>4</em>남은 주소 직접 입력</div><i>→</i>
    <div class="wf"><em>5</em>입력한 주소 적용 및 결과 다운로드</div>
    <details class="usage"><summary>▣ 사용방법 보기</summary><div class="usage-body"><b>계약자료 처리 순서</b><ol><li>자료관리 Excel 파일을 하나 이상 업로드합니다.</li><li>기준 지역과 집계 금액을 확인한 뒤 API로 주소를 조회합니다.</li><li>기존 사용자 주소를 불러오고 남은 주소를 직접 입력합니다.</li><li>입력한 주소 적용을 누른 뒤 결과 파일을 다운로드합니다.</li></ol><p>파일 다운로드 경로: 학교(재무)회계 → 계약관리 → 계약자료관리 → 자료관리</p></div></details>
  </div>
</div>
"""

ADDRESS_WORKFLOW_CSS = r"""
:host{font-family:'Pretendard','Noto Sans KR',system-ui,-apple-system,sans-serif;color:#10294b;line-height:1.35}
*{box-sizing:border-box}.address-shell{width:100%;padding:14px 18px 6px;border:1px solid #d9e4f0;border-radius:11px;background:#fff;box-shadow:0 2px 5px #10294d06}
.address-head{display:flex;align-items:center;justify-content:space-between;gap:18px;margin:0 0 12px;min-height:78px}
.head-left{display:flex;align-items:center;gap:14px}.pin{width:48px;height:48px;border-radius:50% 50% 50% 0;background:linear-gradient(180deg,#2c89ff,#0d6fec);transform:rotate(-45deg);position:relative;flex:0 0 48px}.pin span{position:absolute;width:15px;height:15px;border-radius:50%;background:#fff;left:16px;top:16px}
.address-title{font-size:25px;font-weight:900;letter-spacing:-.045em}.address-sub{font-size:16px;color:#5a7592;margin-top:3px}
.missing-card{min-width:39%;min-height:78px;display:flex;align-items:center;gap:13px;padding:11px 17px;border-radius:10px;background:#fff1f2;border:1px solid #ffc9ce;color:#ed2d36}.missing-card.complete{background:#f0fbf6;border-color:#c9edd9;color:#079657}
.doc-icon{width:31px;height:38px;border:4px solid currentColor;border-radius:3px;position:relative}.doc-icon:after{content:"";position:absolute;right:-4px;top:-4px;width:12px;height:12px;background:#fff;border-left:4px solid currentColor;border-bottom:4px solid currentColor}
.missing-card b{font-size:26px;display:block;line-height:1.15}.missing-card span{font-size:14px;color:#687d96;display:block;margin-top:4px}
.step-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;align-items:stretch}
.step-card{border:1px solid;border-radius:10px;padding:8px 18px 12px;background:#fff;min-height:263px;display:grid;grid-template-rows:auto 1fr auto auto}.step-card.blue{border-color:#bedcff;background:linear-gradient(120deg,#f2f8ff,#fbfdff)}.step-card.green{border-color:#c6ead7;background:linear-gradient(120deg,#f0faf6,#fbfefd)}.step-card.orange{border-color:#ffd8b9;background:linear-gradient(120deg,#fff8f2,#fffcfa)}
.step-title{display:flex;align-items:center;gap:16px;margin-bottom:6px}.step-title em{font-style:normal;width:48px;height:48px;flex-shrink:0;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:23px;font-weight:900}.step-title b{font-size:24px;letter-spacing:-.035em}.blue .step-title{color:#0870df}.blue .step-title em{background:#1677f2}.green .step-title{color:#079653}.green .step-title em{background:#0aa35e}.orange .step-title{color:#ef6a08}.orange .step-title em{background:#f97316}
.step-card p{font-size:15px;color:#506d8c;line-height:1.55;min-height:46px;margin:0 0 10px;flex:1}
.main-btn{width:100%;min-height:49px;padding:8px;border:0;border-radius:7px;color:#fff;font:750 19px 'Pretendard','Malgun Gothic',sans-serif;cursor:pointer;box-shadow:0 2px 5px rgba(0,0,0,.06)}.main-btn.blue{background:#1677f2}.main-btn.green{background:#0aa35e}.main-btn.orange{background:#f97316}.main-btn:disabled{cursor:not-allowed;opacity:.45}
.count-box{display:flex;align-items:center;gap:10px;margin-top:13px;padding:9px 10px;min-height:69px;border:1px solid;border-radius:8px}.count-icon{width:46px;height:46px;flex-shrink:0;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:15px}.count-box b{display:block;font-size:16px}.count-box small{display:block;font-size:13px;color:#657b93;margin-top:2px}.count-box.blue{background:#f2f8ff;border-color:#cee3ff;color:#116bc8}.count-box.blue .count-icon{background:#dfeeff;color:#1677f2}.count-box.green{background:#f0fbf6;border-color:#ccebdc;color:#087f4b}.count-box.green .count-icon{background:#ddf4e8;color:#0aa35e}.count-box.orange{background:#fff7ef;border-color:#ffdabe;color:#d95d07}.count-box.orange .count-icon{background:#ffead8;color:#f97316}
.workflow{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:14px;padding:10px 16px;position:relative;padding-right:182px;min-height:88px;background:#eff6ff;border:1px solid #b8d7ff;border-radius:9px;color:#126ac9;font-size:16px;font-weight:750}.workflow-label{display:flex;align-items:center;gap:10px;flex-basis:100%;font-size:19px}.workflow-label span{display:inline-flex;width:23px;height:23px;border-radius:50%;align-items:center;justify-content:center;background:#1677f2;color:#fff}.wf{display:inline-flex;align-items:center;gap:6px}.wf em{font-style:normal;display:inline-flex;width:29px;height:29px;border-radius:50%;align-items:center;justify-content:center;background:#1677f2;color:#fff}.workflow>i{font-style:normal;color:#7f9dbc;font-size:17px}
.usage{position:absolute;right:16px;top:20px;font-size:15px;font-weight:500}.usage summary{cursor:pointer;padding:12px 17px;border:1px solid #b8d7ff;border-radius:8px;list-style:none;background:#f5f9ff}.usage[open]{position:static;flex-basis:100%}.usage-body{color:#496789;font-size:15px;line-height:1.6}.usage-body p{margin:4px 0}.usage-body ol{padding-left:24px}
button:focus-visible,summary:focus-visible{outline:3px solid #89baff;outline-offset:3px}
@media(min-width:901px) and (max-width:1350px){.step-title b{font-size:20px}.main-btn{font-size:16px}.step-card p{font-size:14px}.workflow{font-size:13px;gap:10px}.address-sub{font-size:13px}}
@media(max-width:900px){.step-grid{grid-template-columns:1fr}.missing-card{min-width:0}.address-head{align-items:stretch;flex-direction:column}.step-card{min-height:0}.workflow{padding-right:16px}.usage{position:static;flex-basis:100%}.address-sub{font-size:14px}.missing-card b{font-size:22px}}
"""

ADDRESS_WORKFLOW_JS = r"""
export default function(component){
  const {parentElement,data,setTriggerValue}=component;
  const missing=Number(data?.missing_count || 0);
  const apiCount=Number(data?.api_count || 0);
  const userCount=Number(data?.user_count || 0);
  const directCount=Number(data?.direct_count || 0);
  const manualCount=Number(data?.manual_count || 0);

  const card=parentElement.querySelector("#missing-card");
  const missingText=parentElement.querySelector("#missing-count");
  missingText.textContent=data?.empty ? "자료 업로드 대기" : missing>0 ? `주소 미확인 ${missing.toLocaleString("ko-KR")}건` : "주소 확인 완료";
  card.classList.toggle("complete",missing===0 && !data?.empty);

  parentElement.querySelector("#api-count").textContent=`API 조회대상 ${apiCount.toLocaleString("ko-KR")}개 업체`;
  parentElement.querySelector("#user-count").textContent=`사용자 주소 보유 ${userCount.toLocaleString("ko-KR")}개 업체`;
  parentElement.querySelector("#direct-count").textContent=`직접 입력 필요 ${directCount.toLocaleString("ko-KR")}개 업체`;

  const apiBtn=parentElement.querySelector("#api-btn");
  const bulkBtn=parentElement.querySelector("#bulk-btn");
  const manualBtn=parentElement.querySelector("#manual-btn");
  bulkBtn.textContent=`▣  이전 주소 한꺼번에 불러오기 · ${userCount.toLocaleString("ko-KR")}개`;
  manualBtn.textContent=`✎  주소 미확인 업체 확인 · ${manualCount.toLocaleString("ko-KR")}개`;

  apiBtn.disabled=apiCount===0;
  bulkBtn.disabled=userCount===0;
  manualBtn.disabled=manualCount===0;

  apiBtn.onclick=()=>setTriggerValue("api",true);
  bulkBtn.onclick=()=>setTriggerValue("bulk",true);
  manualBtn.onclick=()=>setTriggerValue("manual",true);
}
"""


filter_controls_component = st.components.v2.component(
    "mode1_filter_controls",
    html=FILTER_CONTROLS_HTML,
    css=FILTER_CONTROLS_CSS,
    js=FILTER_CONTROLS_JS,
    isolate_styles=True,
)

address_workflow_component = st.components.v2.component(
    "mode1_address_workflow",
    html=ADDRESS_WORKFLOW_HTML,
    css=ADDRESS_WORKFLOW_CSS,
    js=ADDRESS_WORKFLOW_JS,
    isolate_styles=True,
)

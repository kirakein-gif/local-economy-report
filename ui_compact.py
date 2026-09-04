COMPACT_UI_CSS = r'''
<style>
/* v1.6 — 기준 시안에 맞춘 native Streamlit 영역 보정 */
.block-container{
  max-width:1580px!important;
  padding-top:.8rem!important;
  padding-bottom:1.4rem!important;
  padding-left:1.35rem!important;
  padding-right:1.35rem!important;
}
.standard-hero{margin:0 0 15px!important;min-height:82px!important}
.hero-building{width:56px!important;height:56px!important;font-size:2.35rem!important}
.hero-title{font-size:1.9rem!important;line-height:1.12!important}
.hero-sub{font-size:.96rem!important;margin-top:5px!important}
.hero-info{padding:12px 16px!important;max-width:430px!important;font-size:.82rem!important}
.hero-info small{font-size:.68rem!important;margin-top:3px!important}

/* 자료입력 카드 */
.st-key-upload_card [data-testid="stVerticalBlockBorderWrapper"]{
  min-height:0!important;
  height:365px!important;
  border-color:#d7e3f0!important;
  border-radius:12px!important;
  box-shadow:0 2px 8px rgba(44,86,133,.035)!important;
}
.st-key-upload_card [data-testid="stVerticalBlockBorderWrapper"]>div{padding:1rem 1.1rem!important}
.panel-head{margin-bottom:10px!important;gap:13px!important}
.panel-icon{width:46px!important;height:46px!important;font-size:1.5rem!important}
.panel-title{font-size:1.45rem!important;font-weight:900!important}
.panel-desc{font-size:.87rem!important;margin-top:4px!important}

/* 파일 업로더 — Streamlit 기능은 유지하되 시안처럼 크게 */
.st-key-upload_card [data-testid="stFileUploaderDropzone"],
.st-key-upload_card [data-testid="stFileUploadDropzone"]{
  min-height:174px!important;
  height:174px!important;
  background:#fcfdff!important;
  border:1.5px dashed #bfd0e3!important;
  border-radius:10px!important;
  padding:1rem!important;
}
.st-key-upload_card [data-testid="stFileUploaderDropzoneInstructions"]{
  display:none!important;
}
.st-key-upload_card [data-testid="stFileUploaderDropzone"] button,
.st-key-upload_card [data-testid="stFileUploadDropzone"] button{
  min-height:42px!important;
  border-radius:8px!important;
  background:#fff!important;
  color:#153a63!important;
  border:1px solid #cbd8e6!important;
  font-size:.86rem!important;
  font-weight:800!important;
}
.drop-guide{
  margin-top:-126px!important;
  position:relative!important;
  z-index:1!important;
  pointer-events:none!important;
  text-align:center!important;
}
.drop-guide .drop-cloud{font-size:2.1rem!important;margin-bottom:6px!important}
.drop-guide b{font-size:.95rem!important}
.drop-guide span{font-size:.78rem!important;margin-top:5px!important}
.source-path-guide{
  margin-top:78px!important;
  padding:9px 12px!important;
  font-size:.78rem!important;
  line-height:1.5!important;
}
.source-path-guide small{font-size:.7rem!important}
.upload-checks{
  margin-top:8px!important;
  gap:4px!important;
  font-size:.76rem!important;
  line-height:1.38!important;
}
/* 업로드 후에는 파일칩을 우선하고 오버레이 제거 */
.st-key-upload_card:has([data-testid="stFileUploaderFile"]) .drop-guide,
.st-key-upload_card:has([data-testid="stFileUploaderFileName"]) .drop-guide{display:none!important}
.st-key-upload_card:has([data-testid="stFileUploaderFile"]) .source-path-guide,
.st-key-upload_card:has([data-testid="stFileUploaderFileName"]) .source-path-guide{margin-top:10px!important}

/* 커스텀 컴포넌트와 주변 Streamlit 블록 간 간격 */
.st-key-mode1_filter_controls_v2{margin:0!important}
.st-key-mode1_address_workflow_v2{margin-top:10px!important;margin-bottom:4px!important}

/* 알림과 상세입력 */
[data-testid="stAlert"]{font-size:.86rem!important;padding:.68rem .82rem!important;border-radius:8px!important}
[data-testid="stExpander"]{border-radius:9px!important;border-color:#cfdcea!important}
[data-testid="stExpander"] summary{font-size:.9rem!important;font-weight:760!important}
[data-testid="stExpander"] input{font-size:.86rem!important;min-height:40px!important}
[data-testid="stExpander"] p,[data-testid="stExpander"] .stCaption{font-size:.8rem!important}

/* 지역별 구매 비중 */
.region-card{margin-top:10px!important;padding:13px 15px!important;border-radius:10px!important}
.region-card .work-title{font-size:1.03rem!important;font-weight:850!important}
.region-track{height:9px!important;margin:11px 0 9px!important}
.region-legend{font-size:.8rem!important;gap:20px!important}

/* 결과 파일 */
.section-title{font-size:1.18rem!important;font-weight:900!important;margin:14px 0 8px!important}
.card-title{font-size:1.02rem!important;font-weight:850!important;line-height:1.2!important}
.card-desc{font-size:.78rem!important;line-height:1.45!important;margin-top:3px!important}
.small-file-icon{width:38px!important;height:38px!important;font-size:1rem!important}
div.stDownloadButton>button{
  min-height:44px!important;
  font-size:.9rem!important;
  font-weight:800!important;
}
.result-step-box{
  border:1px solid #dbe7f4;
  background:#f8fbff;
  border-radius:8px;
  padding:8px 10px;
  margin-top:7px;
}
.result-step-box b{display:block;font-size:.84rem;color:#143a65;line-height:1.3}
.result-step-box span{display:block;font-size:.72rem;color:#647b96;line-height:1.4;margin-top:2px}

/* 공통 native 버튼/입력은 지나치게 작지 않게 */
div.stButton>button{font-size:.86rem!important;min-height:40px!important}
[data-testid="stNumberInput"] input,[data-baseweb="select"]>div{font-size:.86rem!important}

/* 사이드바는 콘텐츠보다 한 단계 작게 유지 */
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p{font-size:.82rem!important}

@media(max-width:1100px){
  .st-key-upload_card [data-testid="stVerticalBlockBorderWrapper"]{height:auto!important}
  .hero-title{font-size:1.55rem!important}
  .hero-info{max-width:360px!important}
}
@media(max-width:760px){
  .standard-hero{display:block!important}
  .hero-info{margin-top:10px!important;max-width:none!important}
}
</style>
'''

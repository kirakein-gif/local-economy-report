APP_CSS = r"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
:root{--blue:#2563EB;--blue2:#1D4ED8;--soft:#EFF6FF;--ink:#172033;--muted:#667085;--bg:#F7F9FC;--line:#E4EAF2;--green:#16A36A;--greens:#ECFDF3;--amber:#D97706;--ambers:#FFF8E7;--card:#FFFFFF}
html,body,[class*="css"]{font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
#MainMenu,footer{visibility:hidden}
header[data-testid="stHeader"]{background:transparent!important;height:2.25rem!important;visibility:visible!important}
[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{visibility:visible!important;display:flex!important}
.stApp{background:var(--bg)}
.block-container{max-width:1320px;padding-top:.55rem!important;padding-bottom:1.2rem!important;padding-left:1.25rem!important;padding-right:1.25rem!important}
[data-testid="stSidebar"]{background:#FBFCFE!important;border-right:1px solid var(--line);min-width:280px!important;max-width:300px!important}
[data-testid="stSidebar"]>div:first-child{padding-top:.55rem!important}
[data-testid="stSidebar"] *{letter-spacing:-.01em}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:var(--ink)!important}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] .stCaption{color:#475467!important;font-size:.77rem!important}
[data-testid="stSidebar"] hr{border-color:var(--line);margin:.55rem 0!important}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"]{margin-bottom:.12rem!important}
[data-testid="stSidebar"] [data-baseweb="select"]>div,[data-testid="stSidebar"] input{min-height:34px!important;font-size:.8rem!important}
[data-testid="stFileUploaderDropzone"],[data-testid="stFileUploadDropzone"]{background:#fff!important;border:1px dashed #B8C7DD!important;border-radius:10px!important;min-height:72px!important;padding:.55rem!important}
[data-testid="stFileUploaderDropzone"] *,[data-testid="stFileUploadDropzone"] *{color:#344054!important;fill:#344054!important}
div.stButton>button,div.stDownloadButton>button{background:var(--blue)!important;color:#fff!important;border:1px solid var(--blue)!important;border-radius:8px!important;min-height:36px!important;font-weight:700!important;font-size:.8rem!important;transition:.12s ease}
div.stButton>button *,div.stButton>button p,div.stButton>button span,div.stDownloadButton>button *,div.stDownloadButton>button p,div.stDownloadButton>button span{color:#fff!important}
div.stButton>button:hover,div.stDownloadButton>button:hover{background:var(--blue2)!important;border-color:var(--blue2)!important}
div.stDownloadButton>button{width:100%}
.app-head{display:flex;justify-content:space-between;gap:14px;align-items:center;margin-bottom:9px;padding:3px 0 9px;border-bottom:1px solid var(--line)}
.app-brand{display:flex;gap:9px;align-items:center}.app-logo{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#2F6FED,#5B8DF6);display:flex;align-items:center;justify-content:center;color:#fff;font-size:17px;box-shadow:0 4px 10px rgba(37,99,235,.14)}
.app-title{font-size:1.18rem;font-weight:800;color:var(--ink);letter-spacing:-.035em}.app-sub{font-size:.74rem;color:var(--muted);margin-top:1px}.live-chip{background:#fff;border:1px solid var(--line);border-radius:999px;padding:5px 9px;font-size:.7rem;color:#475467;white-space:nowrap}
.sidebar-brand{font-size:.94rem;font-weight:800;color:var(--ink);margin:1px 0 10px}.side-section{font-size:.75rem;font-weight:800;color:#344054;margin:1px 0 5px}.side-gap{margin-top:11px!important}.side-help{font-size:.68rem;color:#667085;line-height:1.4;margin-top:3px}
.section-title{font-size:.88rem;font-weight:800;color:var(--ink);margin:13px 0 6px}.compact-title{margin-top:8px!important}.card-title{font-size:.88rem;font-weight:800;color:var(--ink);margin-bottom:3px}.card-desc{font-size:.73rem;color:var(--muted);line-height:1.4;margin-bottom:7px}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line)!important;border-radius:10px!important;background:#fff!important;box-shadow:0 1px 2px rgba(16,24,40,.02)}
[data-testid="stVerticalBlockBorderWrapper"]>div{padding:.7rem .8rem!important}
.mini-info{font-size:.76rem;line-height:1.5;color:#475467;background:#F8FAFD;border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.mini-status{font-size:.72rem;line-height:1.35;border-radius:8px;padding:7px 10px;min-height:36px}.warn-mini{background:var(--ambers);border:1px solid #F5D99A;color:#9A6700}.ok-mini{background:var(--greens);border:1px solid #B9EACF;color:#087A50}
.kpi-row{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0 10px}.kpi-card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 12px;box-shadow:0 1px 2px rgba(16,24,40,.02)}.kpi-label{font-size:.7rem;color:var(--muted);font-weight:650;margin-bottom:3px}.kpi-value{font-size:1.22rem;font-weight:800;color:var(--ink);letter-spacing:-.035em;line-height:1.2}.kpi-unit{font-size:.75rem;color:var(--muted);font-weight:600;margin-left:2px}.kpi-note{font-size:.68rem;color:var(--muted);margin-top:3px}.small-value{font-size:.9rem!important;padding-top:3px}.compact-kpi{margin-top:7px!important;margin-bottom:8px!important}
.work-card,.download-card,.mode-banner,.empty-card,.info-panel,.region-card{background:#fff;border:1px solid var(--line);border-radius:10px}.work-card{padding:11px 13px;margin-bottom:9px}.work-title{font-size:.84rem;font-weight:800;color:var(--ink);margin-bottom:3px}.work-desc{font-size:.72rem;color:var(--muted);line-height:1.42}.status{display:inline-flex;align-items:center;border-radius:999px;padding:4px 8px;font-size:.7rem;font-weight:750}.status.ok{background:var(--greens);color:var(--green)}.status.warn{background:var(--ambers);color:var(--amber)}
.download-card{display:flex;gap:8px;align-items:flex-start;padding:10px 12px;margin-bottom:6px;min-height:64px}.download-icon{width:32px;height:32px;flex:0 0 32px;border-radius:50%;background:var(--soft);display:flex;align-items:center;justify-content:center;font-size:16px}.final-card{margin-top:9px}.mode-banner{padding:12px 14px;margin-bottom:9px}.mode-eyebrow{font-size:.68rem;color:var(--blue);font-weight:800;margin-bottom:2px}.mode-title{font-size:.98rem;color:var(--ink);font-weight:800}.mode-desc{font-size:.72rem;color:var(--muted);margin-top:3px}.info-panel{display:flex;gap:8px;padding:11px 12px;min-height:76px}.info-icon{width:28px;height:28px;flex:0 0 28px;border-radius:50%;background:var(--greens);color:var(--green);display:flex;align-items:center;justify-content:center;font-weight:800}.empty-card{text-align:center;padding:22px 16px;margin-top:8px}.compact-empty{padding:18px 14px!important}.empty-icon{font-size:1.35rem;margin-bottom:4px}
.region-card{padding:10px 12px;margin-top:8px}.compact-region{margin-top:6px!important}.region-track{height:7px;background:#EEF2F7;border-radius:999px;overflow:hidden;display:flex;margin:6px 0}.region-seg-1{background:#2563EB}.region-seg-2{background:#14B8A6}.region-seg-3{background:#CBD5E1}.region-legend{display:flex;gap:13px;flex-wrap:wrap;font-size:.69rem;color:var(--muted)}
.waiting-card{max-width:460px;margin:60px auto;background:#fff;border:1px solid var(--line);border-radius:14px;text-align:center;padding:28px}.waiting-icon{font-size:1.7rem}.waiting-title{font-size:1rem;font-weight:800;color:var(--ink);margin:7px 0 4px}.waiting-desc{font-size:.8rem;color:var(--muted)}.waiting-meta{font-size:.7rem;color:#98A2B3;margin-top:9px}
[data-testid="stAlert"]{padding:.55rem .7rem!important;font-size:.76rem!important;margin:.35rem 0!important}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{font-size:.76rem!important}
@media(max-width:1100px){.kpi-row{grid-template-columns:1fr 1fr}.block-container{padding-left:.8rem!important;padding-right:.8rem!important}}
@media(max-width:700px){.kpi-row{grid-template-columns:1fr}.app-head{display:block}.live-chip{display:inline-block;margin-top:6px}}
</style>
"""

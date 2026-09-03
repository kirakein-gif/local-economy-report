APP_CSS = r"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
:root{
  --background:#ffffff;
  --foreground:#18181b;
  --card:#ffffff;
  --card-foreground:#18181b;
  --muted:#71717a;
  --muted-bg:#f4f4f5;
  --border:#e4e4e7;
  --input:#e4e4e7;
  --primary:#18181b;
  --primary-hover:#27272a;
  --secondary:#f4f4f5;
  --success:#15803d;
  --success-bg:#f0fdf4;
  --warning:#a16207;
  --warning-bg:#fefce8;
}
html,body,[class*="css"]{font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
#MainMenu,footer{visibility:hidden}
header[data-testid="stHeader"]{background:#fff!important;height:2.2rem!important;visibility:visible!important;border-bottom:0!important}
[data-testid="stSidebarCollapseButton"],[data-testid="stSidebar"] [data-testid="baseButton-header"],[data-testid="stSidebar"] button[kind="header"]{display:none!important;visibility:hidden!important}
[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{visibility:visible!important;display:flex!important}
.stApp{background:var(--background);color:var(--foreground)}
.block-container{max-width:1400px;padding-top:.45rem!important;padding-bottom:1.5rem!important;padding-left:1.5rem!important;padding-right:1.5rem!important}

[data-testid="stSidebar"]{background:#fafafa!important;border-right:1px solid var(--border);min-width:285px!important;max-width:305px!important}
[data-testid="stSidebar"]>div:first-child{padding-top:.7rem!important;padding-left:.9rem!important;padding-right:.9rem!important}
[data-testid="stSidebar"] *{letter-spacing:-.012em}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] .stCaption{color:#52525b!important;font-size:.82rem!important}
[data-testid="stSidebar"] hr{border-color:var(--border);margin:.65rem 0!important}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"]{margin-bottom:.22rem!important}
[data-testid="stSidebar"] [data-baseweb="select"]>div,[data-testid="stSidebar"] input{min-height:36px!important;font-size:.84rem!important;border-color:var(--input)!important;border-radius:6px!important;background:#fff!important}
[data-testid="stSidebar"] [role="radiogroup"]{gap:4px!important}
[data-testid="stSidebar"] [role="radiogroup"] label{background:transparent;border-radius:6px;padding:5px 6px;margin:0!important}

[data-testid="stFileUploaderDropzone"],[data-testid="stFileUploadDropzone"]{background:#fff!important;border:1px dashed #d4d4d8!important;border-radius:8px!important;min-height:78px!important;padding:.7rem!important}
[data-testid="stFileUploaderDropzone"] *,[data-testid="stFileUploadDropzone"] *{color:#3f3f46!important;fill:#3f3f46!important}

div.stButton>button,div.stDownloadButton>button{background:var(--primary)!important;color:#fff!important;border:1px solid var(--primary)!important;border-radius:6px!important;min-height:36px!important;font-weight:650!important;font-size:.82rem!important;box-shadow:none!important;transition:.12s ease}
div.stButton>button *,div.stButton>button p,div.stButton>button span,div.stDownloadButton>button *,div.stDownloadButton>button p,div.stDownloadButton>button span{color:#fff!important}
div.stButton>button:hover,div.stDownloadButton>button:hover{background:var(--primary-hover)!important;border-color:var(--primary-hover)!important}
div.stDownloadButton>button{width:100%}

.app-head{display:flex;justify-content:space-between;gap:14px;align-items:center;margin-bottom:14px;padding:2px 0 12px;border-bottom:1px solid var(--border)}
.app-brand{display:flex;gap:10px;align-items:center}.app-logo{width:34px;height:34px;border-radius:7px;background:#18181b;display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;font-weight:750;box-shadow:none}
.app-title{font-size:1.24rem;font-weight:720;color:var(--foreground);letter-spacing:-.032em}.app-sub{font-size:.78rem;color:var(--muted);margin-top:2px}.live-chip{background:#fff;border:1px solid var(--border);border-radius:6px;padding:5px 8px;font-size:.73rem;color:#52525b;white-space:nowrap}
.sidebar-brand{font-size:.95rem;font-weight:720;color:var(--foreground);margin:2px 0 10px}.side-section{font-size:.72rem;font-weight:700;color:#71717a;text-transform:uppercase;letter-spacing:.04em;margin:4px 0 6px}.side-gap{margin-top:12px!important}.side-help{font-size:.72rem;color:#71717a;line-height:1.45;margin-top:4px}.developer-note{font-size:.74rem;line-height:1.45;color:#71717a;background:#fff;border:1px solid var(--border);border-radius:7px;padding:8px 9px;margin:6px 0 2px}.developer-note b{color:#3f3f46;font-size:.76rem}

.section-title{font-size:.93rem;font-weight:700;color:var(--foreground);margin:14px 0 7px}.compact-title{margin-top:10px!important}.card-title{font-size:.9rem;font-weight:700;color:var(--foreground);margin-bottom:3px}.card-desc{font-size:.77rem;color:var(--muted);line-height:1.45;margin-bottom:7px}.card-desc.no-margin{margin-bottom:0!important}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--border)!important;border-radius:8px!important;background:#fff!important;box-shadow:none!important}
[data-testid="stVerticalBlockBorderWrapper"]>div{padding:.8rem .9rem!important}
.mini-info{font-size:.8rem;line-height:1.6;color:#52525b;background:#fafafa;border:1px solid var(--border);border-radius:7px;padding:8px 10px}.mini-info b{color:var(--foreground);margin-left:5px}.mini-label{display:inline-block;min-width:62px;color:#71717a;font-size:.72rem}.upload-guide{min-height:76px;display:flex;flex-direction:column;justify-content:center}
.mini-status{font-size:.75rem;line-height:1.4;border-radius:6px;padding:7px 9px;min-height:36px}.warn-mini{background:var(--warning-bg);border:1px solid #fde68a;color:var(--warning)}.ok-mini{background:var(--success-bg);border:1px solid #bbf7d0;color:var(--success)}

.kpi-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:8px 0 11px}.kpi-card{background:#fff;border:1px solid var(--border);border-radius:8px;padding:12px 13px;box-shadow:none}.kpi-label{font-size:.72rem;color:#71717a;font-weight:600;margin-bottom:5px}.kpi-value{font-size:1.42rem;font-weight:720;color:var(--foreground);letter-spacing:-.04em;line-height:1.15}.kpi-unit{font-size:.76rem;color:#71717a;font-weight:500;margin-left:2px}.kpi-note{font-size:.71rem;color:#a1a1aa;margin-top:4px}.small-value{font-size:.96rem!important;padding-top:3px}.compact-kpi{margin-top:0!important;margin-bottom:8px!important}

.work-card,.download-card,.mode-banner,.empty-card,.info-panel,.region-card{background:#fff;border:1px solid var(--border);border-radius:8px}.work-card{padding:12px 13px;margin-bottom:9px}.work-title{font-size:.88rem;font-weight:700;color:var(--foreground);margin-bottom:3px}.work-desc{font-size:.76rem;color:var(--muted);line-height:1.45}.status{display:inline-flex;align-items:center;border:1px solid var(--border);border-radius:999px;padding:3px 8px;font-size:.7rem;font-weight:650;background:#fff}.status.ok{background:var(--success-bg);border-color:#bbf7d0;color:var(--success)}.status.warn{background:var(--warning-bg);border-color:#fde68a;color:var(--warning)}
.download-card{display:flex;gap:9px;align-items:flex-start;padding:11px 12px;margin-bottom:6px;min-height:66px}.download-icon{width:32px;height:32px;flex:0 0 32px;border-radius:7px;background:#f4f4f5;display:flex;align-items:center;justify-content:center;font-size:15px;color:#3f3f46;font-weight:700}.final-card{margin-top:9px}.mode-banner{padding:12px 14px;margin-bottom:10px}.mode-eyebrow{font-size:.7rem;color:#71717a;font-weight:700;text-transform:uppercase;letter-spacing:.04em;margin-bottom:2px}.mode-title{font-size:1rem;color:var(--foreground);font-weight:720}.mode-desc{font-size:.76rem;color:var(--muted);margin-top:3px}.info-panel{display:flex;gap:9px;padding:11px 12px;min-height:74px}.info-icon{width:29px;height:29px;flex:0 0 29px;border-radius:7px;background:#f4f4f5;color:#3f3f46;display:flex;align-items:center;justify-content:center;font-weight:700}.empty-card{text-align:center;padding:24px 16px;margin-top:8px}.compact-empty{padding:20px 14px!important}.empty-icon{font-size:1.32rem;margin-bottom:5px;color:#52525b}
.small-file-icon{width:36px;height:36px;border-radius:7px;background:#f4f4f5;border:1px solid var(--border);color:#3f3f46;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:750;margin:1px auto}.small-file-icon.green-file{background:var(--success-bg);border-color:#bbf7d0;color:var(--success)}.download-side-head{display:flex;align-items:center;gap:10px;margin-bottom:9px}.download-side-head .small-file-icon{margin:0}.file-name-box{font-size:.72rem;line-height:1.4;color:#52525b;background:#fafafa;border:1px solid var(--border);border-radius:6px;padding:7px 8px;margin:7px 0 9px;word-break:break-all}
.region-card{padding:11px 13px;margin-top:8px}.compact-region{margin-top:6px!important}.region-track{height:6px;background:#f4f4f5;border-radius:999px;overflow:hidden;display:flex;margin:8px 0}.region-seg-1{background:#18181b}.region-seg-2{background:#71717a}.region-seg-3{background:#d4d4d8}.region-legend{display:flex;gap:14px;flex-wrap:wrap;font-size:.72rem;color:#71717a}
.waiting-card{max-width:460px;margin:60px auto;background:#fff;border:1px solid var(--border);border-radius:10px;text-align:center;padding:28px}.waiting-icon{font-size:1.55rem}.waiting-title{font-size:1rem;font-weight:720;color:var(--foreground);margin:7px 0 4px}.waiting-desc{font-size:.8rem;color:var(--muted)}.waiting-meta{font-size:.7rem;color:#a1a1aa;margin-top:9px}
[data-testid="stAlert"]{padding:.58rem .72rem!important;font-size:.78rem!important;margin:.35rem 0!important;border-radius:7px!important}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{font-size:.77rem!important;border-radius:8px!important}
[data-testid="stExpander"]{border:1px solid var(--border)!important;border-radius:8px!important;box-shadow:none!important}
@media(max-width:1100px){.kpi-row{grid-template-columns:1fr 1fr}.block-container{padding-left:.9rem!important;padding-right:.9rem!important}}
@media(max-width:700px){.kpi-row{grid-template-columns:1fr}.app-head{display:block}.live-chip{display:inline-block;margin-top:6px}}
</style>
"""

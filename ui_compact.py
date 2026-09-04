COMPACT_UI_CSS = r'''
<style>
[data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"] > style){display:none}
/* Mode 1 native surfaces. Component styles live in ui_components.py. */
.block-container{max-width:1580px;padding:16px 22px 28px!important}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]{gap:16px}
.standard-hero{display:flex;align-items:center;justify-content:space-between;gap:20px;min-height:59px;margin-bottom:10px}
.hero-left{display:flex;align-items:center;gap:16px;min-width:0}
.hero-building{width:54px;flex:0 0 54px;color:#10294d;font-size:48px;font-weight:900;line-height:1}
.hero-title{font-size:28px;font-weight:850;line-height:1.25;letter-spacing:-.04em}
.hero-sub{font-size:16px;color:#496789;margin-top:4px}
.hero-info{display:flex;align-items:center;gap:10px;padding:12px 16px;border:1px solid #c9e0ff;border-radius:11px;background:#eef6ff;color:#315a91;font-size:14px}
.hero-info>span{display:grid;place-items:center;width:22px;height:22px;flex-shrink:0;border-radius:50%;background:#1677f2;color:white;font-weight:800}
.hero-info small{display:none}
:is(.st-key-upload_card,.st-key-final_upload_card){min-height:430px;padding:14px 22px 16px;border:1px solid #d9e4f0;border-radius:11px;background:#fff;box-shadow:0 2px 5px #10294d06;gap:10px}
.panel-head{display:flex;align-items:center;gap:22px;margin:0 3px 4px}
.panel-icon{display:grid;place-items:center;width:40px;height:48px;flex-shrink:0;border-radius:4px;background:#1677f2;color:white;font-size:36px}
.panel-title{font-size:27px;line-height:1.25;font-weight:850;color:#10294d}
.panel-desc{font-size:16px;color:#496789;margin-top:4px}.panel-desc b{font-weight:400}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzone"]{display:flex;flex-direction:column;justify-content:center;gap:16px;min-height:232px;padding:20px;border:1px dashed #c5d3e5;border-radius:11px;background:#f9fbfd;text-align:center}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzone"]>span{order:2;display:flex;justify-content:center;width:100%}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzoneInstructions"]{display:flex;flex-direction:column;align-items:center;gap:6px;margin:0;width:100%}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzoneInstructions"]>div{font-size:0}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzoneInstructions"]>div>span{display:none}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzoneInstructions"]:before{content:'';width:56px;height:48px;background:url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NCA1NCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMTY3N2YyIiBzdHJva2Utd2lkdGg9IjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIwIDQxSDE2YTEyIDEyIDAgMCAxLTEtMjQgMTcgMTcgMCAwIDEgMzMtMSAxMiAxMiAwIDAgMSAxIDI1aC01TTMyIDQ4VjI3bS05IDggOS05IDkgOSIvPjwvc3ZnPg==') center/contain no-repeat;margin-bottom:9px}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzoneInstructions"]:after{content:'여기에 파일을 드래그하거나 클릭하여 업로드하세요';font-size:18px;font-weight:750;color:#123b76;order:1}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzoneInstructions"]>div{order:2}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzoneInstructions"]>div:after{content:'Excel 파일(.xlsx, .xls)을 여러 개 선택할 수 있습니다.';font-size:14px;color:#496789}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzone"] > span button{min-height:48px;padding:0 24px;background:white;border:1px solid #d2deed;border-radius:10px;color:#10294d}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzone"] > span button p{font-size:0}
:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzone"] > span button p:after{content:'파일 선택하기';font-size:17px;font-weight:750}
.upload-checks{display:flex;flex-direction:column;gap:6px;font-size:15px;line-height:1.55;color:#496789}
.upload-checks span::first-letter{color:#1677f2;font-weight:900}
div.stButton>button,div.stDownloadButton>button{border-radius:8px;min-height:44px;font-weight:750}
div.stButton>button[kind="primary"],div.stDownloadButton>button{background:#1677f2;color:#fff;border-color:#1677f2}
.result-step-box{padding:10px;border:1px solid #d9e4f0;border-radius:8px;background:#f8fbff}
.result-step-box b,.result-step-box span{display:block}.result-step-box span{font-size:13px;color:#647b96}
@media(max-width:1100px){.standard-hero{align-items:flex-start}.hero-title{font-size:23px}.hero-info{max-width:340px;font-size:12px}.hero-sub{font-size:14px}.panel-desc{font-size:14px}}
@media(max-width:800px){.standard-hero{flex-direction:column}.hero-info{max-width:none}:is(.st-key-upload_card,.st-key-final_upload_card){min-height:0;padding:16px}.block-container{padding:16px 12px!important}.hero-title{font-size:22px}.hero-building{width:38px;flex-basis:38px}:is(.st-key-upload_card,.st-key-final_upload_card) [data-testid="stFileUploaderDropzoneInstructions"]>span:after{font-size:15px}[data-testid="stHorizontalBlock"]:has(:is(.st-key-upload_card,.st-key-final_upload_card)){flex-direction:column}[data-testid="stHorizontalBlock"]:has(:is(.st-key-upload_card,.st-key-final_upload_card))>[data-testid="stColumn"]{width:100%;flex:1 1 100%}}
</style>
'''

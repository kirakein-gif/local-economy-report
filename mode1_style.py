MODE1_CSS = r"""
<style>
/* 자료 입력 · 검색조건 */
.upload-panel-title{font-size:1.06rem;font-weight:780;color:#18181b;margin-bottom:2px;letter-spacing:-.025em}
.upload-panel-desc{font-size:.77rem;color:#71717a;margin-bottom:10px;line-height:1.5}
.upload-hint{font-size:.76rem;color:#3f3f46;line-height:1.6;margin:4px 0 8px}.upload-hint span{color:#71717a}
.source-path-guide{font-size:.76rem;line-height:1.55;color:#475569;background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;padding:9px 11px;margin-top:7px}.source-path-guide b{color:#1e3a5f}
.filter-panel-title{font-size:.94rem;font-weight:750;color:#18181b;padding-bottom:8px;margin-bottom:7px;border-bottom:1px solid #e4e4e7}.filter-panel-title span{font-size:.7rem;font-weight:600;color:#a1a1aa;margin-left:3px}
.auto-region-box{display:grid;grid-template-columns:auto auto;gap:2px 8px;align-items:center;background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;padding:8px 10px;margin:4px 0 8px}.auto-region-box span{font-size:.7rem;color:#64748b}.auto-region-box b{font-size:.9rem;color:#2563eb}.auto-region-box small{grid-column:1/-1;color:#94a3b8;font-size:.66rem}
.filter-divider{height:1px;background:#e4e4e7;margin:10px 0 9px}.amount-label{font-size:.8rem;font-weight:720;color:#27272a;margin-bottom:6px}.amount-label span{font-size:.69rem;color:#71717a;font-weight:600}
.st-key-data_input_panel [data-testid="stFileUploaderDropzone"],.st-key-data_input_panel [data-testid="stFileUploadDropzone"]{min-height:138px!important;background:#fbfdff!important;border:1px dashed #bfd4ee!important;border-radius:9px!important}
.st-key-data_input_panel [data-testid="stFileUploaderDropzone"] button,.st-key-data_input_panel [data-testid="stFileUploadDropzone"] button{background:#fff!important;color:#18181b!important;border:1px solid #d4d4d8!important}
.st-key-data_input_panel [data-testid="stFileUploaderDropzone"] button *,.st-key-data_input_panel [data-testid="stFileUploadDropzone"] button *{color:#18181b!important}

/* 주소 보완 헤더 */
.address-head-row{display:flex;justify-content:space-between;gap:18px;align-items:center;margin:18px 0 10px;padding:2px 0}
.address-title{font-size:1.16rem;font-weight:790;color:#111827;letter-spacing:-.03em}.address-title:first-letter{color:#2563eb}.address-sub{font-size:.76rem;color:#64748b;margin-top:3px}
.address-missing-card,.address-complete-card{min-width:300px;border-radius:8px;padding:10px 14px;display:flex;flex-direction:column}.address-missing-card{background:#fff1f2;border:1px solid #fecdd3;color:#dc2626}.address-complete-card{background:#f0fdf4;border:1px solid #bbf7d0;color:#15803d}.address-missing-card b,.address-complete-card b{font-size:1.02rem;font-weight:800}.address-missing-card span,.address-complete-card span{font-size:.68rem;margin-top:2px;opacity:.78}

/* 3단계 주소 처리 카드 */
.step-card-title{display:flex;align-items:center;gap:8px;font-size:1rem;font-weight:800;letter-spacing:-.025em;margin-bottom:7px}.step-card-title span{display:inline-flex;align-items:center;justify-content:center;width:29px;height:29px;border-radius:50%;color:#fff;font-size:.8rem}.step-card-title.blue{color:#2563eb}.step-card-title.blue span{background:#2563eb}.step-card-title.green{color:#16a34a}.step-card-title.green span{background:#16a34a}.step-card-title.orange{color:#ea580c}.step-card-title.orange span{background:#f97316}
.step-card-desc{font-size:.73rem;color:#64748b;line-height:1.5;min-height:48px;margin-bottom:8px}.step-count{font-size:.7rem;border-radius:7px;padding:8px 10px;margin:5px 0 8px}.blue-count{background:#eff6ff;border:1px solid #dbeafe;color:#1d4ed8}.green-count{background:#f0fdf4;border:1px solid #dcfce7;color:#15803d}.orange-count{background:#fff7ed;border:1px solid #ffedd5;color:#c2410c}
.st-key-api_address_card{background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%)!important;border-color:#bfdbfe!important}.st-key-user_address_card{background:linear-gradient(180deg,#ffffff 0%,#f7fff9 100%)!important;border-color:#bbf7d0!important}.st-key-manual_address_card{background:linear-gradient(180deg,#ffffff 0%,#fffaf5 100%)!important;border-color:#fed7aa!important}
.st-key-api_address_card div.stButton>button{background:#2563eb!important;border-color:#2563eb!important}.st-key-api_address_card div.stButton>button:hover{background:#1d4ed8!important;border-color:#1d4ed8!important}
.st-key-user_address_card div.stButton>button{background:#16a34a!important;border-color:#16a34a!important}.st-key-user_address_card div.stButton>button:hover{background:#15803d!important;border-color:#15803d!important}.st-key-user_address_card div.stButton>button:disabled{background:#dcfce7!important;border-color:#bbf7d0!important;color:#86a98f!important;opacity:1!important}
.st-key-manual_address_card div.stButton>button{background:#f97316!important;border-color:#f97316!important}.st-key-manual_address_card div.stButton>button:hover{background:#ea580c!important;border-color:#ea580c!important}

.workflow-strip{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 13px;margin:10px 0 12px;color:#2563eb;font-size:.72rem}.workflow-strip b{margin-right:4px}.workflow-strip span{font-weight:680}.workflow-strip i{font-style:normal;color:#94a3b8}

@media(max-width:900px){.address-head-row{align-items:stretch;flex-direction:column}.address-missing-card,.address-complete-card{min-width:0}.step-card-desc{min-height:auto}}
</style>
"""

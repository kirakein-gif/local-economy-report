COMPACT_UI_CSS = r'''
<style>
/* v1.5.4 — 실제 배포 화면 기준 가독성/밀도 보정 */
.block-container{max-width:1600px!important;padding-top:.7rem!important;padding-bottom:1.1rem!important}
.standard-hero{margin-bottom:11px!important;min-height:76px!important}
.hero-building{width:50px!important;height:50px!important;font-size:2.05rem!important}
.hero-title{font-size:1.72rem!important;line-height:1.12!important}.hero-sub{font-size:.92rem!important;margin-top:4px!important}
.hero-info{padding:10px 14px!important;max-width:405px!important;font-size:.8rem!important}.hero-info small{font-size:.68rem!important}

/* 상단 카드: 너무 길지 않되 글자는 크게 */
.st-key-upload_card [data-testid="stVerticalBlockBorderWrapper"],
.st-key-filter_card [data-testid="stVerticalBlockBorderWrapper"]{min-height:0!important;height:405px!important}
.st-key-upload_card [data-testid="stVerticalBlockBorderWrapper"]>div,
.st-key-filter_card [data-testid="stVerticalBlockBorderWrapper"]>div{padding:.82rem .95rem!important}
.panel-head{margin-bottom:7px!important}.panel-icon{width:41px!important;height:41px!important;font-size:1.38rem!important}.panel-title{font-size:1.36rem!important}.panel-desc{font-size:.84rem!important;margin-top:4px!important}

/* 업로드 */
[data-testid="stFileUploaderDropzone"],[data-testid="stFileUploadDropzone"]{min-height:145px!important;padding:.85rem 1rem!important}
.drop-guide{margin-top:-106px!important;font-size:.8rem!important}.drop-guide .drop-cloud{font-size:1.75rem!important;margin-bottom:5px!important}.drop-guide b{font-size:.9rem!important}.drop-guide span{font-size:.72rem!important;margin-top:4px!important}
.source-path-guide{margin-top:59px!important;padding:8px 11px!important;font-size:.76rem!important;line-height:1.45!important}.source-path-guide small{font-size:.67rem!important}.upload-checks{gap:3px!important;margin-top:7px!important;font-size:.72rem!important;line-height:1.38!important}
.st-key-upload_card:has([data-testid="stFileUploaderFile"]) .drop-guide,.st-key-upload_card:has([data-testid="stFileUploaderFileName"]) .drop-guide{display:none!important}
.st-key-upload_card:has([data-testid="stFileUploaderFile"]) .source-path-guide,.st-key-upload_card:has([data-testid="stFileUploaderFileName"]) .source-path-guide{margin-top:11px!important}

/* 검색 조건 */
.filter-title-row{padding-bottom:8px!important;margin-bottom:8px!important}.filter-title{font-size:1.17rem!important}.filter-note{font-size:.69rem!important}.field-title{font-size:.93rem!important;margin:3px 0 5px!important}.field-info{width:18px!important;height:18px!important;font-size:.65rem!important}
.st-key-filter_card [role="radiogroup"]{margin-bottom:2px!important}.st-key-filter_card [role="radiogroup"] label{font-size:.86rem!important}.auto-region-box{padding:8px 10px!important;margin:4px 0 7px!important}.auto-region-box span{font-size:.76rem!important}.auto-region-box b{font-size:1rem!important}.auto-region-box small{font-size:.69rem!important}.filter-divider{margin:8px -.95rem!important}
.st-key-filter_card div.stButton>button{min-height:40px!important;height:40px!important;font-size:.84rem!important}
.st-key-filter_card [data-testid="stNumberInput"]{min-width:150px!important}.st-key-filter_card [data-testid="stNumberInput"] input{min-height:42px!important;height:42px!important;font-size:.9rem!important;font-weight:700!important;padding-left:.65rem!important}.direct-input-label{font-size:.73rem!important;margin-bottom:4px!important;font-weight:700!important}
.st-key-filter_card [data-testid="stSlider"]{margin-top:4px!important}.slider-caption{margin-top:-7px!important;font-size:.67rem!important}.slider-caption b{font-size:.75rem!important}
.nonlinear-scale{display:grid;grid-template-columns:repeat(5,1fr);font-size:.64rem;color:#6f839a;margin-top:-3px;margin-bottom:1px}.nonlinear-scale span:nth-child(1){text-align:left}.nonlinear-scale span:nth-child(2),.nonlinear-scale span:nth-child(3),.nonlinear-scale span:nth-child(4){text-align:center}.nonlinear-scale span:nth-child(5){text-align:right}.nonlinear-note{font-size:.64rem;color:#7b8da3;margin-top:2px}

/* 주소 보완 */
.address-head-row{margin:10px 0 8px!important;min-height:68px!important}.address-pin{width:40px!important;height:40px!important;flex-basis:40px!important}.address-pin:after{width:12px!important;height:12px!important;left:14px!important;top:14px!important}.address-title{font-size:1.43rem!important}.address-sub{font-size:.8rem!important}
.address-missing-card,.address-complete-card{min-width:330px!important;padding:10px 14px!important}.address-missing-card b,.address-complete-card b{font-size:1.28rem!important}.address-missing-card span,.address-complete-card span{font-size:.68rem!important}.status-icon{font-size:1.55rem!important}

/* 3단계 카드 */
.st-key-api_address_card [data-testid="stVerticalBlockBorderWrapper"],
.st-key-user_address_card [data-testid="stVerticalBlockBorderWrapper"],
.st-key-manual_address_card [data-testid="stVerticalBlockBorderWrapper"]{min-height:0!important;height:230px!important}
.st-key-api_address_card [data-testid="stVerticalBlockBorderWrapper"]>div,
.st-key-user_address_card [data-testid="stVerticalBlockBorderWrapper"]>div,
.st-key-manual_address_card [data-testid="stVerticalBlockBorderWrapper"]>div{padding:.78rem .85rem!important}
.step-card-title{font-size:1.16rem!important;margin-bottom:6px!important}.step-card-title span{width:31px!important;height:31px!important;font-size:.82rem!important;margin-right:6px!important}.step-card-desc{min-height:48px!important;font-size:.78rem!important;line-height:1.42!important;margin-bottom:6px!important}
.st-key-api_fill_button button,.st-key-bulk_user_address_button button,.st-key-open_manual_button button{min-height:41px!important;height:41px!important;font-size:.86rem!important}
.step-count{padding:7px 9px!important;margin-top:6px!important;gap:8px!important}.step-count .count-icon{width:27px!important;height:27px!important;font-size:.8rem!important}.step-count b{font-size:.79rem!important}.step-count small{font-size:.65rem!important;margin-top:1px!important}
.workflow-strip{margin:8px 0 8px!important;padding:8px 12px!important;gap:10px!important;font-size:.73rem!important}.workflow-label>span{width:21px!important;height:21px!important}.workflow-step em{width:23px!important;height:23px!important;font-size:.66rem!important}

/* 하단 결과 */
.section-title{margin:10px 0 7px!important;font-size:1.08rem!important}.region-card{margin-top:7px!important;padding:10px 12px!important}.region-card .work-title{font-size:.9rem!important}.region-legend{font-size:.72rem!important}
.card-title{font-size:.97rem!important}.card-desc{font-size:.75rem!important;line-height:1.4!important}.mini-info{font-size:.8rem!important;line-height:1.55!important}.mini-label{font-size:.72rem!important}.result-step-box{margin-top:7px;padding:9px 10px;border:1px solid #dbe7f5;border-radius:8px;background:#f7fbff}.result-step-box b{font-size:.8rem;color:#174a82}.result-step-box span{display:block;font-size:.72rem;color:#607892;line-height:1.5;margin-top:2px}

@media(max-width:1100px){
 .st-key-upload_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-filter_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-api_address_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-user_address_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-manual_address_card [data-testid="stVerticalBlockBorderWrapper"]{height:auto!important}
 .address-missing-card,.address-complete-card{min-width:0!important}
}
</style>
'''

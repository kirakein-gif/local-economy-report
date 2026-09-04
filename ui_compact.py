COMPACT_UI_CSS = r'''
<style>
/* v1.5.3 — 실제 배포 화면 기준 강제 레이아웃 보정 */
.block-container{max-width:1600px!important;padding-top:.65rem!important;padding-bottom:1rem!important}
.standard-hero{margin-bottom:10px!important;min-height:72px!important}
.hero-building{width:48px!important;height:48px!important;font-size:2rem!important}
.hero-title{font-size:1.58rem!important}.hero-sub{font-size:.82rem!important;margin-top:3px!important}
.hero-info{padding:9px 13px!important;max-width:390px!important}

/* 상단 두 카드는 실제 화면에서 같은 높이로 압축 */
.st-key-upload_card [data-testid="stVerticalBlockBorderWrapper"],
.st-key-filter_card [data-testid="stVerticalBlockBorderWrapper"]{min-height:0!important;height:390px!important}
.st-key-upload_card [data-testid="stVerticalBlockBorderWrapper"]>div,
.st-key-filter_card [data-testid="stVerticalBlockBorderWrapper"]>div{padding:.72rem .9rem!important}
.panel-head{margin-bottom:6px!important}.panel-icon{width:38px!important;height:38px!important;font-size:1.3rem!important}.panel-title{font-size:1.2rem!important}.panel-desc{font-size:.75rem!important;margin-top:3px!important}

/* 업로드 박스 */
[data-testid="stFileUploaderDropzone"],[data-testid="stFileUploadDropzone"]{min-height:138px!important;padding:.75rem 1rem!important}
.drop-guide{margin-top:-103px!important;font-size:.75rem!important}.drop-guide .drop-cloud{font-size:1.6rem!important;margin-bottom:4px!important}.drop-guide b{font-size:.8rem!important}.drop-guide span{font-size:.67rem!important;margin-top:3px!important}
.source-path-guide{margin-top:56px!important;padding:7px 10px!important;font-size:.69rem!important;line-height:1.4!important}.source-path-guide small{font-size:.62rem!important}.upload-checks{gap:2px!important;margin-top:6px!important;font-size:.66rem!important;line-height:1.3!important}

/* 파일 업로드가 끝난 화면은 기본 파일 카드가 보이므로 안내 오버레이를 숨김 */
.st-key-upload_card:has([data-testid="stFileUploaderFile"]) .drop-guide,
.st-key-upload_card:has([data-testid="stFileUploaderFileName"]) .drop-guide{display:none!important}
.st-key-upload_card:has([data-testid="stFileUploaderFile"]) .source-path-guide,
.st-key-upload_card:has([data-testid="stFileUploaderFileName"]) .source-path-guide{margin-top:10px!important}

/* 검색 조건 압축 */
.filter-title-row{padding-bottom:7px!important;margin-bottom:7px!important}.filter-title{font-size:1.04rem!important}.filter-note{font-size:.64rem!important}.field-title{font-size:.8rem!important;margin:2px 0 4px!important}
.st-key-filter_card [role="radiogroup"]{margin-bottom:1px!important}.auto-region-box{padding:7px 9px!important;margin:3px 0 6px!important}.filter-divider{margin:7px -.9rem!important}
.st-key-filter_card div.stButton>button{min-height:35px!important;height:35px!important;font-size:.75rem!important}
.st-key-filter_card [data-testid="stNumberInput"] input{min-height:35px!important;height:35px!important;font-size:.72rem!important}
.st-key-filter_card [data-testid="stSlider"]{margin-top:2px!important}.slider-caption{margin-top:-10px!important;font-size:.61rem!important}

/* 주소보완을 상단 카드 바로 밑에 붙임 */
.address-head-row{margin:9px 0 7px!important;min-height:66px!important}.address-pin{width:38px!important;height:38px!important;flex-basis:38px!important}.address-pin:after{width:11px!important;height:11px!important;left:13px!important;top:13px!important}.address-title{font-size:1.25rem!important}.address-sub{font-size:.7rem!important}
.address-missing-card,.address-complete-card{min-width:310px!important;padding:9px 13px!important}.address-missing-card b,.address-complete-card b{font-size:1.15rem!important}.address-missing-card span,.address-complete-card span{font-size:.62rem!important}.status-icon{font-size:1.45rem!important}

/* 3단계 작업카드 높이 통일 및 압축 */
.st-key-api_address_card [data-testid="stVerticalBlockBorderWrapper"],
.st-key-user_address_card [data-testid="stVerticalBlockBorderWrapper"],
.st-key-manual_address_card [data-testid="stVerticalBlockBorderWrapper"]{min-height:0!important;height:214px!important}
.st-key-api_address_card [data-testid="stVerticalBlockBorderWrapper"]>div,
.st-key-user_address_card [data-testid="stVerticalBlockBorderWrapper"]>div,
.st-key-manual_address_card [data-testid="stVerticalBlockBorderWrapper"]>div{padding:.7rem .8rem!important}
.step-card-title{font-size:1.02rem!important;margin-bottom:5px!important}.step-card-title span{width:29px!important;height:29px!important;font-size:.78rem!important;margin-right:5px!important}.step-card-desc{min-height:43px!important;font-size:.67rem!important;line-height:1.38!important;margin-bottom:5px!important}
.st-key-api_fill_button button,.st-key-bulk_user_address_button button,.st-key-open_manual_button button{min-height:37px!important;height:37px!important;font-size:.76rem!important}
.step-count{padding:6px 8px!important;margin-top:5px!important;gap:7px!important}.step-count .count-icon{width:25px!important;height:25px!important;font-size:.75rem!important}.step-count b{font-size:.7rem!important}.step-count small{font-size:.59rem!important;margin-top:1px!important}
.workflow-strip{margin:7px 0 7px!important;padding:7px 11px!important;gap:9px!important;font-size:.66rem!important}.workflow-label>span{width:19px!important;height:19px!important}.workflow-step em{width:21px!important;height:21px!important;font-size:.62rem!important}

/* 결과영역도 같은 밀도로 */
.section-title{margin:9px 0 6px!important}.region-card{margin-top:6px!important;padding:9px 11px!important}.download-card,.info-panel{min-height:58px!important;padding:8px 10px!important}

@media(max-width:1100px){
 .st-key-upload_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-filter_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-api_address_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-user_address_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-manual_address_card [data-testid="stVerticalBlockBorderWrapper"]{height:auto!important}
 .address-missing-card,.address-complete-card{min-width:0!important}
}
</style>
'''

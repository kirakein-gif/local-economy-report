from datetime import date

import pandas as pd
import streamlit as st
from core_logic import (
    CHUNGNAM_REGIONS,
    DEFAULT_TARGET_AMOUNT,
    FALLBACK_COLS,
    file_fingerprint,
    find_source_col,
    load_excel_normalized,
    missing_address_mask,
    normalize_biz_no,
    normalize_contract_type,
)

QUICK_AMOUNTS = [0, 100000, 500000, 1000000]
AMOUNT_SLIDER_MAX = 10000000


def _detect_region_from_addresses(df, col_addr):
    """기존 주소에서 가장 많이 등장하는 충남 시·군을 1차 기준 지역으로 잡습니다."""
    if col_addr is None or col_addr >= df.shape[1]:
        return CHUNGNAM_REGIONS[0], 0

    counts = {region: 0 for region in CHUNGNAM_REGIONS}
    for value in df.iloc[:, col_addr].dropna():
        text = str(value).strip()
        if not text:
            continue
        for region in CHUNGNAM_REGIONS:
            if region in text:
                counts[region] += 1
                break

    best_region, best_count = max(counts.items(), key=lambda item: item[1])
    return best_region, best_count


def _set_amount(value):
    value = int(value)
    st.session_state.amount_number = value
    st.session_state.amount_slider = min(value, AMOUNT_SLIDER_MAX)


def _sync_amount_from_slider():
    st.session_state.amount_number = int(st.session_state.amount_slider)


def _sync_amount_from_number():
    value = int(st.session_state.amount_number or 0)
    st.session_state.amount_slider = min(max(value, 0), AMOUNT_SLIDER_MAX)


def prepare_mode1():
    report_year = 2026
    report_label = '상반기'
    period_start = date(2026, 1, 1)
    period_end = date(2026, 7, 31)

    if 'amount_number' not in st.session_state:
        st.session_state.amount_number = int(DEFAULT_TARGET_AMOUNT)
    if 'amount_slider' not in st.session_state:
        st.session_state.amount_slider = min(int(DEFAULT_TARGET_AMOUNT), AMOUNT_SLIDER_MAX)
    if 'region_mode' not in st.session_state:
        st.session_state.region_mode = '자동 선택'

    # 상단은 표준 UI 이미지처럼 자료 입력 / 검색 조건 2개 카드로 구성합니다.
    left, right = st.columns([1.62, 1], gap='medium')

    with left:
        with st.container(border=True, key='upload_card'):
            st.markdown(
                '''<div class="panel-head">
                    <div class="panel-icon blue-icon">▤</div>
                    <div><div class="panel-title">자료 입력</div>
                    <div class="panel-desc">계약자료 Excel 파일을 업로드하세요. <b>(여러 파일 가능)</b></div></div>
                </div>''',
                unsafe_allow_html=True,
            )
            data_files = st.file_uploader(
                '자료관리목록 Excel',
                type=['xlsx', 'xls'],
                accept_multiple_files=True,
                key='source_files',
                label_visibility='collapsed',
            )
            st.markdown(
                '''<div class="drop-guide">
                    <div class="drop-cloud">☁</div>
                    <b>여기에 파일을 드래그하거나 클릭하여 업로드하세요</b>
                    <span>Excel 파일(.xlsx, .xls)을 여러 개 선택할 수 있습니다.</span>
                </div>''',
                unsafe_allow_html=True,
            )
            st.markdown(
                '''<div class="source-path-guide"><span class="path-info">●</span>
                <b>파일 다운로드 경로 :</b>&nbsp; 학교(재무)회계 → 계약관리 → 계약자료관리 → 자료관리<br>
                <small>해당 메뉴에서 Excel 파일을 내려받아 업로드하세요.</small></div>''',
                unsafe_allow_html=True,
            )
            st.markdown(
                '''<div class="upload-checks">
                <span>● 여러 파일을 한 번에 업로드하면 자동으로 합산됩니다.</span>
                <span>● 파일을 드래그해서 놓아도 업로드할 수 있습니다.</span>
                <span>● 업로드한 파일은 현재 작업 중에만 임시 사용됩니다.</span>
                </div>''',
                unsafe_allow_html=True,
            )

    if data_files:
        fingerprint = file_fingerprint(data_files)
        if st.session_state.get('uploaded_fingerprint') != fingerprint:
            loaded = [load_excel_normalized(f.getvalue(), 21) for f in data_files]
            frames = [x[0] for x in loaded]
            headers = list(loaded[0][1])
            max_cols = max(frame.shape[1] for frame in frames)
            frames = [frame.reindex(columns=range(max_cols)) for frame in frames]
            if len(headers) < max_cols:
                headers += [f'열{i+1}' for i in range(len(headers), max_cols)]
            st.session_state.df = pd.concat(frames, ignore_index=True)
            st.session_state.original_headers = tuple(headers)
            st.session_state.uploaded_fingerprint = fingerprint

        df = st.session_state.df
        headers = st.session_state.original_headers

        def pre_col(key):
            found = find_source_col(headers, key)
            return FALLBACK_COLS.get(key) if found is None else found

        auto_region, auto_region_count = _detect_region_from_addresses(df, pre_col('address'))
    else:
        auto_region, auto_region_count = CHUNGNAM_REGIONS[0], 0

    with right:
        with st.container(border=True, key='filter_card'):
            st.markdown(
                '''<div class="filter-title-row"><div class="filter-icon">⌕</div>
                <div class="filter-title">검색 조건 <span>(선택)</span></div>
                <div class="filter-note">비워두면 전체 데이터를 대상으로 처리합니다.</div></div>''',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="field-title">기준 지역 <span class="field-info">i</span></div>', unsafe_allow_html=True)
            region_mode = st.radio(
                '기준 지역',
                ['자동 선택', '직접 선택'],
                horizontal=True,
                key='region_mode',
                help='자동 선택은 업로드 자료의 기존 주소에서 가장 많이 나타나는 지역을 기준으로 잡습니다.',
                label_visibility='collapsed',
            )
            if region_mode == '자동 선택':
                target_region = auto_region
                if data_files and auto_region_count:
                    st.markdown(
                        f'''<div class="auto-region-box"><span>현재 기준 지역</span><b>{target_region}</b>
                        <small>(예시: 주소가 가장 많은 지역) · 기존 주소 {auto_region_count:,}건 확인</small></div>''',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '''<div class="auto-region-box"><span>현재 기준 지역</span><b>파일 업로드 후 자동 선택</b>
                        <small>기존 주소에서 가장 많이 확인되는 지역을 기준으로 잡습니다.</small></div>''',
                        unsafe_allow_html=True,
                    )
            else:
                current = st.session_state.get('manual_target_region', CHUNGNAM_REGIONS[0])
                target_region = st.selectbox(
                    '지역 직접 선택',
                    CHUNGNAM_REGIONS,
                    index=CHUNGNAM_REGIONS.index(current) if current in CHUNGNAM_REGIONS else 0,
                    key='manual_target_region',
                    label_visibility='collapsed',
                )

            st.markdown('<div class="filter-divider"></div>', unsafe_allow_html=True)
            st.markdown('<div class="field-title">집계 기준 금액 <span>(원 이상)</span> <span class="field-info">i</span></div>', unsafe_allow_html=True)

            q1, q2, q3, q4, q5 = st.columns([0.75, 0.85, 0.85, 0.9, 1.42], gap='small')
            quick_specs = [
                (q1, '0원', 0),
                (q2, '10만원', 100000),
                (q3, '50만원', 500000),
                (q4, '100만원', 1000000),
            ]
            for col, label, value in quick_specs:
                col.button(
                    label,
                    key=f'quick_amount_{value}',
                    on_click=_set_amount,
                    args=(value,),
                    width='stretch',
                    type='primary' if int(st.session_state.amount_number) == value else 'secondary',
                )
            with q5:
                st.markdown('<div class="direct-input-label">직접 입력</div>', unsafe_allow_html=True)
                st.number_input(
                    '직접 입력',
                    min_value=0,
                    step=10000,
                    key='amount_number',
                    on_change=_sync_amount_from_number,
                    format='%d',
                    label_visibility='collapsed',
                    help='원하는 집계 기준 금액을 직접 입력할 수 있습니다.',
                )

            st.slider(
                '금액 슬라이더',
                min_value=0,
                max_value=AMOUNT_SLIDER_MAX,
                step=100000,
                key='amount_slider',
                on_change=_sync_amount_from_slider,
                label_visibility='collapsed',
            )
            target_amount = int(st.session_state.amount_number or 0)
            st.markdown(
                f'<div class="slider-caption"><span>0원</span><b>{target_amount:,}원 이상</b><span>{AMOUNT_SLIDER_MAX:,}원+</span></div>',
                unsafe_allow_html=True,
            )

    if not data_files:
        st.stop()

    df = st.session_state.df
    headers = st.session_state.original_headers

    def col(key):
        found = find_source_col(headers, key)
        return FALLBACK_COLS.get(key) if found is None else found

    col_amount, col_biz, col_addr, col_company, col_type = (col(k) for k in ['amount', 'biz', 'address', 'company', 'type'])
    amounts = pd.to_numeric(df.iloc[:, col_amount], errors='coerce').fillna(0)
    contract_types = df.iloc[:, col_type].apply(normalize_contract_type)
    recognized = contract_types.isin(['공사', '용역', '물품'])
    report_mask = (amounts >= target_amount) & recognized
    biz_norm = df.iloc[:, col_biz].apply(normalize_biz_no)
    valid_biz = biz_norm.str.len().eq(10)
    missing = report_mask & missing_address_mask(df.iloc[:, col_addr])
    missing_indices = df.index[missing]
    api_missing_indices = df.index[missing & valid_biz]
    report_count = int(report_mask.sum())
    missing_count = int(missing.sum())
    completion = 0 if report_count == 0 else round((report_count - missing_count) / report_count * 100, 1)

    return locals()

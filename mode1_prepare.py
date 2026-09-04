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
    """이미 들어 있는 주소 중 가장 많이 등장하는 충남 시·군을 1차 기준 지역으로 잡습니다."""
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

    st.markdown('<div class="section-title compact-title">▣ 자료 입력</div>', unsafe_allow_html=True)
    with st.container(border=True, key='data_input_panel'):
        left, right = st.columns([2.25, 1.05], gap='large')

        with left:
            st.markdown(
                '''<div class="upload-panel-title">자료 입력</div>
                <div class="upload-panel-desc">계약자료 Excel 파일을 업로드하세요. 여러 파일을 한 번에 선택할 수 있습니다.</div>''',
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
                '''<div class="upload-hint">↥ <b>파일을 클릭하여 선택하거나 이 영역으로 드래그해서 놓으세요.</b><br>
                <span>여러 파일은 자동으로 합산됩니다.</span></div>''',
                unsafe_allow_html=True,
            )
            st.markdown(
                '''<div class="source-path-guide"><b>파일 내려받기 경로</b><br>
                학교(재무)회계 → 계약관리 → 계약자료관리 → 자료관리</div>''',
                unsafe_allow_html=True,
            )

        # 업로드 파일을 먼저 읽어 자동 기준 지역을 계산합니다.
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
            st.markdown(
                '''<div class="filter-panel-title">⌕&nbsp; 검색 조건 <span>(선택)</span></div>''',
                unsafe_allow_html=True,
            )
            region_mode = st.radio(
                '기준 지역',
                ['자동 선택', '직접 선택'],
                horizontal=True,
                key='region_mode',
                help='자동 선택은 업로드 자료의 기존 주소에서 가장 많이 나타나는 지역을 기준으로 잡습니다.',
            )
            if region_mode == '자동 선택':
                target_region = auto_region
                if data_files and auto_region_count:
                    st.markdown(
                        f'''<div class="auto-region-box"><span>현재 기준 지역</span><b>{target_region}</b><small>기존 주소에서 가장 많이 확인된 지역 · {auto_region_count:,}건</small></div>''',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'''<div class="auto-region-box"><span>현재 기준 지역</span><b>{target_region}</b><small>파일 업로드 후 기존 주소를 기준으로 자동 선택됩니다.</small></div>''',
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
            st.markdown('<div class="amount-label">집계 기준 금액 <span>(원 이상)</span></div>', unsafe_allow_html=True)

            q1, q2, q3, q4 = st.columns(4, gap='small')
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

            st.slider(
                '금액 슬라이더',
                min_value=0,
                max_value=AMOUNT_SLIDER_MAX,
                step=100000,
                key='amount_slider',
                on_change=_sync_amount_from_slider,
                label_visibility='collapsed',
            )
            st.number_input(
                '직접 입력',
                min_value=0,
                step=10000,
                key='amount_number',
                on_change=_sync_amount_from_number,
                format='%d',
                help='버튼이나 슬라이더 외에 원하는 금액을 직접 입력할 수 있습니다.',
            )
            target_amount = int(st.session_state.amount_number or 0)
            st.caption(f'현재 집계 기준 · {target_amount:,}원 이상')

    if not data_files:
        st.markdown(
            '''<div class="empty-card compact-empty"><div class="empty-icon">▤</div>
            <div class="work-title">자료관리목록을 업로드해 주세요</div>
            <div class="work-desc">파일은 클릭하여 선택하거나 업로드 영역으로 드래그해서 놓을 수 있습니다.<br>
            <span style="color:#475467;font-weight:650">학교(재무)회계 → 계약관리 → 계약자료관리 → 자료관리</span>에서 내려받으시면 됩니다.</div></div>''',
            unsafe_allow_html=True,
        )
        st.stop()

    if data_files:
        st.caption(f'선택된 파일 {len(data_files)}개 · 여러 파일은 자동 합산됩니다.')

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

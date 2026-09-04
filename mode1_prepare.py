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
from ui_components import filter_controls_component


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
    return max(counts.items(), key=lambda item: item[1])


def _component_value(result, name, default):
    try:
        value = getattr(result, name)
        return default if value is None else value
    except Exception:
        return default


def prepare_mode1():
    report_year = 2026
    report_label = '상반기'
    period_start = date(2026, 1, 1)
    period_end = date(2026, 7, 31)

    st.session_state.setdefault('amount_number', int(DEFAULT_TARGET_AMOUNT))
    st.session_state.setdefault('region_mode', '자동 선택')
    st.session_state.setdefault('manual_target_region', CHUNGNAM_REGIONS[0])

    left, right = st.columns([1.62, 1], gap='medium')

    with left:
        with st.container(border=True, key='upload_card'):
            st.markdown(
                '''<div class="panel-head"><div class="panel-icon blue-icon">▤</div><div>
                <div class="panel-title">자료 입력</div>
                <div class="panel-desc">계약자료 Excel 파일을 업로드하세요. <b>(여러 파일 가능)</b></div></div></div>''',
                unsafe_allow_html=True,
            )
            data_files = st.file_uploader(
                '자료관리목록 Excel',
                type=['xlsx', 'xls'],
                accept_multiple_files=True,
                key='source_files',
                label_visibility='collapsed',
            )
            if not data_files:
                st.markdown(
                    '''<div class="drop-guide"><div class="drop-cloud">☁</div>
                    <b>여기에 파일을 드래그하거나 클릭하여 업로드하세요</b>
                    <span>Excel 파일(.xlsx, .xls)을 여러 개 선택할 수 있습니다.</span></div>''',
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
                <span>● 업로드한 파일은 현재 작업 중에만 임시 사용됩니다.</span></div>''',
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

    current_mode = 'auto' if st.session_state.get('region_mode') != '직접 선택' else 'manual'
    current_manual = st.session_state.get('manual_target_region', CHUNGNAM_REGIONS[0])
    current_amount = int(st.session_state.get('amount_number', DEFAULT_TARGET_AMOUNT) or 0)

    with right:
        filter_result = filter_controls_component(
            data={
                'regions': list(CHUNGNAM_REGIONS),
                'auto_region': auto_region if data_files else '파일 업로드 후 자동 선택',
                'auto_count': int(auto_region_count),
                'region_mode': current_mode,
                'manual_region': current_manual,
                'amount': current_amount,
            },
            default={
                'region_mode': current_mode,
                'manual_region': current_manual,
                'amount': current_amount,
            },
            key='mode1_filter_controls_v2',
            on_region_mode_change=lambda: None,
            on_manual_region_change=lambda: None,
            on_amount_change=lambda: None,
            width='stretch',
        )

    component_mode = str(_component_value(filter_result, 'region_mode', current_mode))
    component_manual = str(_component_value(filter_result, 'manual_region', current_manual))
    component_amount = int(_component_value(filter_result, 'amount', current_amount) or 0)

    st.session_state.region_mode = '직접 선택' if component_mode == 'manual' else '자동 선택'
    if component_manual in CHUNGNAM_REGIONS:
        st.session_state.manual_target_region = component_manual
    st.session_state.amount_number = max(0, component_amount)

    target_region = (
        st.session_state.manual_target_region
        if st.session_state.region_mode == '직접 선택'
        else auto_region
    )
    target_amount = int(st.session_state.amount_number)

    if not data_files:
        st.stop()

    df = st.session_state.df
    headers = st.session_state.original_headers

    def col(key):
        found = find_source_col(headers, key)
        return FALLBACK_COLS.get(key) if found is None else found

    col_amount, col_biz, col_addr, col_company, col_type = (
        col(k) for k in ['amount', 'biz', 'address', 'company', 'type']
    )
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

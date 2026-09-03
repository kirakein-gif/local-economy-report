from datetime import date
import pandas as pd
import streamlit as st
from core_logic import (
    CHUNGNAM_REGIONS, DEFAULT_TARGET_AMOUNT, FALLBACK_COLS,
    file_fingerprint, find_source_col, load_excel_normalized,
    missing_address_mask, normalize_biz_no, normalize_contract_type,
)


def prepare_mode1():
    with st.sidebar:
        st.markdown('<div class="side-section">집계 기준</div>', unsafe_allow_html=True)
        target_region = st.selectbox('기준 지역', CHUNGNAM_REGIONS, index=0, key='target_region')
        raw_amount = st.text_input('금액 기준(원 이상)', value=f'{DEFAULT_TARGET_AMOUNT:,}', key='amount_raw')
        cleaned = raw_amount.replace(',', '').replace(' ', '').strip()
        if cleaned == '':
            target_amount = 0
        elif cleaned.isdigit():
            target_amount = int(cleaned)
        else:
            target_amount = DEFAULT_TARGET_AMOUNT
            st.warning(f'숫자만 입력해 주세요. {DEFAULT_TARGET_AMOUNT:,}원을 사용합니다.')
        st.caption('자료 집계에서는 기준 지역과 금액만 설정합니다.')

    report_year = 2026
    report_label = '상반기'
    period_start = date(2026, 1, 1)
    period_end = date(2026, 7, 31)

    st.markdown('<div class="section-title compact-title">▣ 자료 입력</div>', unsafe_allow_html=True)
    with st.container(border=True):
        left, right = st.columns([2.5, 1], gap='medium')
        with left:
            data_files = st.file_uploader(
                '자료관리목록 Excel',
                type=['xlsx', 'xls'],
                accept_multiple_files=True,
                key='source_files',
                label_visibility='collapsed',
            )
        with right:
            st.markdown(
                f'''<div class="mini-info"><span class="mini-label">기준 지역</span><b>{target_region}</b><br><span class="mini-label">집계 기준</span><b>{target_amount:,}원 이상</b></div>''',
                unsafe_allow_html=True,
            )
        if data_files:
            st.caption(f'선택된 파일 {len(data_files)}개 · 여러 파일은 자동 합산됩니다.')

    if not data_files:
        st.markdown('''<div class="empty-card compact-empty"><div class="empty-icon">▤</div><div class="work-title">자료관리목록을 업로드해 주세요</div><div class="work-desc">왼쪽에서 기준 지역과 금액을 설정한 뒤 Excel 파일을 선택하세요.<br><span style="color:#475467;font-weight:650">학교(재무)회계 → 계약관리 → 계약자료관리 → 자료관리</span>에서 내려받으시면 됩니다.</div></div>''', unsafe_allow_html=True)
        st.stop()

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

    st.markdown(
        f'''<div class="kpi-row compact-kpi"><div class="kpi-card"><div class="kpi-label">전체 계약자료</div><div class="kpi-value">{int(recognized.sum()):,}<span class="kpi-unit">건</span></div></div><div class="kpi-card"><div class="kpi-label">집계 대상</div><div class="kpi-value">{report_count:,}<span class="kpi-unit">건</span></div><div class="kpi-note">{target_amount:,}원 이상</div></div><div class="kpi-card"><div class="kpi-label">주소 완료율</div><div class="kpi-value">{completion}<span class="kpi-unit">%</span></div><div class="kpi-note">미확인 {missing_count}건</div></div></div>''',
        unsafe_allow_html=True,
    )

    return locals()

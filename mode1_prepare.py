from datetime import date
import pandas as pd
import streamlit as st
from core_logic import (
    CHUNGNAM_REGIONS, DEFAULT_TARGET_AMOUNT, FALLBACK_COLS, SCHOOL_LEVELS,
    file_fingerprint, find_source_col, load_excel_normalized,
    missing_address_mask, normalize_biz_no, normalize_contract_type,
)


def prepare_mode1():
    st.markdown('<div class="section-title">자료 입력 및 처리 설정</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap='medium')

    with c1:
        with st.container(border=True):
            st.markdown('<div class="card-icon">📄</div><div class="card-title">자료 입력</div><div class="card-desc">자료관리목록 Excel 파일을 업로드하세요. 여러 파일은 자동으로 합산합니다.</div>', unsafe_allow_html=True)
            data_files = st.file_uploader('자료관리목록 Excel', type=['xlsx', 'xls'], accept_multiple_files=True, key='source_files', label_visibility='collapsed')
            if data_files:
                st.caption(f'선택된 파일 {len(data_files)}개')

    with c2:
        with st.container(border=True):
            st.markdown('<div class="card-icon">⚙️</div><div class="card-title">옵션 설정</div><div class="card-desc">기준 지역과 집계 금액을 설정합니다.</div>', unsafe_allow_html=True)
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

    with c3:
        with st.container(border=True):
            st.markdown('<div class="card-icon green">▶</div><div class="card-title">자동 처리</div><div class="card-desc">업로드 후 주소를 보완하고 분기보고서와 반기 검토파일을 생성합니다.</div>', unsafe_allow_html=True)
            institution_name = st.text_input('기관명', value='천안버들유치원', key='institution_name')
            school_level = st.selectbox('급별', SCHOOL_LEVELS, index=0, key='school_level')
            if data_files:
                st.success('자료가 준비되었습니다. 아래 주소 보완 단계로 진행하세요.')
            else:
                st.info('Excel 파일을 선택하면 처리를 시작할 수 있습니다.')

    with st.sidebar:
        st.markdown('<div class="side-section">반기 검토파일 설정</div>', unsafe_allow_html=True)
        report_year = int(st.number_input('보고연도', min_value=2020, max_value=2100, value=2026, step=1))
        report_label = st.text_input('보고구분', value='상반기')
        period_start = st.date_input('기간 시작', value=date(2026, 1, 1))
        period_end = st.date_input('기간 종료', value=date(2026, 7, 31))
        st.markdown('<div class="side-help">반기 검토용 1-4 기초자료의 제목과 기간에 반영됩니다.</div>', unsafe_allow_html=True)

    if not data_files:
        st.markdown('''<div class="empty-card"><div class="empty-icon">📂</div><div class="work-title">자료관리목록을 업로드해 주세요</div><div class="work-desc">위의 ‘자료 입력’ 카드에서 Excel 파일을 선택하면 자동으로 자료를 분석합니다.</div></div>''', unsafe_allow_html=True)
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

    st.markdown('<div class="section-title">처리 현황</div>', unsafe_allow_html=True)
    st.markdown(
        f'''<div class="kpi-row"><div class="kpi-card"><div class="kpi-label">전체 계약자료</div><div class="kpi-value">{int(recognized.sum()):,}<span class="kpi-unit">건</span></div><div class="kpi-note">공사 · 용역 · 물품 인식 건수</div></div><div class="kpi-card"><div class="kpi-label">집계 대상</div><div class="kpi-value">{report_count:,}<span class="kpi-unit">건</span></div><div class="kpi-note">{target_amount:,}원 이상</div></div><div class="kpi-card"><div class="kpi-label">주소 완료율</div><div class="kpi-value">{completion}<span class="kpi-unit">%</span></div><div class="kpi-note">미확인 {missing_count}건 · 미확인은 타시도 임시분류</div></div></div>''',
        unsafe_allow_html=True,
    )

    return locals()

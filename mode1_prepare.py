from datetime import date
import pandas as pd
import streamlit as st
from core_logic import (
    CHUNGNAM_REGIONS, DEFAULT_TARGET_AMOUNT, FALLBACK_COLS, SCHOOL_LEVELS,
    file_fingerprint, find_source_col, load_excel_normalized,
    missing_address_mask, normalize_biz_no, normalize_contract_type, release_slot,
)


def prepare_mode1():
    st.markdown('''
    <div class="flow">
      <div class="flow-step active"><div class="flow-no">STEP 1</div><div class="flow-title">자료 업로드</div><div class="flow-desc">자료관리목록 여러 파일 합산</div></div>
      <div class="flow-step active"><div class="flow-no">STEP 2</div><div class="flow-title">주소 보완</div><div class="flow-desc">기존자료 → 조달청 → 수동확인</div></div>
      <div class="flow-step"><div class="flow-no">STEP 3</div><div class="flow-title">분기보고서</div><div class="flow-desc">현재 사용 중인 서식 그대로 산출</div></div>
      <div class="flow-step"><div class="flow-no">STEP 4</div><div class="flow-title">반기 검토파일</div><div class="flow-desc">공식 1-4 기초자료 형식으로 내려받기</div></div>
    </div>''', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="side-section">1. 자료 업로드</div>', unsafe_allow_html=True)
        target_region = st.selectbox('기준 지역', CHUNGNAM_REGIONS, index=0, key='target_region')
        institution_name = st.text_input('기관명(학교명)', value='천안버들유치원', key='institution_name')
        school_level = st.selectbox('급별', SCHOOL_LEVELS, index=0, key='school_level')
        data_files = st.file_uploader('자료관리목록 엑셀', type=['xlsx', 'xls'], accept_multiple_files=True, key='source_files')
        st.markdown('<div class="side-help">학교회계 → 계약관리 → 계약자료관리 → 자료관리에서 내려받은 파일을 여러 개 함께 올릴 수 있습니다.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown('<div class="side-section">2. 집계 기준</div>', unsafe_allow_html=True)
        raw_amount = st.text_input('금액 기준(원 이상)', value=f'{DEFAULT_TARGET_AMOUNT:,}', key='amount_raw')
        cleaned = raw_amount.replace(',', '').replace(' ', '').strip()
        if cleaned == '':
            target_amount = 0
        elif cleaned.isdigit():
            target_amount = int(cleaned)
        else:
            target_amount = DEFAULT_TARGET_AMOUNT
            st.warning(f'숫자만 입력해 주세요. {DEFAULT_TARGET_AMOUNT:,}원을 사용합니다.')
        with st.expander('반기 검토파일 설정', expanded=False):
            report_year = int(st.number_input('보고연도', min_value=2020, max_value=2100, value=2026, step=1))
            report_label = st.text_input('보고구분', value='상반기')
            period_start = st.date_input('기간 시작', value=date(2026, 1, 1))
            period_end = st.date_input('기간 종료', value=date(2026, 7, 31))
        st.divider()
        if st.button('🚪 나가기 (자리 반납)', width='stretch'):
            release_slot(); st.success('자리를 반납했습니다. 페이지를 닫으셔도 됩니다.'); st.stop()

    if not data_files:
        st.markdown('''<div class="work-card" style="text-align:center;padding:44px 20px;"><div style="font-size:1.6rem;margin-bottom:8px;">📂</div><div class="work-title">자료관리목록을 업로드해 주세요</div><div class="work-desc">왼쪽에서 기준 지역과 기관 정보를 확인한 뒤 Excel 파일을 선택하면 자동 집계가 시작됩니다.</div></div>''', unsafe_allow_html=True)
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
    col_amount, col_biz, col_addr, col_company, col_type = (col(k) for k in ['amount','biz','address','company','type'])
    amounts = pd.to_numeric(df.iloc[:, col_amount], errors='coerce').fillna(0)
    contract_types = df.iloc[:, col_type].apply(normalize_contract_type)
    recognized = contract_types.isin(['공사','용역','물품'])
    report_mask = (amounts >= target_amount) & recognized
    biz_norm = df.iloc[:, col_biz].apply(normalize_biz_no)
    valid_biz = biz_norm.str.len().eq(10)
    missing = report_mask & missing_address_mask(df.iloc[:, col_addr])
    missing_indices = df.index[missing]
    api_missing_indices = df.index[missing & valid_biz]
    report_count = int(report_mask.sum())
    missing_count = int(missing.sum())
    completion = 0 if report_count == 0 else round((report_count-missing_count)/report_count*100, 1)

    st.markdown(f'''<div class="kpi-row"><div class="kpi-card"><div class="kpi-label">계약자료</div><div class="kpi-value">{int(recognized.sum()):,}<span class="kpi-unit">건</span></div><div class="kpi-note">공사 · 용역 · 물품 인식 건수</div></div><div class="kpi-card"><div class="kpi-label">집계 대상</div><div class="kpi-value">{report_count:,}<span class="kpi-unit">건</span></div><div class="kpi-note">{target_amount:,}원 이상</div></div><div class="kpi-card"><div class="kpi-label">주소 완료율</div><div class="kpi-value">{completion}<span class="kpi-unit">%</span></div><div class="kpi-note">미확인 {missing_count}건 · 미확인은 타시도 임시분류</div></div></div>''', unsafe_allow_html=True)

    return locals()

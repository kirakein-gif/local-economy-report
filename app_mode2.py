import streamlit as st
from core_logic import release_slot
from excel_reports import build_final_halfyear_report_bytes


def render_mode2():
    st.markdown('''
    <div class="flow">
      <div class="flow-step"><div class="flow-no">STEP 1</div><div class="flow-title">1차 자동처리</div><div class="flow-desc">주소·지역·구입목적 초깃값 생성</div></div>
      <div class="flow-step"><div class="flow-no">STEP 2</div><div class="flow-title">Excel 사용자 검토</div><div class="flow-desc">계약방법·견적방법·구입목적 등 수정</div></div>
      <div class="flow-step active"><div class="flow-no">STEP 3</div><div class="flow-title">검토파일 재업로드</div><div class="flow-desc">공식 1-4 기초자료를 다시 불러오기</div></div>
      <div class="flow-step active"><div class="flow-no">STEP 4</div><div class="flow-title">최종 4시트 출력</div><div class="flow-desc">공사·용역·물품 총괄 자동 집계</div></div>
    </div>''', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('<div class="side-section">검토 완료 파일</div>', unsafe_allow_html=True)
        review_upload = st.file_uploader('1-4 기초자료 Excel 업로드', type=['xlsx'], accept_multiple_files=False, key='review_upload')
        st.markdown('<div class="side-help">1차에서 내려받은 검토용 파일의 계약방법·견적/경쟁방법·구입목적·비고 등을 확인한 뒤 다시 올려주세요. 이 단계에서는 사용자의 수정값을 최종값으로 사용합니다.</div>', unsafe_allow_html=True)
        st.divider()
        if st.button('🚪 나가기 (자리 반납)', width='stretch'):
            release_slot(); st.success('자리를 반납했습니다. 페이지를 닫으셔도 됩니다.'); st.stop()
    if not review_upload:
        st.markdown('''<div class="work-card" style="text-align:center;padding:44px 20px;"><div style="font-size:1.6rem;margin-bottom:8px;">📝</div><div class="work-title">검토 완료한 1-4 기초자료 파일을 올려주세요</div><div class="work-desc">자동분류를 다시 덮어쓰지 않습니다. 사용자가 Excel에서 수정한 값을 기준으로 1-1 공사 · 1-2 용역 · 1-3 물품을 집계합니다.</div></div>''', unsafe_allow_html=True)
        st.stop()
    try:
        final_bytes, records, meta, aggregation = build_final_halfyear_report_bytes(review_upload.getvalue())
        base, edu, book = aggregation
        total=len(records); works=sum(base['공사',loc][0] for loc in [1,2,3]); services=sum(base['용역',loc][0] for loc in [1,2,3]); goods=sum(base['물품',loc][0] for loc in [1,2,3])
        edu_count=sum(edu[loc][0] for loc in [1,2,3]); book_count=sum(book[loc][0] for loc in [1,2,3])
        st.markdown(f'''<div class="kpi-row"><div class="kpi-card"><div class="kpi-label">기초자료</div><div class="kpi-value">{total:,}<span class="kpi-unit">건</span></div><div class="kpi-note">검토 완료 파일 기준</div></div><div class="kpi-card"><div class="kpi-label">목적물 구성</div><div class="kpi-value" style="font-size:1.05rem">공사 {works} · 용역 {services} · 물품 {goods}</div><div class="kpi-note">1-1~1-3 자동 집계</div></div><div class="kpi-card"><div class="kpi-label">물품 구입목적</div><div class="kpi-value" style="font-size:1.05rem">교육용 {edu_count} · 도서 {book_count}</div><div class="kpi-note">나머지는 그 외</div></div></div>''', unsafe_allow_html=True)
        notes=[]
        if meta['blank_purpose']: notes.append(f"구입목적 미입력 {meta['blank_purpose']}건은 '그 외'로 보수 처리")
        if meta['invalid_purpose']: notes.append(f"정의되지 않은 구입목적 {meta['invalid_purpose']}건은 '그 외'로 처리")
        if meta['corrected_location']: notes.append(f"소재지 미입력/오류 {meta['corrected_location']}건은 주소 기준으로 보정")
        if notes:
            st.markdown('<span class="status warn">⚠ 자동 보정 사항 있음</span>', unsafe_allow_html=True); st.caption(' · '.join(notes))
        else:
            st.markdown('<span class="status ok">✓ 검토파일 구조 및 분류값 확인 완료</span>', unsafe_allow_html=True)
        st.markdown('''<div class="work-card" style="margin-top:14px;"><div class="work-title">최종 제출파일 준비 완료</div><div class="work-desc">검토한 1-4 기초자료 값을 기준으로 공식 양식의 1-1 공사 · 1-2 용역 · 1-3 물품 총괄을 산출하고, 1-4 기초자료와 함께 하나의 Excel 파일로 묶었습니다.</div></div>''', unsafe_allow_html=True)
        with st.sidebar:
            st.divider(); st.markdown('<div class="side-section">최종 출력</div>', unsafe_allow_html=True)
            st.download_button('📊 최종 반기보고서 4시트', final_bytes, '지역경제활성화_최종_반기보고서.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', width='stretch')
            st.caption('1-1 공사 · 1-2 용역 · 1-3 물품 · 1-4 기초자료')
    except Exception as exc:
        st.error(f'검토파일을 처리하지 못했습니다: {exc}')

import streamlit as st
from core_logic import release_slot
import excel_reports as reports
from template_fallback import build_fallback_workbook

# 최종 반기보고서도 손상될 수 있는 저장소 xlsx를 열지 않고 내장 템플릿을 사용합니다.
reports._load_halfyear_template = build_fallback_workbook


def render_mode2():
    st.markdown('''<div class="mode-banner"><div><div class="mode-eyebrow">반기보고서 최종작성</div><div class="mode-title">검토한 1-4 기초자료를 다시 업로드하세요</div><div class="mode-desc">사용자가 Excel에서 수정한 계약방법·견적/경쟁방법·구입목적·비고를 최종값으로 사용해 4개 시트를 생성합니다.</div></div></div>''', unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85], gap='large')
    with left:
        st.markdown('<div class="card-title">검토파일 업로드</div><div class="card-desc">1차 업무에서 내려받은 검토용 기초자료(.xlsx)를 선택하세요.</div>', unsafe_allow_html=True)
        review_upload = st.file_uploader('검토 완료 1-4 기초자료', type=['xlsx'], accept_multiple_files=False, key='review_upload')
    with right:
        st.markdown('''<div class="info-panel"><div class="info-icon">✓</div><div><div class="work-title">사용자 수정값 우선</div><div class="work-desc">2차 단계에서는 자동분류를 다시 덮어쓰지 않습니다. 빈 구입목적만 ‘그 외’로 보수 처리합니다.</div></div></div>''', unsafe_allow_html=True)

    with st.sidebar:
        if st.button('나가기 · 자리 반납', width='stretch'):
            release_slot(); st.success('자리를 반납했습니다. 페이지를 닫으셔도 됩니다.'); st.stop()

    if not review_upload:
        st.markdown('''<div class="empty-card"><div class="empty-icon">📝</div><div class="work-title">검토 완료 파일을 기다리고 있습니다</div><div class="work-desc">파일을 업로드하면 공사·용역·물품과 교육용·도서를 다시 집계하고 최종 4시트 제출파일을 만듭니다.</div></div>''', unsafe_allow_html=True)
        return

    try:
        final_bytes, records, meta, aggregation = reports.build_final_halfyear_report_bytes(review_upload.getvalue())
        base, edu, book = aggregation
        total = len(records)
        works = sum(base['공사', loc][0] for loc in [1, 2, 3])
        services = sum(base['용역', loc][0] for loc in [1, 2, 3])
        goods = sum(base['물품', loc][0] for loc in [1, 2, 3])
        edu_count = sum(edu[loc][0] for loc in [1, 2, 3])
        book_count = sum(book[loc][0] for loc in [1, 2, 3])

        st.markdown(
            f'''<div class="kpi-row"><div class="kpi-card"><div class="kpi-label">기초자료</div><div class="kpi-value">{total:,}<span class="kpi-unit">건</span></div><div class="kpi-note">검토 완료 파일 기준</div></div><div class="kpi-card"><div class="kpi-label">목적물 구성</div><div class="kpi-value small-value">공사 {works} · 용역 {services} · 물품 {goods}</div><div class="kpi-note">1-1~1-3 자동 집계</div></div><div class="kpi-card"><div class="kpi-label">물품 구입목적</div><div class="kpi-value small-value">교육용 {edu_count} · 도서 {book_count}</div><div class="kpi-note">나머지는 그 외</div></div></div>''',
            unsafe_allow_html=True,
        )

        notes = []
        if meta['blank_purpose']:
            notes.append(f"구입목적 미입력 {meta['blank_purpose']}건은 '그 외'로 보수 처리")
        if meta['invalid_purpose']:
            notes.append(f"정의되지 않은 구입목적 {meta['invalid_purpose']}건은 '그 외'로 처리")
        if meta['corrected_location']:
            notes.append(f"소재지 미입력/오류 {meta['corrected_location']}건은 주소 기준으로 보정")
        if notes:
            st.warning(' · '.join(notes))
        else:
            st.success('검토파일 구조와 분류값을 정상적으로 확인했습니다.')

        st.markdown('''<div class="download-card final-card"><div class="download-icon">📊</div><div><div class="work-title">최종 제출파일 준비 완료</div><div class="work-desc">1-1 공사 · 1-2 용역 · 1-3 물품 · 1-4 기초자료를 하나의 Excel 파일로 생성했습니다.</div></div></div>''', unsafe_allow_html=True)
        st.download_button(
            '최종 반기보고서 4시트 다운로드',
            final_bytes,
            '지역경제활성화_최종_반기보고서.xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            width='stretch',
        )
    except Exception as exc:
        st.error(f'검토파일을 처리하지 못했습니다: {exc}')

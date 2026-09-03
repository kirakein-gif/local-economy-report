import re
from datetime import date

import streamlit as st
import excel_reports as reports
from template_fallback import load_halfyear_template_safe

# 최종보고서 생성도 템플릿이 손상되면 자동 복구합니다.
reports._load_halfyear_template = lambda: load_halfyear_template_safe(reports.HALFYEAR_TEMPLATE)


def _detect_year_half(title):
    m = re.search(r'(\d{4})년\s*(상반기|하반기|반기)', title or '')
    if not m:
        return '', ''
    return m.group(1), ('상' if m.group(2).startswith('상') else ('하' if m.group(2).startswith('하') else '반기'))


def _safe_filename_text(value):
    text = str(value or '').strip()
    for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        text = text.replace(ch, '_')
    return text or '기관명미입력'


def render_mode2():
    with st.sidebar:
        st.markdown('<div class="side-section side-gap">반기보고서 설정</div>', unsafe_allow_html=True)
        report_year = int(st.number_input('보고연도', min_value=2020, max_value=2100, value=2026, step=1, key='final_report_year'))
        report_label = st.selectbox('보고구분', ['상반기', '하반기'], key='final_report_label')
        if report_label == '상반기':
            default_start, default_end = date(report_year, 1, 1), date(report_year, 7, 31)
        else:
            default_start, default_end = date(report_year, 8, 1), date(report_year, 12, 31)
        st.date_input('기간 시작', value=default_start, key='final_period_start')
        st.date_input('기간 종료', value=default_end, key='final_period_end')
        st.caption('검토파일의 실제 값이 우선이며, 이 설정은 확인용입니다.')

    st.markdown('<div class="section-title compact-title">📤 검토 완료 파일 업로드</div>', unsafe_allow_html=True)
    with st.container(border=True):
        review_upload = st.file_uploader(
            '검토 완료 1-4 기초자료',
            type=['xlsx'],
            accept_multiple_files=False,
            key='review_upload',
            label_visibility='collapsed',
        )
        st.caption('1차에서 내려받아 검토·수정한 파일을 올려주세요. 사용자 수정값을 그대로 집계합니다.')

    if not review_upload:
        st.markdown('''<div class="empty-card compact-empty"><div class="empty-icon">📝</div><div class="work-title">검토 완료 파일을 기다리고 있습니다</div><div class="work-desc">업로드하면 공사 · 용역 · 물품 · 기초자료 4개 시트를 자동 작성합니다.</div></div>''', unsafe_allow_html=True)
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
        year, half = _detect_year_half(meta.get('title', ''))
        institution = _safe_filename_text(meta.get('institution', ''))
        final_name = f'지역경제활성화 실적 작성 양식({year}{half}_{institution}).xlsx' if year else f'지역경제활성화 실적 작성 양식({institution}).xlsx'

        with st.sidebar:
            st.markdown('<div class="side-section side-gap">검토파일 인식 정보</div>', unsafe_allow_html=True)
            st.caption(f'보고구분: {year}{half}' if year else '보고구분: 자동 인식 실패')
            st.caption(f'기관명: {meta.get("institution", "") or "미입력"}')
            st.caption(f'기준지역: {meta.get("region", "") or "미입력"}')

        st.markdown(
            f'''<div class="kpi-row compact-kpi"><div class="kpi-card"><div class="kpi-label">기초자료</div><div class="kpi-value">{total:,}<span class="kpi-unit">건</span></div></div><div class="kpi-card"><div class="kpi-label">목적물 구성</div><div class="kpi-value small-value">공사 {works} · 용역 {services} · 물품 {goods}</div></div><div class="kpi-card"><div class="kpi-label">물품 구입목적</div><div class="kpi-value small-value">교육용 {edu_count} · 도서 {book_count}</div></div></div>''',
            unsafe_allow_html=True,
        )

        notes = []
        if meta['blank_purpose']:
            notes.append(f"구입목적 미입력 {meta['blank_purpose']}건 → 그 외")
        if meta['invalid_purpose']:
            notes.append(f"정의되지 않은 구입목적 {meta['invalid_purpose']}건 → 그 외")
        if meta['corrected_location']:
            notes.append(f"소재지 보정 {meta['corrected_location']}건")
        if notes:
            st.warning(' · '.join(notes))
        else:
            st.success('검토파일 구조와 분류값을 정상적으로 확인했습니다.')

        st.download_button(
            '최종 반기보고서 다운로드',
            final_bytes,
            final_name,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            width='stretch',
        )
        st.caption(f'4시트 보고서 · 파일명: {final_name}')
    except Exception as exc:
        st.error(f'검토파일을 처리하지 못했습니다: {exc}')

import streamlit as st
from core_logic import categorize_region_code, format_money, safe_value
import excel_reports as reports
from template_fallback import load_halfyear_template_safe

# GitHub/배포 과정에서 xlsx 바이너리가 손상되더라도 내장 기본양식으로 자동 복구합니다.
reports._load_halfyear_template = lambda: load_halfyear_template_safe(reports.HALFYEAR_TEMPLATE)


def render_mode1_outputs(ctx):
    df = st.session_state.df
    report_mask = ctx['report_mask']
    contract_types = ctx['contract_types']
    col_addr = ctx['col_addr']
    col_amount = ctx['col_amount']
    target_region = ctx['target_region']

    results = {(t, loc): [0, 0] for t in ['공사', '용역', '물품'] for loc in [1, 2, 3]}
    for idx in df.index[report_mask]:
        row = df.loc[idx]
        ctype = contract_types.at[idx]
        loc = categorize_region_code(safe_value(row, col_addr, ''), target_region)
        amount = format_money(safe_value(row, col_amount, 0))
        results[ctype, loc][0] += 1
        results[ctype, loc][1] += amount

    total = sum(v[1] for v in results.values())
    if total:
        amounts = [sum(results[t, loc][1] for t in ['공사', '용역', '물품']) for loc in [1, 2, 3]]
        pct = [round(x / total * 100, 1) for x in amounts]
        st.markdown(
            f'''<div class="region-card"><div class="work-title">지역별 구매 금액 비중</div><div class="region-track"><div class="region-seg-1" style="width:{pct[0]}%"></div><div class="region-seg-2" style="width:{pct[1]}%"></div><div class="region-seg-3" style="width:{pct[2]}%"></div></div><div class="region-legend"><span>{target_region} {pct[0]}%</span><span>충남 관외 {pct[1]}%</span><span>타시도 {pct[2]}%</span></div></div>''',
            unsafe_allow_html=True,
        )

    st.markdown('''<div class="section-title">처리 결과 및 파일 다운로드</div>''', unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap='large')
    with col1:
        st.markdown('''<div class="download-card"><div class="download-icon">📄</div><div><div class="work-title">분기별 실적보고서</div><div class="work-desc">현재 사용 중인 분기 제출서식을 그대로 생성합니다.</div></div></div>''', unsafe_allow_html=True)
        try:
            q = reports.build_quarter_report_bytes(results, target_region)
            st.download_button(
                '분기별 실적보고서 다운로드',
                q,
                f'지역경제활성화_실적보고({target_region}기준).xlsx',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                width='stretch',
            )
        except Exception as exc:
            st.error(f'분기보고서 생성 오류: {exc}')

    with col2:
        st.markdown('''<div class="download-card"><div class="download-icon">📝</div><div><div class="work-title">반기보고서 검토용 기초자료</div><div class="work-desc">공식 1-4 기초자료 형식으로 내려받아 계약방법·견적방법·구입목적 등을 검토합니다.</div></div></div>''', unsafe_allow_html=True)
        try:
            b, n, _ = reports.build_review_workbook_bytes(
                df,
                ctx['headers'],
                ctx['target_amount'],
                target_region,
                ctx['institution_name'].strip(),
                ctx['school_level'],
                ctx['report_year'],
                ctx['report_label'].strip() or '반기',
                ctx['period_start'],
                ctx['period_end'],
            )
            st.download_button(
                '반기 검토용 기초자료 다운로드',
                b,
                f'지역경제활성화_{ctx["report_year"]}{ctx["report_label"]}_검토용기초자료.xlsx',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                width='stretch',
            )
            st.caption(f'1-4 기초자료 형식 · {n:,}건 · Excel에서 최종 검토 후 2차 업무에 다시 업로드')
        except Exception as exc:
            st.error(f'검토용 파일 생성 오류: {exc}')

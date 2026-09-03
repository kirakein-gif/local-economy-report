from io import BytesIO
import pandas as pd
import streamlit as st
from core_logic import categorize_region_code, display_headers, format_money, safe_value
from excel_reports import build_quarter_report_bytes, build_review_workbook_bytes


def render_mode1_outputs(ctx):
    df=st.session_state.df; report_mask=ctx['report_mask']; contract_types=ctx['contract_types']; col_addr=ctx['col_addr']; col_amount=ctx['col_amount']; target_region=ctx['target_region']
    results={(t,loc):[0,0] for t in ['공사','용역','물품'] for loc in [1,2,3]}
    for idx in df.index[report_mask]:
        row=df.loc[idx]; ctype=contract_types.at[idx]; loc=categorize_region_code(safe_value(row,col_addr,''),target_region); amount=format_money(safe_value(row,col_amount,0))
        results[ctype,loc][0]+=1; results[ctype,loc][1]+=amount
    total=sum(v[1] for v in results.values())
    if total:
        amounts=[sum(results[t,loc][1] for t in ['공사','용역','물품']) for loc in [1,2,3]]; pct=[round(x/total*100,1) for x in amounts]
        st.markdown(f'''<div class="region-card"><div class="work-title">지역별 구매 금액 비중</div><div class="region-track"><div class="region-seg-1" style="width:{pct[0]}%"></div><div class="region-seg-2" style="width:{pct[1]}%"></div><div class="region-seg-3" style="width:{pct[2]}%"></div></div><div class="region-legend"><span>{target_region} {pct[0]}%</span><span>충남 관외 {pct[1]}%</span><span>타시도 {pct[2]}%</span></div></div>''',unsafe_allow_html=True)
    st.markdown('''<div class="work-card" style="margin-top:16px;"><div class="work-title">반기보고서는 ‘검토 후 최종집계’ 방식으로 처리합니다</div><div class="work-desc">1차에서 공식 <b>1-4 기초자료</b> 형식의 Excel을 내려받습니다. 계약방법·견적/경쟁방법·구입목적·비고 등 사람이 확인해야 하는 항목을 Excel에서 수정한 뒤, ‘반기보고서 최종작성’ 메뉴에 다시 업로드하면 1-1~1-4 네 시트를 자동 완성합니다.</div></div>''',unsafe_allow_html=True)
    with st.sidebar:
        st.divider(); st.markdown('<div class="side-section">4. 결과 다운로드</div>',unsafe_allow_html=True)
        raw=df.copy(); raw.columns=display_headers(ctx['headers'],df.shape[1]); buf=BytesIO()
        with pd.ExcelWriter(buf,engine='openpyxl') as writer: raw.to_excel(writer,index=False)
        st.download_button('1. 주소 완료 원본',buf.getvalue(),'주소완료_자료관리목록.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch')
        try:
            q=build_quarter_report_bytes(results,target_region)
            st.download_button('2. 분기별 실적보고서',q,f'지역경제활성화_실적보고({target_region}기준).xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch')
        except Exception as exc: st.error(f'분기보고서 생성 오류: {exc}')
        try:
            b,n,_=build_review_workbook_bytes(df,ctx['headers'],ctx['target_amount'],target_region,ctx['institution_name'].strip(),ctx['school_level'],ctx['report_year'],ctx['report_label'].strip() or '반기',ctx['period_start'],ctx['period_end'])
            st.download_button('3. 반기보고서 검토용 기초자료',b,f'지역경제활성화_{ctx["report_year"]}{ctx["report_label"]}_검토용기초자료.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',width='stretch')
            st.caption(f'공식 1-4 기초자료 형식 · {n:,}건 · Excel에서 최종 검토')
        except Exception as exc: st.error(f'검토용 파일 생성 오류: {exc}')

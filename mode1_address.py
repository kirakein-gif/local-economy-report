import pandas as pd
import streamlit as st
from core_logic import get_addr_api, missing_address_mask, touch_slot


def render_address_tools(ctx):
    df=ctx['df']; col_addr=ctx['col_addr']; col_company=ctx['col_company']; biz_norm=ctx['biz_norm']
    missing_indices=ctx['missing_indices']; api_missing_indices=ctx['api_missing_indices']; missing_count=ctx['missing_count']
    with st.sidebar:
        st.divider(); st.markdown('<div class="side-section">3. 주소 보완</div>', unsafe_allow_html=True)
        if st.button('① 파일 내 주소 자체 채우기', width='stretch'):
            addr_series=df.iloc[:,col_addr].replace(r'^\s*$',pd.NA,regex=True)
            known_df=pd.DataFrame({'biz':biz_norm,'addr':addr_series})
            known=known_df.dropna(subset=['addr']).loc[lambda x:x['biz'].str.len().eq(10)].drop_duplicates('biz').set_index('biz')['addr'].to_dict()
            fills=biz_norm.map(known); miss=missing_address_mask(df.iloc[:,col_addr]) & fills.notna()
            df.loc[miss,df.columns[col_addr]]=fills[miss]; st.session_state.df=df; st.rerun()
        if st.button('② 조달청 API 검색', width='stretch'):
            unique_biz=[x for x in biz_norm.loc[api_missing_indices].drop_duplicates().tolist() if x]
            if not unique_biz: st.info('사업자번호로 조회할 주소가 없습니다.')
            else:
                progress=st.progress(0,text='조달청 주소 조회 중...')
                for i,biz in enumerate(unique_biz):
                    addr=get_addr_api(biz)
                    if addr:
                        mask=biz_norm.eq(biz) & missing_address_mask(df.iloc[:,col_addr]); df.loc[mask,df.columns[col_addr]]=addr
                    touch_slot(); progress.progress((i+1)/len(unique_biz),text=f'{i+1}/{len(unique_biz)}개 업체 조회')
                st.session_state.df=df; st.rerun()
    if missing_count:
        rows=[]; seen=set()
        for idx in missing_indices:
            biz=biz_norm.at[idx]; company=str(df.iat[idx,col_company] if pd.notna(df.iat[idx,col_company]) else '').strip()
            key=('biz',biz) if biz else ('company',company,idx if not company else '')
            if key in seen: continue
            seen.add(key); rows.append({'_source_idx':idx,'업체명':company or '정보없음','사업자번호':biz or '확인불가','주소 수동 입력':''})
        edit_df=pd.DataFrame(rows).set_index('_source_idx')
        st.markdown(f'<span class="status warn">⚠ 주소 미확인 업체/건 {len(edit_df)}개</span>',unsafe_allow_html=True)
        st.caption('주소가 끝까지 확인되지 않아도 보고서는 생성되며, 기존 운영정책대로 타시도로 임시 반영됩니다. 검토용 기초자료의 비고에도 표시됩니다.')
        edited=st.data_editor(edit_df,disabled=['업체명','사업자번호'],column_config={'주소 수동 입력':st.column_config.TextColumn('주소 입력')},width='stretch',key='manual_address_editor')
        if st.button('입력한 주소 일괄 적용'):
            applied=0
            for idx in edited.index:
                new_addr=str(edited.at[idx,'주소 수동 입력'] or '').strip()
                if not new_addr: continue
                biz=biz_norm.at[idx]; company=str(df.iat[idx,col_company] if pd.notna(df.iat[idx,col_company]) else '').strip()
                mask=biz_norm.eq(biz) if biz else (df.iloc[:,col_company].astype(str).str.strip().eq(company) if company else df.index.to_series().eq(idx))
                df.loc[mask,df.columns[col_addr]]=new_addr; applied+=1
            if applied: st.session_state.df=df; st.rerun()
            else: st.warning('입력한 주소가 없습니다.')
    else:
        st.markdown(f'<span class="status ok">✓ 집계 대상 {ctx["target_amount"]:,}원 이상의 주소가 모두 채워졌습니다</span>',unsafe_allow_html=True)

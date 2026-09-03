import pandas as pd
import streamlit as st
from core_logic import get_addr_api, missing_address_mask, touch_slot


def render_address_tools(ctx):
    df = ctx['df']
    col_addr = ctx['col_addr']
    col_company = ctx['col_company']
    biz_norm = ctx['biz_norm']
    missing_indices = ctx['missing_indices']
    api_missing_indices = ctx['api_missing_indices']
    missing_count = ctx['missing_count']

    st.markdown('<div class="section-title compact-title">주소 보완</div>', unsafe_allow_html=True)
    a1, a2, a3 = st.columns([1, 1, 1.35], gap='small')
    with a1:
        if st.button('① 파일 내 주소 채우기', width='stretch'):
            addr_series = df.iloc[:, col_addr].replace(r'^\s*$', pd.NA, regex=True)
            known_df = pd.DataFrame({'biz': biz_norm, 'addr': addr_series})
            known = known_df.dropna(subset=['addr']).loc[lambda x: x['biz'].str.len().eq(10)].drop_duplicates('biz').set_index('biz')['addr'].to_dict()
            fills = biz_norm.map(known)
            miss = missing_address_mask(df.iloc[:, col_addr]) & fills.notna()
            df.loc[miss, df.columns[col_addr]] = fills[miss]
            st.session_state.df = df
            st.rerun()
        st.caption('같은 사업자번호의 기존 주소 재사용')

    with a2:
        if st.button('② 조달청 주소 찾기', width='stretch'):
            unique_biz = [x for x in biz_norm.loc[api_missing_indices].drop_duplicates().tolist() if x]
            if not unique_biz:
                st.info('사업자번호로 조회할 주소가 없습니다.')
            else:
                progress = st.progress(0, text='조달청 주소 조회 중...')
                for i, biz in enumerate(unique_biz):
                    addr = get_addr_api(biz)
                    if addr:
                        mask = biz_norm.eq(biz) & missing_address_mask(df.iloc[:, col_addr])
                        df.loc[mask, df.columns[col_addr]] = addr
                    touch_slot()
                    progress.progress((i + 1) / len(unique_biz), text=f'{i+1}/{len(unique_biz)}개 업체 조회')
                st.session_state.df = df
                st.rerun()
        st.caption('주소 없는 고유 사업자번호만 API 조회')

    with a3:
        if missing_count:
            st.markdown(f'<div class="mini-status warn-mini"><b>주소 미확인 {missing_count}건</b><br>미확인은 타시도로 임시 반영됩니다.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="mini-status ok-mini"><b>주소 확인 완료</b><br>{ctx["target_amount"]:,}원 이상 집계대상</div>', unsafe_allow_html=True)

    if missing_count:
        rows = []
        seen = set()
        for idx in missing_indices:
            biz = biz_norm.at[idx]
            company = str(df.iat[idx, col_company] if pd.notna(df.iat[idx, col_company]) else '').strip()
            key = ('biz', biz) if biz else ('company', company, idx if not company else '')
            if key in seen:
                continue
            seen.add(key)
            rows.append({'_source_idx': idx, '업체명': company or '정보없음', '사업자번호': biz or '확인불가', '주소 수동 입력': ''})

        edit_df = pd.DataFrame(rows).set_index('_source_idx')
        with st.expander(f'주소 수동 입력 · {len(edit_df)}개 업체/건', expanded=False):
            st.caption('필요한 항목만 입력하세요. 입력하지 않아도 보고서 생성은 가능합니다.')
            edited = st.data_editor(
                edit_df,
                disabled=['업체명', '사업자번호'],
                column_config={'주소 수동 입력': st.column_config.TextColumn('주소 입력')},
                width='stretch',
                height=min(340, 86 + max(1, min(len(edit_df), 8)) * 34),
                key='manual_address_editor',
            )
            if st.button('입력한 주소 일괄 적용', key='apply_manual_address'):
                applied = 0
                for idx in edited.index:
                    new_addr = str(edited.at[idx, '주소 수동 입력'] or '').strip()
                    if not new_addr:
                        continue
                    biz = biz_norm.at[idx]
                    company = str(df.iat[idx, col_company] if pd.notna(df.iat[idx, col_company]) else '').strip()
                    mask = biz_norm.eq(biz) if biz else (df.iloc[:, col_company].astype(str).str.strip().eq(company) if company else df.index.to_series().eq(idx))
                    df.loc[mask, df.columns[col_addr]] = new_addr
                    applied += 1
                if applied:
                    st.session_state.df = df
                    st.rerun()
                else:
                    st.warning('입력한 주소가 없습니다.')

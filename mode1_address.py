import urllib.parse

import pandas as pd
import streamlit as st
from core_logic import get_addr_api, missing_address_mask, touch_slot


def _bizno_url(biz):
    biz = str(biz or '').strip()
    if not biz or biz == '확인불가':
        return 'https://bizno.net/'
    return 'https://bizno.net/?query=' + urllib.parse.quote(biz)


def _propagate_known_addresses(df, col_addr, biz_norm):
    """이미 확인된 주소를 동일한 10자리 사업자등록번호의 빈 행에만 자동 전파합니다."""
    addr_series = df.iloc[:, col_addr]
    known_by_biz = {}

    for idx in df.index:
        addr = str(addr_series.at[idx] if pd.notna(addr_series.at[idx]) else '').strip()
        biz = str(biz_norm.at[idx] or '').strip()
        if addr and len(biz) == 10 and biz not in known_by_biz:
            known_by_biz[biz] = addr

    filled = 0
    missing = missing_address_mask(df.iloc[:, col_addr])
    for idx in df.index[missing]:
        biz = str(biz_norm.at[idx] or '').strip()
        if len(biz) != 10:
            continue
        addr = known_by_biz.get(biz, '')
        if addr:
            df.iat[idx, col_addr] = addr
            filled += 1
    return filled


def render_address_tools(ctx):
    df = ctx['df']
    col_addr = ctx['col_addr']
    col_company = ctx['col_company']
    biz_norm = ctx['biz_norm']
    missing_indices = ctx['missing_indices']
    api_missing_indices = ctx['api_missing_indices']
    missing_count = ctx['missing_count']

    # 업로드 자료 안에 이미 주소가 있는 동일 사업자번호가 있으면 별도 버튼 없이 즉시 재사용합니다.
    if _propagate_known_addresses(df, col_addr, biz_norm):
        st.session_state.df = df
        st.rerun()

    st.markdown('<div class="section-title compact-title">주소 보완</div>', unsafe_allow_html=True)
    a1, a2 = st.columns([1, 1.15], gap='small')

    with a1:
        if st.button('조달청 주소 찾기', width='stretch'):
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
                # API로 새 주소가 확인되면 같은 사업자번호의 빈 주소에만 자동 반영합니다.
                _propagate_known_addresses(df, col_addr, biz_norm)
                st.session_state.df = df
                st.rerun()
        st.caption('주소 없는 업체만 나라장터 API 조회 · 동일 사업자번호에만 자동 반영')

    with a2:
        if missing_count:
            st.markdown(f'<div class="mini-status warn-mini"><b>주소 미확인 {missing_count}건</b><br>미확인은 타시도로 임시 반영</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="mini-status ok-mini"><b>주소 확인 완료</b><br>{ctx["target_amount"]:,}원 이상 집계대상</div>', unsafe_allow_html=True)

    if missing_count:
        rows = []
        seen = set()
        for idx in missing_indices:
            biz = str(biz_norm.at[idx] or '').strip()
            company = str(df.iat[idx, col_company] if pd.notna(df.iat[idx, col_company]) else '').strip()
            # 유효한 사업자번호가 있으면 사업자번호별 1행만 표시합니다.
            # 사업자번호가 없거나 비정상이면 자동 전파하지 않으므로 각 원본 행을 개별 표시합니다.
            key = ('biz', biz) if len(biz) == 10 else ('row', idx)
            if key in seen:
                continue
            seen.add(key)
            biz_display = biz if len(biz) == 10 else '확인불가'
            rows.append({
                '_source_idx': idx,
                '업체명': company or '정보없음',
                '사업자번호': biz_display,
                'Bizno 조회': _bizno_url(biz_display),
                '주소 수동 입력': '',
            })

        edit_df = pd.DataFrame(rows).set_index('_source_idx')
        with st.expander(f'주소 미확인 업체 확인 · {len(edit_df)}개', expanded=False):
            st.caption('Bizno 조회를 눌러 주소를 확인한 뒤 필요한 주소만 입력하세요. 적용한 주소는 동일한 사업자등록번호의 빈 행에만 자동 반영됩니다.')
            edited = st.data_editor(
                edit_df,
                disabled=['업체명', '사업자번호', 'Bizno 조회'],
                column_config={
                    '업체명': st.column_config.TextColumn('업체명', width='medium'),
                    '사업자번호': st.column_config.TextColumn('사업자번호', width='small'),
                    'Bizno 조회': st.column_config.LinkColumn('Bizno 조회', display_text='조회하기', width='small'),
                    '주소 수동 입력': st.column_config.TextColumn('주소 입력', width='large'),
                },
                width='stretch',
                height=min(360, 90 + max(1, min(len(edit_df), 8)) * 35),
                key='manual_address_editor',
            )
            if st.button('입력한 주소 적용', key='apply_manual_address'):
                applied = 0
                for idx in edited.index:
                    new_addr = str(edited.at[idx, '주소 수동 입력'] or '').strip()
                    if not new_addr:
                        continue
                    biz = str(biz_norm.at[idx] or '').strip()
                    if len(biz) == 10:
                        mask = biz_norm.eq(biz)
                        df.loc[mask, df.columns[col_addr]] = new_addr
                    else:
                        # 사업자번호가 없거나 비정상이면 해당 행에만 적용합니다.
                        df.iat[idx, col_addr] = new_addr
                    applied += 1
                if applied:
                    _propagate_known_addresses(df, col_addr, biz_norm)
                    st.session_state.df = df
                    st.rerun()
                else:
                    st.warning('입력한 주소가 없습니다.')

import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st
from address_api import get_address_from_public_apis
from core_logic import missing_address_mask, touch_slot
from manual_address_store import load_manual_addresses, get_manual_address, save_manual_address

# 본 사이트와 4개 미러의 동시 운영을 고려해 앱 인스턴스당 2개 업체만 병렬 조회합니다.
ADDRESS_LOOKUP_WORKERS = 2


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


def _lookup_one_business(biz):
    """한 사업자번호는 나라장터→학교장터→공정위→지역화폐 순서를 지켜 조회합니다."""
    return biz, *get_address_from_public_apis(biz)


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
        if st.button('API 주소 찾기', width='stretch'):
            unique_biz = [x for x in biz_norm.loc[api_missing_indices].drop_duplicates().tolist() if x]
            if not unique_biz:
                st.info('사업자번호로 조회할 주소가 없습니다.')
            else:
                progress = st.progress(0, text='주소 조회 중...')
                found_procurement = 0
                found_s2b = 0
                found_ftc = 0
                found_local = 0
                completed = 0

                with ThreadPoolExecutor(max_workers=ADDRESS_LOOKUP_WORKERS) as executor:
                    futures = {executor.submit(_lookup_one_business, biz): biz for biz in unique_biz}
                    for future in as_completed(futures):
                        biz = futures[future]
                        try:
                            _, addr, source = future.result()
                        except Exception:
                            addr, source = None, None

                        if addr:
                            mask = biz_norm.eq(biz) & missing_address_mask(df.iloc[:, col_addr])
                            df.loc[mask, df.columns[col_addr]] = addr
                            if source == '나라장터':
                                found_procurement += 1
                            elif source == '학교장터(S2B)':
                                found_s2b += 1
                            elif source == '공정위 통신판매사업자':
                                found_ftc += 1
                            elif source == '지역화폐 가맹점':
                                found_local += 1

                        touch_slot()
                        completed += 1
                        progress.progress(
                            completed / len(unique_biz),
                            text=f'{completed}/{len(unique_biz)}개 업체 조회 · 나라장터 → 학교장터 → 공정위 → 지역화폐',
                        )

                _propagate_known_addresses(df, col_addr, biz_norm)
                st.session_state.df = df
                st.session_state.address_api_result = {
                    '나라장터': found_procurement,
                    '학교장터(S2B)': found_s2b,
                    '공정위 통신판매사업자': found_ftc,
                    '지역화폐 가맹점': found_local,
                }
                st.rerun()
        st.caption(
            '주소 없는 업체만 나라장터 → 학교장터(S2B) → 공정위 통신판매사업자 → 지역화폐 가맹점 순으로 조회 · '
            '사업자번호 정확일치만 반영 · 개별 조회 24시간 캐시 · 앱당 최대 2개 업체 동시 조회'
        )
        result = st.session_state.pop('address_api_result', None)
        if result:
            total = sum(result.values())
            st.caption(
                f'최근 조회: {total}개 확인 · 나라장터 {result.get("나라장터", 0)}개 · '
                f'학교장터 {result.get("학교장터(S2B)", 0)}개 · '
                f'공정위 {result.get("공정위 통신판매사업자", 0)}개 · '
                f'지역화폐 {result.get("지역화폐 가맹점", 0)}개'
            )

    with a2:
        if missing_count:
            st.markdown(f'<div class="mini-status warn-mini"><b>주소 미확인 {missing_count}건</b><br>미확인은 타시도로 임시 반영</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="mini-status ok-mini"><b>주소 확인 완료</b><br>{ctx["target_amount"]:,}원 이상 집계대상</div>', unsafe_allow_html=True)

    if missing_count:
        # 모든 본/미러 앱이 같은 GitHub JSON을 읽으므로 다른 사용자의 수동입력도 제안할 수 있습니다.
        shared_store = load_manual_addresses()
        rows = []
        seen = set()
        for idx in missing_indices:
            biz = str(biz_norm.at[idx] or '').strip()
            company = str(df.iat[idx, col_company] if pd.notna(df.iat[idx, col_company]) else '').strip()
            key = ('biz', biz) if len(biz) == 10 else ('row', idx)
            if key in seen:
                continue
            seen.add(key)
            biz_display = biz if len(biz) == 10 else '확인불가'
            previous = get_manual_address(biz, shared_store) if len(biz) == 10 else None
            rows.append({
                '_source_idx': idx,
                '업체명': company or '정보없음',
                '사업자번호': biz_display,
                '이전 입력주소': previous or '',
                '이전주소 사용': False,
                'Bizno 조회': _bizno_url(biz_display),
                '주소 수동 입력': '',
            })

        edit_df = pd.DataFrame(rows).set_index('_source_idx')
        with st.expander(f'주소 미확인 업체 확인 · {len(edit_df)}개', expanded=False):
            st.caption(
                '다른 사용자가 같은 사업자번호에 입력한 주소가 있으면 이전 입력주소에 표시됩니다. '
                '자동 반영하지 않으며, 확인 후 이전주소 사용을 선택하거나 Bizno 조회 후 직접 입력하세요.'
            )
            edited = st.data_editor(
                edit_df,
                disabled=['업체명', '사업자번호', '이전 입력주소', 'Bizno 조회'],
                column_config={
                    '업체명': st.column_config.TextColumn('업체명', width='medium'),
                    '사업자번호': st.column_config.TextColumn('사업자번호', width='small'),
                    '이전 입력주소': st.column_config.TextColumn('이전 입력주소', width='large'),
                    '이전주소 사용': st.column_config.CheckboxColumn('사용', width='small'),
                    'Bizno 조회': st.column_config.LinkColumn('Bizno 조회', display_text='조회하기', width='small'),
                    '주소 수동 입력': st.column_config.TextColumn('주소 입력', width='large'),
                },
                width='stretch',
                height=min(360, 90 + max(1, min(len(edit_df), 8)) * 35),
                key='manual_address_editor',
            )
            if st.button('선택·입력한 주소 적용', key='apply_manual_address'):
                applied = 0
                saved = 0
                save_errors = []
                for idx in edited.index:
                    biz = str(biz_norm.at[idx] or '').strip()
                    company = str(df.iat[idx, col_company] if pd.notna(df.iat[idx, col_company]) else '').strip()
                    previous = str(edited.at[idx, '이전 입력주소'] or '').strip()
                    use_previous = bool(edited.at[idx, '이전주소 사용'])
                    new_addr = str(edited.at[idx, '주소 수동 입력'] or '').strip()

                    # 새로 입력한 주소가 있으면 그것을 우선하고, 없을 때만 사용자가 선택한 이전주소를 씁니다.
                    chosen = new_addr or (previous if use_previous else '')
                    if not chosen:
                        continue

                    if len(biz) == 10:
                        mask = biz_norm.eq(biz)
                        df.loc[mask, df.columns[col_addr]] = chosen
                    else:
                        df.iat[idx, col_addr] = chosen
                    applied += 1

                    # 신규 수동입력만 공유 DB에 기록합니다. 이전주소 재사용은 불필요한 GitHub 쓰기를 하지 않습니다.
                    if new_addr and len(biz) == 10:
                        ok, message = save_manual_address(biz, new_addr, company)
                        if ok:
                            saved += 1
                        else:
                            save_errors.append(f'{company or biz}: {message}')

                if applied:
                    _propagate_known_addresses(df, col_addr, biz_norm)
                    st.session_state.df = df
                    st.session_state.manual_address_notice = {
                        'applied': applied,
                        'saved': saved,
                        'errors': save_errors,
                    }
                    st.rerun()
                else:
                    st.warning('선택하거나 입력한 주소가 없습니다.')

            notice = st.session_state.pop('manual_address_notice', None)
            if notice:
                st.success(f'{notice["applied"]}개 주소를 적용했습니다. 신규 수동주소 {notice["saved"]}개를 공유했습니다.')
                if notice['errors']:
                    st.warning('일부 공유주소 저장에 실패했습니다: ' + ' / '.join(notice['errors'][:3]))

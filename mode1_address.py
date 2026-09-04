import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st
from address_api import get_address_from_public_apis
from core_logic import missing_address_mask, touch_slot
from manual_address_store import load_manual_addresses, get_manual_address, save_manual_address

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
    return biz, *get_address_from_public_apis(biz)


def _set_manual_address(input_key, address):
    st.session_state[input_key] = address


def _load_all_previous_addresses(rows):
    loaded = 0
    for row in rows:
        previous = str(row.get('이전 입력주소', '') or '').strip()
        if not previous:
            continue
        input_key = f'manual_addr_input_{row["_source_idx"]}'
        if str(st.session_state.get(input_key, '') or '').strip():
            continue
        st.session_state[input_key] = previous
        loaded += 1
    st.session_state.bulk_previous_notice = loaded
    st.session_state.open_manual_editor = True


def _open_manual_editor():
    st.session_state.open_manual_editor = True


def _build_manual_rows(df, missing_indices, biz_norm, col_company, shared_store):
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
            'Bizno 조회': _bizno_url(biz_display),
        })
    return rows


def render_address_tools(ctx):
    df = ctx['df']
    col_addr = ctx['col_addr']
    col_company = ctx['col_company']
    biz_norm = ctx['biz_norm']
    missing_indices = ctx['missing_indices']
    api_missing_indices = ctx['api_missing_indices']
    missing_count = ctx['missing_count']

    if _propagate_known_addresses(df, col_addr, biz_norm):
        st.session_state.df = df
        st.rerun()

    shared_store = load_manual_addresses() if missing_count else {}
    rows = _build_manual_rows(df, missing_indices, biz_norm, col_company, shared_store) if missing_count else []
    previous_count = sum(1 for row in rows if str(row['이전 입력주소'] or '').strip())
    direct_count = max(len(rows) - previous_count, 0)
    api_target_count = len([x for x in biz_norm.loc[api_missing_indices].drop_duplicates().tolist() if x])

    st.markdown(
        '''<div class="address-head-row"><div><div class="address-title">● 주소 보완</div>
        <div class="address-sub">API와 기존 사용자 주소를 활용해 주소를 채운 뒤, 남은 업체만 직접 입력합니다.</div></div>'''
        + (
            f'<div class="address-missing-card"><b>주소 미확인 {missing_count:,}건</b><span>중복 업체를 포함한 전체 미확인 계약 건수</span></div>'
            if missing_count
            else '<div class="address-complete-card"><b>주소 확인 완료</b><span>집계대상 주소가 모두 확인되었습니다.</span></div>'
        )
        + '</div>',
        unsafe_allow_html=True,
    )

    if not missing_count:
        return

    c1, c2, c3 = st.columns(3, gap='small')

    with c1:
        with st.container(border=True, key='api_address_card'):
            st.markdown(
                f'''<div class="step-card-title blue"><span>1</span> API로 주소 채우기</div>
                <div class="step-card-desc">나라장터 → 학교장터 → 공정위 → 지역화폐 순으로 조회합니다.<br>사업자번호 10자리 정확일치만 반영합니다.</div>
                <div class="step-count blue-count">API 조회대상 <b>{api_target_count:,}개 업체</b></div>''',
                unsafe_allow_html=True,
            )
            if st.button('⌕  API로 주소 채우기', key='api_fill_button', width='stretch'):
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

            st.caption('개별 조회 24시간 캐시 · 앱당 최대 2개 업체 동시 조회')

    with c2:
        with st.container(border=True, key='user_address_card'):
            st.markdown(
                f'''<div class="step-card-title green"><span>2</span> 사용자 주소 채우기</div>
                <div class="step-card-desc">공동 주소정보에서 이전에 입력했던 주소를 한꺼번에 불러옵니다.<br>기존 입력값은 덮어쓰지 않습니다.</div>
                <div class="step-count green-count">사용자 주소 보유 <b>{previous_count:,}개 업체</b></div>''',
                unsafe_allow_html=True,
            )
            st.button(
                f'↺  이전 주소 한꺼번에 불러오기 · {previous_count:,}개',
                key='bulk_user_address_button',
                on_click=_load_all_previous_addresses,
                args=(rows,),
                width='stretch',
                disabled=previous_count == 0,
            )
            st.caption('불러온 주소는 입력칸까지만 채워지며, 마지막 적용 전 수정할 수 있습니다.')

    with c3:
        with st.container(border=True, key='manual_address_card'):
            st.markdown(
                f'''<div class="step-card-title orange"><span>3</span> 남은 주소 직접 입력</div>
                <div class="step-card-desc">API와 사용자 주소로도 채워지지 않은 업체만 직접 확인합니다.<br>입력 후 한 번에 적용할 수 있습니다.</div>
                <div class="step-count orange-count">직접 입력 필요 <b>{direct_count:,}개 업체</b></div>''',
                unsafe_allow_html=True,
            )
            st.button(
                f'✎  주소 미확인 업체 확인 · {len(rows):,}개',
                key='open_manual_button',
                on_click=_open_manual_editor,
                width='stretch',
            )
            st.caption('사업자번호가 없는 행은 해당 행에만 적용되고 공동 DB에는 저장되지 않습니다.')

    result = st.session_state.pop('address_api_result', None)
    if result:
        total = sum(result.values())
        st.success(
            f'최근 API 조회에서 {total}개 업체 주소를 확인했습니다. '
            f'나라장터 {result.get("나라장터", 0)}개 · 학교장터 {result.get("학교장터(S2B)", 0)}개 · '
            f'공정위 {result.get("공정위 통신판매사업자", 0)}개 · 지역화폐 {result.get("지역화폐 가맹점", 0)}개'
        )

    bulk_notice = st.session_state.pop('bulk_previous_notice', None)
    if bulk_notice is not None:
        if bulk_notice:
            st.success(f'공동 주소정보에서 {bulk_notice}개 업체의 이전 주소를 불러왔습니다. 아래에서 확인한 뒤 입력한 주소 적용을 눌러주세요.')
        else:
            st.info('불러올 새 이전 주소가 없습니다. 이미 입력된 주소는 그대로 유지했습니다.')

    expand_manual = bool(st.session_state.pop('open_manual_editor', False))
    with st.expander(f'주소 미확인 업체 상세 · {len(rows):,}개', expanded=expand_manual):
        st.caption(
            '이전 입력주소가 있으면 주소 자체를 눌러 한 건씩 채울 수도 있습니다. '
            '필요하면 주소를 수정한 뒤 아래의 입력한 주소 적용 버튼을 누르세요.'
        )

        h1, h2, h3, h4, h5 = st.columns([1.25, 0.9, 2.25, 0.8, 2.25], gap='small')
        h1.markdown('**업체명**')
        h2.markdown('**사업자번호**')
        h3.markdown('**이전 입력주소**')
        h4.markdown('**Bizno 조회**')
        h5.markdown('**주소 입력**')

        for row in rows:
            idx = row['_source_idx']
            previous = row['이전 입력주소']
            input_key = f'manual_addr_input_{idx}'
            c1r, c2r, c3r, c4r, c5r = st.columns([1.25, 0.9, 2.25, 0.8, 2.25], gap='small', vertical_alignment='center')
            c1r.write(row['업체명'])
            c2r.write(row['사업자번호'])

            if previous:
                c3r.button(
                    previous,
                    key=f'use_previous_addr_{idx}',
                    help='클릭하면 이 주소를 오른쪽 주소 입력란에 채웁니다.',
                    width='stretch',
                    on_click=_set_manual_address,
                    args=(input_key, previous),
                )
            else:
                c3r.caption('기록 없음')

            c4r.link_button('조회하기', row['Bizno 조회'], width='stretch')
            c5r.text_input(
                '주소 입력',
                key=input_key,
                label_visibility='collapsed',
                placeholder='주소를 입력하세요',
            )

        if st.button('입력한 주소 적용', key='apply_manual_address', type='primary'):
            applied = 0
            saved = 0
            save_errors = []
            for row in rows:
                idx = row['_source_idx']
                biz = str(biz_norm.at[idx] or '').strip()
                company = str(df.iat[idx, col_company] if pd.notna(df.iat[idx, col_company]) else '').strip()
                new_addr = str(st.session_state.get(f'manual_addr_input_{idx}', '') or '').strip()
                if not new_addr:
                    continue

                if len(biz) == 10:
                    mask = biz_norm.eq(biz)
                    df.loc[mask, df.columns[col_addr]] = new_addr
                else:
                    df.iat[idx, col_addr] = new_addr
                applied += 1

                previous = str(row['이전 입력주소'] or '').strip()
                if len(biz) == 10 and new_addr != previous:
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
                for row in rows:
                    st.session_state.pop(f'manual_addr_input_{row["_source_idx"]}', None)
                st.rerun()
            else:
                st.warning('입력한 주소가 없습니다.')

        notice = st.session_state.pop('manual_address_notice', None)
        if notice:
            st.success(f'{notice["applied"]}개 주소를 적용했습니다. 신규 수동주소 {notice["saved"]}개를 공유했습니다.')
            if notice['errors']:
                st.warning('일부 공유주소 저장에 실패했습니다: ' + ' / '.join(notice['errors'][:3]))

    st.markdown(
        '''<div class="workflow-strip"><b>작업 순서</b><span>1 자료 입력</span><i>→</i><span>2 API 주소 채우기</span><i>→</i><span>3 사용자 주소 채우기</span><i>→</i><span>4 남은 주소 직접 입력</span><i>→</i><span>5 적용 및 결과 다운로드</span></div>''',
        unsafe_allow_html=True,
    )

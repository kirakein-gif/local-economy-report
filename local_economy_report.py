import streamlit as st
from core_logic import MAX_CONCURRENT, QUEUE_POLL_SECONDS, acquire_slot, ensure_session_id, release_slot, waiting_status
from ui_style import APP_CSS
from ui_compact import COMPACT_UI_CSS
from app_mode1 import render_mode1
from app_mode2 import render_mode2

APP_VERSION = "1.6.0"
DEPLOY_DATE = "2026.09.04"

st.set_page_config(
    page_title="지역경제활성화 자동 집계 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)
st.markdown(COMPACT_UI_CSS, unsafe_allow_html=True)


def render_waiting_room():
    active, waiting, position = waiting_status()
    position_text = f"{position}번째" if position else "확인 중"
    st.markdown(f'<meta http-equiv="refresh" content="{QUEUE_POLL_SECONDS}">', unsafe_allow_html=True)
    st.markdown(
        f'''<div class="waiting-card"><div class="waiting-icon">⏳</div><div class="waiting-title">현재 사용자가 많아 대기 중입니다</div><div class="waiting-desc">대기 순번 <b>{position_text}</b> · 자리가 나면 자동으로 접속됩니다.</div><div class="waiting-meta">최대 동시 사용자 {MAX_CONCURRENT}명 · 현재 사용 {active}명 · 대기 {waiting}명</div></div>''',
        unsafe_allow_html=True,
    )
    st.stop()


ensure_session_id()
if not acquire_slot():
    render_waiting_room()

with st.sidebar:
    st.markdown('<div class="sidebar-brand">▦&nbsp;&nbsp;지역경제활성화</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-section">업무 메뉴</div>', unsafe_allow_html=True)
    mode = st.radio(
        "업무 선택",
        ["자료 집계 · 분기/검토파일", "반기보고서 최종작성"],
        label_visibility="collapsed",
        key="work_mode",
    )
    st.divider()
    if st.button("나가기 · 자리 반납", width='stretch', key='global_release'):
        release_slot()
        st.success("자리를 반납했습니다. 페이지를 닫으셔도 됩니다.")
        st.stop()
    st.markdown(
        '''<div class="developer-note"><b>천안버들유치원 · 나대현</b><br>문의 및 오류 신고는 메신저로 부탁드립니다.</div>''',
        unsafe_allow_html=True,
    )
    st.divider()

active_count, waiting_count, _ = waiting_status()

if mode.startswith("자료"):
    st.markdown(
        f'''<div class="standard-hero">
            <div class="hero-left"><div class="hero-building">▦</div><div>
                <div class="hero-title">지역경제 활성화 계약자료 주소 정리</div>
                <div class="hero-sub">계약자료의 주소를 자동으로 조회하고, 쉽고 빠르게 보완할 수 있습니다.</div>
            </div></div>
            <div class="hero-info"><span>i</span><div>엑셀 파일을 업로드하고, 아래 순서에 따라 진행해 주세요.<small>v{APP_VERSION} · {DEPLOY_DATE} · 사용 {active_count}/{MAX_CONCURRENT} · 대기 {waiting_count}</small></div></div>
        </div>''',
        unsafe_allow_html=True,
    )
    render_mode1()
else:
    st.markdown(
        f'''<div class="app-head"><div class="app-brand"><div class="app-logo">▦</div><div><div class="app-title">지역경제활성화 자동 집계</div><div class="app-sub">검토 완료 기초자료 재업로드 · 최종 4시트 보고서</div></div></div><div class="live-chip">● 사용 {active_count}/{MAX_CONCURRENT} · 대기 {waiting_count}</div></div>''',
        unsafe_allow_html=True,
    )
    render_mode2()

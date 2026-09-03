import streamlit as st
from core_logic import MAX_CONCURRENT, QUEUE_POLL_SECONDS, acquire_slot, ensure_session_id, release_slot, waiting_status
from ui_style import APP_CSS
from app_mode1 import render_mode1
from app_mode2 import render_mode2

st.set_page_config(
    page_title="지역경제활성화 자동 집계 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)


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

active_count, waiting_count, _ = waiting_status()
st.markdown(
    f'''<div class="app-head"><div class="app-brand"><div class="app-logo">📊</div><div><div class="app-title">지역경제활성화 자동 집계 시스템</div><div class="app-sub">자료관리목록 정제 · 주소 보완 · 분기보고서 · 반기 4시트 보고서</div></div></div><div class="live-chip">● 사용 {active_count}/{MAX_CONCURRENT} · 대기 {waiting_count}</div></div>''',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="side-section">업무 선택</div>', unsafe_allow_html=True)
    mode = st.radio(
        "업무 선택",
        ["① 자료 집계 · 분기보고서", "② 반기보고서 최종작성"],
        label_visibility="collapsed",
        key="work_mode",
    )
    st.divider()

if mode.startswith("①"):
    render_mode1()
else:
    render_mode2()

with st.sidebar:
    st.divider()
    st.caption("개발: 천안버들유치원 나대현 · 문의 및 오류 신고는 메신저로 부탁드립니다.")

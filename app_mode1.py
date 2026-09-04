import streamlit as st

from mode1_prepare import prepare_mode1
from mode1_address import render_address_tools
from mode1_output import render_mode1_outputs
from mode1_style import MODE1_CSS
from ui_compact import COMPACT_UI_CSS


def render_mode1():
    # 기본 디자인 뒤에 실제 배포화면 보정 CSS를 적용합니다.
    st.markdown(MODE1_CSS, unsafe_allow_html=True)
    st.markdown(COMPACT_UI_CSS, unsafe_allow_html=True)
    ctx = prepare_mode1()
    render_address_tools(ctx)
    render_mode1_outputs(ctx)

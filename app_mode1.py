import streamlit as st

from mode1_prepare import prepare_mode1
from mode1_address import render_address_tools
from mode1_output import render_mode1_outputs
from ui_compact import COMPACT_UI_CSS


def render_mode1():
    # Native layout styles are owned by ui_compact; isolated components own theirs.
    st.markdown(COMPACT_UI_CSS, unsafe_allow_html=True)
    ctx = prepare_mode1()
    render_address_tools(ctx)
    render_mode1_outputs(ctx)

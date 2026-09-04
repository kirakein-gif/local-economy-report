import streamlit as st

from mode1_prepare import prepare_mode1
from mode1_address import render_address_tools
from mode1_output import render_mode1_outputs


def render_mode1():
    ctx = prepare_mode1()
    render_address_tools(ctx)
    render_mode1_outputs(ctx)

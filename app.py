import streamlit as st
from ui.styles import get_styles
from ui.main   import render_app

st.set_page_config(
    page_title="DynTable IoT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_styles(), unsafe_allow_html=True)

render_app()

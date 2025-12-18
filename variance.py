import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

def toggle_sidebar():
    st.session_state.sidebar_open = not st.session_state.sidebar_open

# -------------------------------------------------
# CSS (SLIDE SIDEBAR, DON'T REMOVE IT)
# -------------------------------------------------
if st.session_state.sidebar_open:
    SIDEBAR_STYLE = """
    <style>
    section[data-testid="stSidebar"] {
        width: 280px !important;
        margin-left: 0px !important;
        transition: margin-left 0.3s ease;
    }
    </style>
    """
else:
    SIDEBAR_STYLE = """
    <style>
    section[data-testid="stSidebar"] {
        width: 280px !important;
        margin-left: -280px !important;
        transition: margin-left 0.3s ease;
    }
    </style>
    """

st.markdown(SIDEBAR_STYLE, unsafe_allow_html=True)

# -------------------------------------------------
# HIDE DEFAULT STREAMLIT UI
# -------------------------------------------------
st.markdown("""
<style>
[data-testid="collapsedControl"] {display: none;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# TOP BAR
# -------------------------------------------------
top1, top2 = st.columns([1, 9])
with top1:
    st.button("☰ Filters", on_click=toggle_sidebar)

with top2:
    st.title("🏪 Sales QTY Check - JAN to NOV")

# -------------------------------------------------
# SIDEBAR CONTENT (ALWAYS RENDERED)
# -------------------------------------------------
with st.sidebar:
    st.subheader("🔍 Filters")
    selected_outlet = st.selectbox(
        "🏬 Select Outlet",
        ["All Outlets", "Outlet A", "Outlet B", "Outlet C"]
    )

# -------------------------------------------------
# MAIN CONTENT
# -------------------------------------------------
st.write("Selected Outlet:", selected_outlet)

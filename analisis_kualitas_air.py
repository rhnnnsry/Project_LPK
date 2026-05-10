import streamlit as st

import pandas as pd

import numpy as np

import plotly.express as px

import plotly.graph_objects as go

from reportlab.platypus import SimpleDocTemplate, Paragraph

from reportlab.lib.styles import getSampleStyleSheet


# =====================================================

# CONFIG

# =====================================================


st.set_page_config(

page_title="WaterLab Analyzer Pro",

layout="wide"

)


# =====================================================

# CUSTOM CSS

# =====================================================


st.markdown("""

<style>

.main {

background-color: #0e1117;

color: white;

}


h1, h2, h3 {

color: #00d4ff;

}


.stButton>button {

background-color: #00d4ff;

color: black;

border-radius: 10px;

}

</style>

""", unsafe_allow_html=True)


# =====================================================

# TITLE

# =====================================================


st.title("🌊 WaterLab Analyzer Pro")

st.write("Sistem Analisis Sampling Air Permukaan & Air Limbah")


# =====================================================

# SIDEBAR MENU

# =====================================================


menu = st.sidebar.selectbox(

"Pilih Menu",

[

"Dashboard",

"Air Permukaan",

"Air Limbah",

"Upload Excel",

"Statistik & Grafik",

"Export PDF"

]

)


# =====================================================

# DASHBOARD

# ===================================================
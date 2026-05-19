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
    page_title="HydroLysis",
    layout="wide"
)

# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>
.main {
    background-color: #0B1727;
    color: #EAF4FF;
}

section[data-testid="stSidebar"] {
    background-color: #111C2D;
}

h1, h2, h3 {
    color: #00CFFF;
}

.stButton>button {
    background-color: #00CFFF;
    color: black;
    border-radius: 10px;
    border: none;
    font-weight: bold;
}

.stNumberInput input,
.stTextInput input,
.stTextArea textarea {
    background-color: #1A2636;
    color: white;
}

.stSelectbox div[data-baseweb="select"] {
    background-color: #1A2636;
}

[data-testid="stDataFrame"] {
    background-color: #111C2D;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# TITLE
# =====================================================

st.title("HydroLysis")
st.write("Program Analisis Kualitas Air Hasil Sampling Air Permukaan & Air Limbah")

# =====================================================
# SIDEBAR MENU
# =====================================================

menu = st.sidebar.selectbox(
    "Pilih Menu",
    [
        "Dashboard",
        "Air Permukaan",
        "Air Limbah",
        "Upload Data Excel",
        "Statistik & Grafik",
        "Export PDF"
    ]
)

# =====================================================
# DASHBOARD
# =====================================================

if menu == "Dashboard":

    st.header("📊 Dashboard Monitoring")

    data = {
        "Parameter": ["pH", "COD", "BOD", "TSS", "DO"],
        "Nilai": [7.2, 85, 25, 40, 6]
    }

    df = pd.DataFrame(data)

    col1, col2 = st.columns(2)

    with col1:
        st.dataframe(df)

    with col2:
        fig = px.bar(
            df,
            x="Parameter",
            y="Nilai",
            title="Kualitas Air"
        )

        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# AIR PERMUKAAN
# =====================================================

elif menu == "Air Permukaan":

    st.header("🌊 Analisis Air Permukaan")

    submenu = st.selectbox(
        "Pilih Parameter",
        [
            "TSS",
            "COD",
            "BOD",
            "TDS"
        ]
    )

    # =================================================
    # TSS
    # =================================================

    if submenu == "TSS":

        st.subheader("Perhitungan TSS")

        berat_awal = st.number_input(
            "Berat filter awal (mg)",
            min_value=0.0,
            key="tss_awal"
        )

        berat_akhir = st.number_input(
            "Berat filter akhir (mg)",
            min_value=0.0,
            key="tss_akhir"
        )

        volume = st.number_input(
            "Volume sampel (mL)",
            min_value=0.0,
            key="tss_volume"
        )

        if st.button("Hitung TSS"):

            tss = ((berat_akhir - berat_awal) * 1000) / volume

            st.success(f"Nilai TSS = {tss:.2f} mg/L")

            if tss <= 50:
                st.success("✅ Memenuhi baku mutu")
            else:
                st.error("❌ Melebihi baku mutu")

            fig = go.Figure(
                data=[go.Bar(x=["TSS"], y=[tss])]
            )

            st.plotly_chart(fig, use_container_width=True)

    # =================================================
    # COD
    # =================================================

    elif submenu == "COD":

        st.subheader("Perhitungan COD")

        blanko = st.number_input(
            "Volume blanko (mL)",
            min_value=0.0,
            key="cod_blanko"
        )

        sampel = st.number_input(
            "Volume sampel (mL)",
            min_value=0.0,
            key="cod_sampel"
        )

        normalitas = st.number_input(
            "Normalitas FAS",
            min_value=0.0,
            key="cod_normalitas"
        )

        volume_sampel = st.number_input(
            "Volume sampel air (mL)",
            min_value=0.0,
            key="cod_volume"
        )

        if st.button("Hitung COD"):

            cod = ((blanko - sampel) * normalitas * 8000) / volume_sampel

            st.success(f"Nilai COD = {cod:.2f} mg/L")

            if cod <= 100:
                st.success("✅ Memenuhi baku mutu")
            else:
                st.error("❌ Melebihi baku mutu")

    # =================================================
    # BOD
    # =================================================

    elif submenu == "BOD":

        st.subheader("Perhitungan BOD")

        do_awal = st.number_input(
            "DO Awal",
            min_value=0.0,
            key="bod_awal"
        )

        do_akhir = st.number_input(
            "DO Akhir",
            min_value=0.0,
            key="bod_akhir"
        )

        if st.button("Hitung BOD"):

            bod = do_awal - do_akhir

            st.success(f"Nilai BOD = {bod:.2f} mg/L")

            if bod <= 30:
                st.success("✅ Memenuhi baku mutu")
            else:
                st.error("❌ Melebihi baku mutu")

    # =================================================
    # TDS
    # =================================================

    elif submenu == "TDS":

        st.subheader("Perhitungan TDS")

        berat_awal = st.number_input(
            "Berat cawan awal (mg)",
            min_value=0.0,
            key="tds_awal"
        )

        berat_akhir = st.number_input(
            "Berat cawan akhir (mg)",
            min_value=0.0,
            key="tds_akhir"
        )

        volume = st.number_input(
            "Volume sampel",
            min_value=0.0,
            key="tds_volume"
        )

        if st.button("Hitung TDS"):

            tds = ((berat_akhir - berat_awal) * 1000) / volume

            st.success(f"Nilai TDS = {tds:.2f} mg/L")

# =====================================================
# AIR LIMBAH
# =====================================================

elif menu == "Air Limbah":

    st.header("🏭 Analisis Air Limbah")

    parameter = st.selectbox(
        "Pilih Parameter",
        [
            "pH",
            "COD",
            "BOD",
            "Amonia"
        ]
    )

    # ==============================================
    # pH
    # ==============================================

    if parameter == "pH":

        ph = st.number_input(
            "Masukkan nilai pH",
            min_value=0.0,
            max_value=14.0
        )

        if st.button("Evaluasi pH"):

            if 6 <= ph <= 9:
                st.success("✅ pH memenuhi baku mutu")
            else:
                st.error("❌ pH melebihi baku mutu")

    # ==============================================
    # COD
    # ==============================================

    elif parameter == "COD":

        blanko = st.number_input(
            "Volume blanko",
            min_value=0.0,
            key="limbah_blanko"
        )

        sampel = st.number_input(
            "Volume sampel",
            min_value=0.0,
            key="limbah_sampel"
        )

        normalitas = st.number_input(
            "Normalitas",
            min_value=0.0,
            key="limbah_normalitas"
        )

        volume = st.number_input(
            "Volume sampel air",
            min_value=0.0,
            key="limbah_volume"
        )

        if st.button("Hitung COD Limbah"):

            cod = ((blanko - sampel) * normalitas * 8000) / volume

            st.success(f"COD = {cod:.2f} mg/L")

    # ==============================================
    # BOD
    # ==============================================

    elif parameter == "BOD":

        do_awal = st.number_input(
            "DO awal",
            min_value=0.0,
            key="limbah_bod_awal"
        )

        do_akhir = st.number_input(
            "DO akhir",
            min_value=0.0,
            key="limbah_bod_akhir"
        )

        if st.button("Hitung BOD Limbah"):

            bod = do_awal - do_akhir

            st.success(f"BOD = {bod:.2f} mg/L")

    # ==============================================
    # AMONIA
    # ==============================================

    elif parameter == "Amonia":

        konsentrasi = st.number_input(
            "Masukkan konsentrasi amonia",
            min_value=0.0
        )

        if st.button("Evaluasi Amonia"):

            st.success(f"Amonia = {konsentrasi:.2f} mg/L")

            if konsentrasi <= 10:
                st.success("✅ Memenuhi baku mutu")
            else:
                st.error("❌ Melebihi baku mutu")

# =====================================================
# UPLOAD EXCEL
# =====================================================

elif menu == "Upload Data Excel":

    st.header("📂 Upload Data Hasil Sampling")

    file = st.file_uploader(
        "Upload file Excel",
        type=["xlsx"],
        key="upload_excel"
    )

    if file is not None:

        data = pd.read_excel(file)

        st.subheader("Data Praktikum")

        st.dataframe(data)

        st.subheader("Statistik")

        st.write(data.describe())

        fig = px.histogram(data)

        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# STATISTIK
# =====================================================

elif menu == "Statistik & Grafik":

    st.header("📈 Statistik & Grafik")

    parameter = ["pH", "COD", "BOD", "TSS"]
    nilai = [7, 80, 20, 40]

    df = pd.DataFrame({
        "Parameter": parameter,
        "Nilai": nilai
    })

    fig = px.line(
        df,
        x="Parameter",
        y="Nilai",
        markers=True,
        title="Trend Parameter"
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# EXPORT PDF
# =====================================================

elif menu == "Export PDF":

    st.header("📄 Export Laporan PDF")

    lokasi = st.text_input("Nama Lokasi")

    hasil = st.text_area("Ringkasan Hasil")

    if st.button("Buat PDF"):

        doc = SimpleDocTemplate("laporan_waterlab.pdf")

        styles = getSampleStyleSheet()

        content = []

        content.append(
            Paragraph("Laporan Analisis Air", styles['Title'])
        )

        content.append(
            Paragraph(f"Lokasi: {lokasi}", styles['Normal'])
        )

        content.append(
            Paragraph(f"Hasil: {hasil}", styles['Normal'])
        )

        doc.build(content)

        with open("laporan_waterlab.pdf", "rb") as pdf_file:
            PDFbyte = pdf_file.read()

        st.download_button(
            label="Download PDF",
            data=PDFbyte,
            file_name="laporan_waterlab.pdf",
            mime='application/octet-stream'
        )

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from datetime import date
import time

# ═══════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════

st.set_page_config(page_title="HydroLisis", layout="wide")

# ═══════════════════════════════════════════════════════
# INIT SESSION STATE
# ═══════════════════════════════════════════════════════

if "sampel_list" not in st.session_state:
    st.session_state["sampel_list"] = []

if "counter" not in st.session_state:
    st.session_state["counter"] = 1

# Temp values untuk setiap parameter (None = belum dihitung)
for k in ["v_tss", "v_cod_ap", "v_bod_ap", "v_tds",
          "v_ph",  "v_cod_al", "v_bod_al"]:
    if k not in st.session_state:
        st.session_state[k] = None

# ═══════════════════════════════════════════════════════
# KONSTANTA BAKU MUTU
# ═══════════════════════════════════════════════════════

BAKU_MUTU = {
    "TSS":    ("≤ 50 mg/L",   lambda v: v <= 50),
    "COD":    ("≤ 100 mg/L",  lambda v: v <= 100),
    "BOD":    ("≤ 30 mg/L",   lambda v: v <= 30),
    "TDS":    ("≤ 500 mg/L",  lambda v: v <= 500),
    "DO":     ("≥ 4 mg/L",    lambda v: v >= 4),
    "pH":     ("6.0 – 9.0",   lambda v: 6.0 <= v <= 9.0),
}

# Penjelasan Tiap Parameter #
PENJELASAN_PARAM = {
    "TSS": (
        "**TSS (Total Suspended Solids)** adalah jumlah padatan tersuspensi (tidak terlarut) "
        "dalam air, seperti lumpur, pasir halus, atau sisa organik. Nilai TSS yang tinggi "
        "menyebabkan air menjadi keruh dan dapat mengganggu kehidupan biota air karena "
        "menghalangi cahaya matahari masuk ke dalam air."
    ),
    "COD": (
        "**COD (Chemical Oxygen Demand)** mengukur jumlah oksigen yang dibutuhkan untuk "
        "mengoksidasi seluruh bahan organik dan anorganik secara kimiawi dalam air. "
        "Nilai COD yang tinggi menunjukkan tingkat pencemaran bahan organik/kimia yang besar."
    ),
    "BOD": (
        "**BOD₅ (Biochemical Oxygen Demand)** mengukur jumlah oksigen yang dibutuhkan oleh "
        "mikroorganisme untuk menguraikan bahan organik dalam air selama 5 hari. "
        "Nilai BOD yang tinggi mengindikasikan banyaknya bahan organik yang dapat terurai "
        "secara biologis, yang juga menguras kadar oksigen terlarut di dalam air."
    ),
    "TDS": (
        "**TDS (Total Dissolved Solids)** adalah jumlah total zat padat yang **terlarut** "
        "dalam air, meliputi garam mineral, ion logam, dan senyawa terlarut lainnya. "
        "TDS berbeda dengan TSS karena TDS mengukur partikel yang larut, bukan tersuspensi."
    ),
    "DO": (
        "**DO (Dissolved Oxygen)** adalah kadar oksigen terlarut dalam air yang dibutuhkan "
        "oleh organisme akuatik (ikan, plankton, mikroorganisme) untuk respirasi. "
        "Berbeda dengan parameter lain, semakin **tinggi** nilai DO maka kualitas air "
        "semakin **baik** — nilai DO yang rendah menandakan air kekurangan oksigen akibat "
        "pencemaran bahan organik berlebih."
    ),
    "pH": (
        "**pH** menunjukkan tingkat keasaman atau kebasaan air pada skala 0–14. "
        "Air dengan pH terlalu rendah (asam) atau terlalu tinggi (basa) dapat merusak "
        "ekosistem perairan dan bersifat korosif terhadap material di sekitarnya."
    ),
}
# ═══════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════

def cek_status(param: str, nilai: float) -> str:
    if param in BAKU_MUTU:
        return "✅ Memenuhi Regulasi Perairan kelas II" if BAKU_MUTU[param][1](nilai) else "❌ Melebihi Regulasi Perairan kelas II"
    return "-"


def simpan_ke_tabel(lokasi: str, tanggal, tipe: str, param: str, nilai: float):
    status = cek_status(param, nilai)
    bm_str = BAKU_MUTU.get(param, ("-", None))[0]
    st.session_state["sampel_list"].append({
        "ID":        st.session_state["counter"],
        "Tanggal":   str(tanggal),
        "Lokasi":    lokasi,
        "Tipe Air":  tipe,
        "Parameter": param,
        "Nilai":     round(nilai, 3),
        "Baku Mutu": bm_str,
        "Status":    status,
    })
    st.session_state["counter"] += 1


def get_df() -> pd.DataFrame:
    if st.session_state["sampel_list"]:
        return pd.DataFrame(st.session_state["sampel_list"])
    return pd.DataFrame(
        columns=["ID", "Tanggal", "Lokasi", "Tipe Air",
                 "Parameter", "Nilai", "Baku Mutu", "Status"]
    )


def show_result_and_save(val_key: str, param: str, tipe: str, lok: str, tgl):
    """
    Tampilkan hasil perhitungan + tombol Simpan ke Tabel.
    Dipakai di semua halaman parameter agar konsisten.
    """
    nilai = st.session_state.get(val_key)
    if nilai is None:
        return

    status   = cek_status(param, nilai)
    bm_str   = BAKU_MUTU.get(param, ("-", None))[0]
    satuan   = "" if param == "pH" else " mg/L"
    label    = f"**{param} = {nilai:.3f}{satuan}** — {status}  (Baku Mutu: {bm_str})"

    st.markdown("---")
    col_res, col_btn = st.columns([4, 1])
    with col_res:
        if status == "✅ Memenuhi Regulasi Perairan kelas II":
            st.success(label)
        else:
            st.error(label)
    with col_btn:
        if st.button("💾 Simpan ke Tabel", key=f"save_{val_key}"):
            if not lok:
                st.warning("⚠️ Isi nama lokasi terlebih dahulu.")
            else:
                simpan_ke_tabel(lok, tgl, tipe, param, nilai)
                st.session_state[val_key] = None
                st.toast("✅ Data berhasil disimpan!", icon="✅")
                st.rerun()


def info_sampel_expander(prefix: str):
    """Widget lokasi + tanggal yang konsisten di semua menu."""
    with st.expander("📋 Informasi Sampel", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            lok = st.text_input("Nama Lokasi / Sumber Air", key=f"{prefix}_lok")
        with c2:
            tgl = st.date_input("Tanggal Sampling", value=date.today(), key=f"{prefix}_tgl")
    return lok, tgl

# =====================================================
# LOADING SCREEN
# =====================================================

placeholder = st.empty()

with placeholder.container():

    st.markdown(
        """
        <h1 style='text-align: center; color: #0099FF;'>
        💧 HydroLisis
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <h4 style='text-align: center; color: #102A43;'>
        Sistem Monitoring Kualitas Air Berbasis Python
        </h4>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
    """
    <div style='text-align:center;'>
        <img src='https://media3.giphy.com/media/v1.Y2lkPTZjMDliOTUyNzZlZXF3NG0xem04czd1N2I3bmM0MGQ0NGYwbzhwYjFsY3hiZXprYSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/5bCYrRAZ3b5HtQ5HuJ/giphy.gif' width='250'>
    </div>
    """,
    unsafe_allow_html=True
)

    st.info("🚀 Initializing HydroLisis...")

    progress_bar = st.progress(0)

    for i in range(100):
        time.sleep(0.02)
        progress_bar.progress(i + 1)

    st.success("System Ready!")

    time.sleep(1)

placeholder.empty()

# ═══════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════

st.markdown("""
<style>

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #E0F7FA, #B2EBF2, 90E0EF);
    border-top-right-radius: 25px;
    border-bottom-right-radius: 25px;
    padding-top: 20px;
}

/* SIDEBAR TITLE */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #0077B6;
}

/* SELECTBOX */
div[data-baseweb="select"] {
    background-color: white;
    border-radius: 18px;
    border: 2px solid #90E0EF;
    padding: 2px;
}

/* MENU BOX */
.stSelectbox {
    background-color: transparent;
    border-radius: 20px;
    padding: 5px;
}

/* BUTTON */
.stButton > button {
    border-radius: 20px;
    background: linear-gradient(90deg, #0099FF, #00C6FF);
    color: white;
    border: none;
    font-weight: bold;
    transition: 0.3s;
}

/* HOVER BUTTON */
.stButton > button:hover {
    transform: scale(1.03);
    box-shadow: 0px 0px 12px rgba(0,153,255,0.4);
}

/* METRIC CARD */
[data-testid="metric-container"] {
    background-color: white;
    border-radius: 20px;
    padding: 10px;
    border: 1px solid #CDEFFF;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
}

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════

st.markdown("""
<div style="text-align: center; padding: 1.2rem 0 0.5rem 0;">
    <h1 style="color:#0099FF; font-size:2.8rem; margin-bottom:0.2rem;">💧 HydroLisis</h1>
    <p style="color:#4A6FA5; font-size:1rem; margin-top:0;">
        Program Analisis Kualitas Air — Air Permukaan &amp; Air Limbah<br>
        <strong>POLITEKNIK AKA BOGOR</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Kreator Web #
def footer():

    st.markdown("""
    <hr>

    <div style="text-align:center; padding:10px">

    <h4 style="margin-bottom:0;">HydroLisis</h4>

    <p style="color:gray;">
    Developed by <b>Kelompok 10</b><br>
    Program Studi Logika Pemrograman Komputer
    Politeknik AKA Bogor
    </p>

    <p style="font-size:13px;color:#888;">
    Mutiara Rahma Hidayati (2560694) • Nessa Amelia (2560723) • Raihan Surya Isnandar (2560744) • Rusmaya Trisya Amanda (2560765) • Sri Deva (2560788)
    </p>

    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# SIDEBAR MENU
# ═══════════════════════════════════════════════════════

menu = st.sidebar.selectbox("Pilih Menu", [
    "Dashboard",
    "Air Permukaan",
    "Air Limbah",
    "Tabel Sampel",
    "Statistik & Grafik",
    "Export PDF",
])

st.sidebar.markdown("---")
st.sidebar.metric("Total Sampel Tersimpan", len(st.session_state["sampel_list"]))

st.sidebar.markdown("---")

st.sidebar.info("""
👨‍💻 Creator

Mutiara R. H.

Nessa A.

Raihan S. I.

Rusmaya T. A.

Sri Deva
""")

# ═══════════════════════════════════════════════════════
# 1 ── DASHBOARD
# ═══════════════════════════════════════════════════════

if menu == "Dashboard":

    st.header("🏠 Dashboard")

     # ── Tentang Aplikasi ──────────────────────────────
    with st.expander("ℹ️ Tentang HydroLisis", expanded=True):
 
        st.markdown("""
        ### 🎯 Tujuan Aplikasi
        **HydroLisis** adalah program berbasis web yang dirancang untuk membantu mahasiswa maupun
        praktisi laboratorium di **Politeknik AKA Bogor** dalam melakukan analisis dan pemantauan
        kualitas air secara sistematis. Aplikasi ini juga merupakan bagian dari projek mata kuliah **Logika Pemrograman Komputer**.
        Pada aplikasi ini pengguna bisa:
        - Menghitung parameter kualitas air dari data hasil sampling
        - Membandingkan hasil pengukuran dengan **baku mutu** perairan kelas II yang berlaku (PP No. 22 Tahun 2021 dan PermenLHK No. P.68 Tahun 2016)
        - Menyimpan dan mengelola data dari **beberapa lokasi dan waktu sampling**
        - Menghasilkan laporan PDF yang siap cetak
        """)

        st.markdown("---")
 
        col_ap, col_al = st.columns(2)
 
        with col_ap:
            st.markdown("""
            ### 🌊 Air Permukaan
            Air permukaan adalah air yang berada di atas permukaan tanah, meliputi
            **sungai, danau, waduk, rawa**, dan badan air terbuka lainnya.
            Air ini merupakan sumber utama baku air minum dan irigasi, namun rentan
            terhadap pencemaran dari aktivitas manusia di sekitarnya.
 
            **Parameter yang dianalisis:**
            | Parameter | Satuan | Baku Mutu |
            |-----------|--------|-----------|
            | TSS (Total Suspended Solids) | mg/L | ≤ 50 |
            | COD (Chemical Oxygen Demand) | mg/L | ≤ 100 |
            | BOD (Biochemical Oxygen Demand) | mg/L | ≤ 30 |
            | TDS (Total Dissolved Solids) | mg/L | ≤ 500 |
            | DO (Dissolved Oxygen) | mg/L | ≥ 4 |

            > 📋 Referensi: **PP No. 22 Tahun 2021** tentang Penyelenggaraan
            Perlindungan dan Pengelolaan Lingkungan Hidup
            """)

        with col_al:
            st.markdown("""
            ### 🏭 Air Limbah
            Air limbah adalah air buangan yang dihasilkan dari kegiatan industri,
            rumah tangga, pertanian, maupun fasilitas umum. Air limbah mengandung
            berbagai zat pencemar yang harus diolah terlebih dahulu sebelum
            dibuang ke badan air penerima.
 
            **Parameter yang dianalisis:**
            | Parameter | Satuan | Baku Mutu |
            |-----------|--------|-----------|
            | pH | - | 6.0 – 9.0 |
            | COD (Chemical Oxygen Demand) | mg/L | ≤ 100 |
            | BOD (Biochemical Oxygen Demand) | mg/L | ≤ 30 |
 
            > 📋 Referensi: **PermenLHK No. P.68 Tahun 2016** tentang
            Baku Mutu Air Limbah Domestik
            """)

    st.markdown("---")

     # ── Cara Penggunaan ───────────────────────────────
    with st.expander("📖 Cara Penggunaan Aplikasi"):
        st.markdown("""
        Ikuti langkah-langkah berikut untuk menggunakan **HydroLysis**:
 
        ---
 
        #### 1️⃣ Input Data Sampling
        - Buka menu **Air Permukaan** atau **Air Limbah** di sidebar kiri
        - Isi **Nama Lokasi** dan **Tanggal Sampling** pada bagian *Informasi Sampel*
        - Pilih parameter yang ingin dihitung (TSS, COD, BOD, dll.)
        - Masukkan data hasil pengukuran laboratorium ke dalam field yang tersedia
        - Klik tombol **Hitung** untuk memproses nilai
 
        ---
 
        #### 2️⃣ Simpan ke Tabel
        - Setelah hasil muncul, klik tombol **💾 Simpan ke Tabel**
        - Data akan tersimpan otomatis beserta status kepatuhan baku mutu
        - Ulangi langkah 1–2 untuk setiap sampel atau parameter yang berbeda
 
        ---
 
        #### 3️⃣ Kelola Data di Tabel Sampel
        - Buka menu **Tabel Sampel** untuk melihat seluruh data yang telah disimpan
        - Gunakan fitur **Tambah Baris Manual** jika ingin menambah data tanpa perhitungan
        - Hapus data per baris menggunakan **ID**, atau hapus semua sekaligus
 
        ---
 
        #### 4️⃣ Analisis di Statistik & Grafik
        - Buka menu **Statistik & Grafik** untuk melihat visualisasi data
        - Gunakan **filter** Tipe Air dan Parameter untuk memfokuskan analisis
        - Tersedia: grafik batang, keterangan waktu dan lokasi, serta statistik deskriptif
 
        ---
 
        #### 5️⃣ Ekspor Laporan
        - Buka menu **Export PDF**
        - Isi nama instansi, nama analis, dan keterangan tambahan
        - Klik **Buat & Download PDF** — laporan berisi seluruh tabel data akan diunduh otomatis
 
        ---
 
        > ⚠️ **Catatan:** Data hanya tersimpan selama sesi berlangsung. Jika halaman di-refresh
        > atau browser ditutup, data akan hilang. Pastikan mengunduh laporan PDF sebelum menutup aplikasi.
        """)
 
    st.markdown("---")

    # ── Monitoring data ───────────────────────────────
    df = get_df()
 
    if df.empty:
        st.info("Belum ada data. Mulai input di menu **Air Permukaan** atau **Air Limbah**.")
        st.stop()
 
    total     = len(df)
    memenuhi  = (df["Status"] == "✅ Memenuhi Baku Mutu Perairan Kelas II").sum()
    melebihi  = (df["Status"] == "❌ Melebihi Baku Mutu Perairan Kelas II").sum()
 
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Pengukuran",       total)
    m2.metric("✅ Memenuhi Baku Mutu Perairan Kelas II",  memenuhi)
    m3.metric("❌ Melebihi Baku Mutu Perairan Kelas II",  melebihi)
 
    st.markdown("---")
    col_a, col_b = st.columns(2)
 
    with col_a:
        avg_df = df.groupby("Parameter")["Nilai"].mean().reset_index()
        avg_df.columns = ["Parameter", "Rata-rata Nilai"]
        fig1 = px.bar(
            avg_df, x="Parameter", y="Rata-rata Nilai",
            color="Parameter", text_auto=".2f",
            title="Rata-rata Nilai per Parameter"
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
 
    with col_b:
        pie_df = df["Status"].value_counts().reset_index()
        pie_df.columns = ["Status", "Jumlah"]
        fig2 = px.pie(
            pie_df, names="Status", values="Jumlah",
            title="Kepatuhan Baku Mutu",
            color="Status",
            color_discrete_map={"✅ Memenuhi Baku Mutu Perairan Kelas II": "#00CC66", "❌ Melebihi Baku Mutu Perairan Kelas II": "#FF4444"}
        )
        st.plotly_chart(fig2, use_container_width=True)
 
    st.subheader("10 Data Terbaru")
    st.dataframe(df.tail(10), use_container_width=True)

    footer()
# ═══════════════════════════════════════════════════════
# 2 ── AIR PERMUKAAN
# ═══════════════════════════════════════════════════════

elif menu == "Air Permukaan":

    st.header("🌊 Analisis Air Permukaan")
    lok, tgl = info_sampel_expander("ap")

    submenu = st.selectbox("Pilih Parameter", ["TSS", "COD", "BOD", "TDS", "DO"])

    with st.expander(f"ℹ️ Apa itu {submenu}?"):
        st.markdown(PENJELASAN_PARAM[submenu])

    # ── TSS ──────────────────────────────────────────
    if submenu == "TSS":
        st.subheader("Perhitungan TSS")
        st.latex(r"\text{TSS} = \frac{(\text{Berat Akhir} - \text{Berat Awal}) \times 1000}{\text{Volume Sampel}}")

        ba = st.number_input("Berat filter awal (mg)",  min_value=0.0, key="tss_ba")
        bk = st.number_input("Berat filter akhir (mg)", min_value=0.0, key="tss_bk")
        vol = st.number_input("Volume sampel (mL)",     min_value=0.1, value=100.0, key="tss_vol")

        if st.button("Hitung TSS"):
            if vol <= 0:
                st.error("Volume sampel harus > 0 mL.")
            else:
                st.session_state["v_tss"] = ((bk - ba) * 1000) / vol

        show_result_and_save("v_tss", "TSS", "Air Permukaan", lok, tgl)
   
    # ── COD ──────────────────────────────────────────
    elif submenu == "COD":
        st.subheader("Perhitungan COD")
        st.latex(r"\text{COD} = \frac{(V_{\text{blanko}} - V_{\text{sampel}}) \times N \times 8000}{V_{\text{air}}}")

        v_blanko  = st.number_input("Volume titrasi blanko (mL)",  min_value=0.0, key="cod_ap_bl")
        v_sampel  = st.number_input("Volume titrasi sampel (mL)",  min_value=0.0, key="cod_ap_sp")
        normalitas = st.number_input("Normalitas FAS",             min_value=0.0, key="cod_ap_n")
        v_air      = st.number_input("Volume sampel air (mL)",     min_value=0.1, value=25.0, key="cod_ap_vol")

        if st.button("Hitung COD"):
            if v_air <= 0:
                st.error("Volume sampel air harus > 0 mL.")
            else:
                st.session_state["v_cod_ap"] = ((v_blanko - v_sampel) * normalitas * 8000) / v_air

        show_result_and_save("v_cod_ap", "COD", "Air Permukaan", lok, tgl)
    
    # ── BOD ──────────────────────────────────────────
    elif submenu == "BOD":
        st.subheader("Perhitungan BOD₅")
        st.latex(r"\text{BOD}_5 = (\text{DO}_{\text{awal}} - \text{DO}_{\text{akhir}}) \times P")
        st.caption("P = Faktor Pengenceran (1 jika tidak ada pengenceran)")

        do_awal  = st.number_input("DO Awal (mg/L)",       min_value=0.0, key="bod_ap_da")
        do_akhir = st.number_input("DO Akhir (mg/L)",      min_value=0.0, key="bod_ap_dk")
        fp       = st.number_input("Faktor Pengenceran (P)", min_value=1.0, value=1.0, key="bod_ap_fp")

        if st.button("Hitung BOD"):
            st.session_state["v_bod_ap"] = (do_awal - do_akhir) * fp

        show_result_and_save("v_bod_ap", "BOD", "Air Permukaan", lok, tgl)
   
    # ── TDS ──────────────────────────────────────────
    elif submenu == "TDS":
        st.subheader("Perhitungan TDS")
        st.latex(r"\text{TDS} = \frac{(\text{Berat Cawan Akhir} - \text{Berat Cawan Awal}) \times 1000}{\text{Volume Sampel}}")

        ba  = st.number_input("Berat cawan awal (mg)",  min_value=0.0, key="tds_ba")
        bk  = st.number_input("Berat cawan akhir (mg)", min_value=0.0, key="tds_bk")
        vol = st.number_input("Volume sampel (mL)",     min_value=0.1, value=100.0, key="tds_vol")

        if st.button("Hitung TDS"):
            if vol <= 0:
                st.error("Volume sampel harus > 0 mL.")
            else:
                st.session_state["v_tds"] = ((bk - ba) * 1000) / vol

        show_result_and_save("v_tds", "TDS", "Air Permukaan", lok, tgl)
  
    # ── DO ───────────────────────────────────────────
    elif submenu == "DO":
        st.subheader("Pengukuran DO (Dissolved Oxygen)")
        st.caption(
            "Nilai DO umumnya dibaca langsung menggunakan **DO meter** di lokasi sampling, "
            "atau dihitung melalui metode titrasi Winkler di laboratorium."
        )

        do_terukur = st.number_input(
            "Nilai DO terukur (mg/L)", min_value=0.0, step=0.01, key="do_ap_val"
        )

        if st.button("Catat DO"):
            st.session_state["v_do"] = do_terukur

        show_result_and_save("v_do", "DO", "Air Permukaan", lok, tgl)
        
    footer()
# ═══════════════════════════════════════════════════════
# 3 ── AIR LIMBAH
# ═══════════════════════════════════════════════════════

elif menu == "Air Limbah":

    st.header("🏭 Analisis Air Limbah")
    lok, tgl = info_sampel_expander("al")

    parameter = st.selectbox("Pilih Parameter", ["pH", "COD", "BOD"])

    with st.expander(f"ℹ️ Apa itu {parameter}?"):
        st.markdown(PENJELASAN_PARAM[parameter])

    # ── pH ───────────────────────────────────────────
    if parameter == "pH":
        st.subheader("Evaluasi pH")

        ph_val = st.number_input("Masukkan nilai pH", min_value=0.0, max_value=14.0, step=0.01)

        if st.button("Evaluasi pH"):
            st.session_state["v_ph"] = ph_val

        show_result_and_save("v_ph", "pH", "Air Limbah", lok, tgl)

    # ── COD ──────────────────────────────────────────
    elif parameter == "COD":
        st.subheader("Perhitungan COD Limbah")
        st.latex(r"\text{COD} = \frac{(V_{\text{blanko}} - V_{\text{sampel}}) \times N \times 8000}{V_{\text{air}}}")

        v_blanko   = st.number_input("Volume titrasi blanko (mL)",  min_value=0.0, key="cod_al_bl")
        v_sampel   = st.number_input("Volume titrasi sampel (mL)",  min_value=0.0, key="cod_al_sp")
        normalitas = st.number_input("Normalitas FAS",              min_value=0.0, key="cod_al_n")
        v_air      = st.number_input("Volume sampel air (mL)",      min_value=0.1, value=25.0, key="cod_al_vol")

        if st.button("Hitung COD Limbah"):
            if v_air <= 0:
                st.error("Volume sampel air harus > 0 mL.")
            else:
                st.session_state["v_cod_al"] = ((v_blanko - v_sampel) * normalitas * 8000) / v_air

        show_result_and_save("v_cod_al", "COD", "Air Limbah", lok, tgl)

    # ── BOD ──────────────────────────────────────────
    elif parameter == "BOD":
        st.subheader("Perhitungan BOD₅ Limbah")
        st.latex(r"\text{BOD}_5 = (\text{DO}_{\text{awal}} - \text{DO}_{\text{akhir}}) \times P")

        do_awal  = st.number_input("DO Awal (mg/L)",         min_value=0.0, key="bod_al_da")
        do_akhir = st.number_input("DO Akhir (mg/L)",        min_value=0.0, key="bod_al_dk")
        fp       = st.number_input("Faktor Pengenceran (P)", min_value=1.0, value=1.0, key="bod_al_fp")

        if st.button("Hitung BOD Limbah"):
            st.session_state["v_bod_al"] = (do_awal - do_akhir) * fp

        show_result_and_save("v_bod_al", "BOD", "Air Limbah", lok, tgl)
        
    footer()
# ═══════════════════════════════════════════════════════
# 4 ── TABEL SAMPEL
# ═══════════════════════════════════════════════════════

elif menu == "Tabel Sampel":

    st.header("📋 Tabel Multi-Sampel")

    df = get_df()

    if df.empty:
        st.info("Belum ada data. Input di menu Air Permukaan atau Air Limbah, lalu tekan **💾 Simpan ke Tabel**.")
        st.stop()

    # ── Tampilkan tabel dengan warna status ──────────
    def highlight_status(val):
        if val == "✅ Memenuhi Baku Mutu":
            return "background-color:#d4edda; color:#155724"
        elif val == "❌ Melebihi Baku Mutu":
            return "background-color:#f8d7da; color:#721c24"
        return ""

    st.dataframe(
        df.style.map(highlight_status, subset=["Status"]),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # ── Input manual tambahan ─────────────────────────
    with st.expander("➕ Tambah Baris Manual"):
        c1, c2, c3 = st.columns(3)
        with c1:
            m_lokasi  = st.text_input("Lokasi",    key="manual_lok")
            m_tipe    = st.selectbox("Tipe Air",   ["Air Permukaan","Air Limbah"], key="manual_tipe")
        with c2:
            m_tanggal = st.date_input("Tanggal",   value=date.today(), key="manual_tgl")
            m_param   = st.selectbox("Parameter",  list(BAKU_MUTU.keys()), key="manual_param")
        with c3:
            m_nilai   = st.number_input("Nilai",   min_value=0.0, key="manual_nilai")
            st.write("")
            st.write("")
            if st.button("➕ Tambah ke Tabel"):
                if not m_lokasi:
                    st.warning("Isi nama lokasi.")
                else:
                    simpan_ke_tabel(m_lokasi, m_tanggal, m_tipe, m_param, m_nilai)
                    st.success("✅ Baris berhasil ditambahkan.")
                    st.rerun()

    st.markdown("---")

    # ── Hapus data ────────────────────────────────────
    col_del1, col_del2 = st.columns(2)

    with col_del1:
        id_hapus = st.number_input("Hapus baris berdasarkan ID", min_value=1, step=1)
        if st.button("🗑️ Hapus Baris"):
            sebelum = len(st.session_state["sampel_list"])
            st.session_state["sampel_list"] = [
                s for s in st.session_state["sampel_list"] if s["ID"] != id_hapus
            ]
            sesudah = len(st.session_state["sampel_list"])
            if sebelum > sesudah:
                st.success(f"Baris ID {id_hapus} berhasil dihapus.")
            else:
                st.warning(f"ID {id_hapus} tidak ditemukan.")
            st.rerun()

    with col_del2:
        st.write("")
        st.write("")
        if st.button("🗑️ Hapus Semua Data", type="primary"):
            st.session_state["sampel_list"] = []
            st.session_state["counter"] = 1
            st.success("Semua data berhasil dihapus.")
            st.rerun()
    footer()

# ═══════════════════════════════════════════════════════
# 5 ── STATISTIK & GRAFIK
# ═══════════════════════════════════════════════════════

elif menu == "Statistik & Grafik":

    st.header("📈 Statistik & Grafik")

    df = get_df()

    if df.empty:
        st.info("Belum ada data sampel tersimpan.")
        st.stop()

    # ── Filter ────────────────────────────────────────
    with st.expander("🔍 Filter Data", expanded=True):
        f1, f2 = st.columns(2)
        with f1:
            f_tipe = st.multiselect(
                "Tipe Air",
                options=df["Tipe Air"].unique().tolist(),
                default=df["Tipe Air"].unique().tolist()
            )
        with f2:
            f_param = st.multiselect(
                "Parameter",
                options=df["Parameter"].unique().tolist(),
                default=df["Parameter"].unique().tolist()
            )

    df_f = df[df["Tipe Air"].isin(f_tipe) & df["Parameter"].isin(f_param)]

    if df_f.empty:
        st.warning("Tidak ada data untuk filter yang dipilih.")
        st.stop()

    st.markdown("---")

    # ── Chart 1: Bar per parameter & lokasi ──────────
    fig1 = px.bar(
        df_f, x="Parameter", y="Nilai",
        color="Lokasi", barmode="group",
        text_auto=".2f",
        title="Nilai per Parameter & Lokasi",
        labels={"Nilai": "Nilai (mg/L)"}
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ── Chart 2: Tren waktu ───────────────────────────
    fig2 = px.line(
        df_f.sort_values("Tanggal"),
        x="Tanggal", y="Nilai",
        color="Parameter", markers=True,
        symbol="Lokasi",
        title="Tren Nilai per Tanggal",
        labels={"Nilai": "Nilai (mg/L)"},
        hover_data=["Lokasi", "Tipe Air", "Status"]
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Chart 3: Kepatuhan per lokasi ─────────────────
    status_df = (
        df_f.groupby(["Lokasi", "Status"])
            .size()
            .reset_index(name="Jumlah")
    )
    fig3 = px.bar(
        status_df, x="Lokasi", y="Jumlah",
        color="Status", barmode="stack",
        title="Kepatuhan Baku Mutu per Lokasi",
        color_discrete_map={"✅ Memenuhi Baku Mutu Perairan Kelas II": "#00CC66", "❌ Melebihi Baku Mutu Perairan Kelas II": "#FF4444"}
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Statistik deskriptif ──────────────────────────
    st.subheader("📐 Statistik Deskriptif per Parameter")
    desc = df_f.groupby("Parameter")["Nilai"].describe().round(3)
    desc.columns = ["N", "Mean", "Std Dev", "Min", "Q1 (25%)", "Median", "Q3 (75%)", "Max"]
    st.dataframe(desc, use_container_width=True)

    footer()
# ═══════════════════════════════════════════════════════
# 6 ── EXPORT PDF
# ═══════════════════════════════════════════════════════

elif menu == "Export PDF":
 
    st.header("📄 Export Laporan PDF")
 
    instansi   = st.text_input("Nama Instansi / Judul Laporan")
    analis     = st.text_input("Nama Analis")
    ket_tambahan = st.text_area("Keterangan Tambahan (opsional)")
 
    if st.button("Buat & Download PDF"):
 
        df = get_df()
 
        doc = SimpleDocTemplate(
            "laporan_hydrolysis.pdf",
            pagesize=A4,
            rightMargin=30, leftMargin=30,
            topMargin=40,   bottomMargin=30
        )
 
        styles  = getSampleStyleSheet()
        content = []
 
        # ── Header ──
        content.append(Paragraph("LAPORAN ANALISIS KUALITAS AIR", styles["Title"]))
        content.append(Spacer(1, 8))
        content.append(Paragraph("POLITEKNIK AKA BOGOR — HydroLysis", styles["Heading2"]))
        content.append(Spacer(1, 12))
        content.append(Paragraph(f"Instansi : {instansi or '-'}", styles["Normal"]))
        content.append(Paragraph(f"Analis   : {analis   or '-'}", styles["Normal"]))
        content.append(Paragraph(f"Tanggal  : {date.today()}", styles["Normal"]))
        if ket_tambahan:
            content.append(Paragraph(f"Keterangan: {ket_tambahan}", styles["Normal"]))
        content.append(Spacer(1, 16))
 
        # ── Tabel data ──
        if df.empty:
            content.append(Paragraph("Tidak ada data sampel tersimpan.", styles["Normal"]))
        else:
            header = [str(c) for c in df.columns.tolist()]
            rows   = [[str(v) for v in row] for row in df.values.tolist()]
            table_data = [header] + rows
 
            t = Table(table_data, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1,  0), colors.HexColor("#0099FF")),
                ("TEXTCOLOR",     (0, 0), (-1,  0), colors.white),
                ("FONTNAME",      (0, 0), (-1,  0), "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1), 7),
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF4FF")]),
                ("GRID",          (0, 0), (-1, -1), 0.4, colors.grey),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            content.append(t)
 
        # ── Kesimpulan ──
        if not df.empty:
            content.append(Spacer(1, 20))
            content.append(Paragraph("KESIMPULAN HASIL ANALISIS KUALITAS AIR", styles["Heading2"]))
            content.append(Spacer(1, 8))
 
            # Referensi regulasi per tipe air
            REGULASI = {
                "Air Permukaan": "PP No. 22 Tahun 2021 tentang Penyelenggaraan Perlindungan dan Pengelolaan Lingkungan Hidup",
                "Air Limbah":    "PermenLHK No. P.68/Menlhk/Setjen/Kum.1/8/2016 tentang Baku Mutu Air Limbah Domestik",
            }
 
            # Baku mutu nilai numerik untuk kesimpulan
            BM_NUM = {
                "TSS":    ("≤ 50 mg/L",   50,   "le"),
                "COD":    ("≤ 100 mg/L",  100,  "le"),
                "BOD":    ("≤ 30 mg/L",   30,   "le"),
                "TDS":    ("≤ 500 mg/L",  500,  "le"),
                "DO":     ("≥ 4 mg/L",    4,    "ge"),
                "pH":     ("6.0 – 9.0",   (6.0, 9.0), "range"),
            }
 
            def status_param(param, nilai):
                if param not in BM_NUM:
                    return "Memenuhi"
                _, bm, mode = BM_NUM[param]
                if mode == "le":
                    return "Memenuhi" if nilai <= bm else "Melebihi"
                elif mode == "range":
                    lo, hi = bm
                    return "Memenuhi" if lo <= nilai <= hi else "Melebihi"
                return "Memenuhi"
 
            # Kelompokkan per tipe air lalu per lokasi
            for tipe in df["Tipe Air"].unique():
                df_tipe = df[df["Tipe Air"] == tipe]
                regulasi = REGULASI.get(tipe, "-")
 
                content.append(Spacer(1, 10))
                content.append(Paragraph(f"A. {tipe}", styles["Heading3"]))
                content.append(Paragraph(
                    f"Dasar hukum penilaian: {regulasi}",
                    styles["Italic"]
                ))
                content.append(Spacer(1, 6))
 
                for lokasi in df_tipe["Lokasi"].unique():
                    df_lok = df_tipe[df_tipe["Lokasi"] == lokasi]
                    params_melebihi = []
                    params_memenuhi = []
 
                    for _, row in df_lok.iterrows():
                        param = row["Parameter"]
                        nilai = row["Nilai"]
                        bm_str = BM_NUM.get(param, ("-", None, None))[0]
                        st_text = status_param(param, nilai)
                        entry = f"{param} = {nilai:.3f} (Baku Mutu: {bm_str})"
                        if st_text == "Melebihi":
                            params_melebihi.append(entry)
                        else:
                            params_memenuhi.append(entry)
 
                    semua_memenuhi = len(params_melebihi) == 0
 
                    # Header lokasi
                    content.append(Paragraph(
                        f"Lokasi: {lokasi}",
                        styles["Heading4"]
                    ))
 
                    # Tabel ringkasan per lokasi
                    lok_header = ["Parameter", "Nilai", "Baku Mutu", "Status"]
                    lok_rows   = [
                        [
                            row["Parameter"],
                            f"{row['Nilai']:.3f}",
                            BM_NUM.get(row["Parameter"], ("-", None, None))[0],
                            row["Status"],
                        ]
                        for _, row in df_lok.iterrows()
                    ]
                    lok_table = Table([lok_header] + lok_rows, hAlign="LEFT")
                    lok_table.setStyle(TableStyle([
                        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#0099FF")),
                        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
                        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                        ("FONTSIZE",      (0, 0), (-1, -1), 8),
                        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                        ("GRID",          (0, 0), (-1, -1), 0.4, colors.grey),
                        ("TOPPADDING",    (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF4FF")]),
                    ]))
                    content.append(lok_table)
                    content.append(Spacer(1, 6))
 
                    # Narasi kesimpulan
                    if semua_memenuhi:
                        narasi = (
                            f"Berdasarkan hasil analisis, seluruh parameter kualitas air di lokasi "
                            f"<b>{lokasi}</b> dinyatakan <b>MEMENUHI</b> baku mutu perairan kelas II sesuai {regulasi}. "
                            f"Air pada lokasi ini dinilai <b>AMAN</b> berdasarkan parameter yang diuji."
                        )
                        content.append(Paragraph(narasi, styles["Normal"]))
                    else:
                        daftar_le = "; ".join(params_melebihi)
                        narasi = (
                            f"Berdasarkan hasil analisis, terdapat {len(params_melebihi)} parameter "
                            f"di lokasi <b>{lokasi}</b> yang <b>MELEBIHI</b> baku mutu sesuai {regulasi}, "
                            f"yaitu: {daftar_le}. "
                            f"Air pada lokasi ini dinilai <b>TIDAK AMAN / TERCEMAR</b> dan memerlukan "
                            f"penanganan lebih lanjut sebelum digunakan atau dibuang ke badan air penerima."
                        )
                        content.append(Paragraph(narasi, styles["Normal"]))
 
                    content.append(Spacer(1, 10))
 
            # Kesimpulan global
            content.append(Spacer(1, 6))
            total_lok    = df["Lokasi"].nunique()
            total_param  = len(df)
            jml_melebihi = (df["Status"] == "❌ Melebihi").sum()
            jml_memenuhi = (df["Status"] == "✅ Memenuhi").sum()
            pct_memenuhi = (jml_memenuhi / total_param * 100) if total_param > 0 else 0
 
            content.append(Paragraph("Ringkasan Keseluruhan", styles["Heading3"]))
            content.append(Spacer(1, 4))
 
            global_rows = [
                ["Uraian", "Jumlah"],
                ["Total lokasi sampling",            str(total_lok)],
                ["Total pengukuran parameter",       str(total_param)],
                ["Parameter memenuhi baku mutu",     str(jml_memenuhi)],
                ["Parameter melebihi baku mutu",     str(jml_melebihi)],
                ["Tingkat kepatuhan",                f"{pct_memenuhi:.1f}%"],
            ]
            global_table = Table(global_rows, hAlign="LEFT", colWidths=[280, 100])
            global_table.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#0099FF")),
                ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
                ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("ALIGN",         (1, 0), (1, -1),  "CENTER"),
                ("GRID",          (0, 0), (-1, -1), 0.4, colors.grey),
                ("TOPPADDING",    (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF4FF")]),
            ]))
            content.append(global_table)
            content.append(Spacer(1, 10))
 
            # Kalimat penutup
            if jml_melebihi == 0:
                penutup = (
                    "Secara keseluruhan, semua lokasi sampling menunjukkan kualitas air yang "
                    "<b>BAIK</b> dan memenuhi seluruh baku mutu perairan kelas II yang berlaku."
                )
            elif pct_memenuhi >= 70:
                penutup = (
                    f"Secara keseluruhan, sebagian besar parameter ({pct_memenuhi:.1f}%) memenuhi baku mutu perairan kelas II. "
                    "Namun terdapat beberapa parameter yang masih perlu diperhatikan dan ditindaklanjuti."
                )
            else:
                penutup = (
                    f"Secara keseluruhan, tingkat kepatuhan baku mutu hanya {pct_memenuhi:.1f}%. "
                    "Diperlukan penanganan serius terhadap sumber pencemaran dan pengolahan air "
                    "sebelum dimanfaatkan atau dibuang ke lingkungan."
                )
            content.append(Paragraph(penutup, styles["Normal"]))
            content.append(Spacer(1, 16))
 
            # Tanda tangan
            content.append(Paragraph(
                f"Bogor, {date.today().strftime('%d %B %Y')}",
                styles["Normal"]
            ))
            content.append(Spacer(1, 40))
            content.append(Paragraph(
                f"({analis or '................................'})",
                styles["Normal"]
            ))
            content.append(Paragraph("Analis / Penanggung Jawab", styles["Normal"]))
 
        doc.build(content)
 
        with open("laporan_hydrolysis.pdf", "rb") as f:
            pdf_bytes = f.read()
 
        st.download_button(
            label="⬇️ Download Laporan PDF",
            data=pdf_bytes,
            file_name=f"laporan_hydrolysis_{date.today()}.pdf",
            mime="application/octet-stream"
        )

    footer()

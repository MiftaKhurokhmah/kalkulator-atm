import pandas as pd
import streamlit as st

# Set judul halaman web
st.set_page_config(
    page_title="Kalkulator GIM & Sewa ATM", page_icon="🖥️", layout="wide"
)

st.title("🖥️ Kalkulator GIM & Prediksi Harga Sewa ATM")
st.write(
    "Aplikasi web interaktif untuk menentukan kelayakan nilai sewa space/booth ATM."
)

# ==============================================================================
# SIDEBAR: UPLOAD & FILTER DATABASE
# ==============================================================================
st.sidebar.header("📁 1. Database Pembanding")
file_diupload = st.sidebar.file_drop_channel(
    "Upload File CSV Pembanding", type=["csv"]
)

gim_pasar_default = 13.5  # Nilai default jika belum ada file yang diupload

if file_diupload is not None:
    try:
        df = pd.read_csv(file_diupload)
        df.columns = df.columns.str.strip()

        if "GIM" in df.columns or "gim" in df.columns:
            kolom_gim = "GIM" if "GIM" in df.columns else "gim"
            data_gim = pd.to_numeric(df[kolom_gim], errors="coerce").dropna()

            # Proses Outlier IQR
            Q1 = data_gim.quantile(0.25)
            Q3 = data_gim.quantile(0.75)
            IQR = Q3 - Q1
            batas_bawah = Q1 - 1.5 * IQR
            batas_above = Q3 + 1.5 * IQR

            df_clean = df[
                (pd.to_numeric(df[kolom_gim], errors="coerce") >= b_bawah)
                & (pd.to_numeric(df[kolom_gim], errors="coerce") <= b_above)
            ]
            gim_pasar_default = pd.to_numeric(
                df_clean[kolom_gim], errors="coerce"
            ).mean()

            st.sidebar.success(
                f"✅ Database Berhasil Diproses! Rata-rata GIM Pasar (Tanpa Outlier): {gim_pasar_default:.2f}"
            )
        else:
            st.sidebar.error("Kolom 'GIM' tidak ditemukan di file Anda.")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca file: {e}")
else:
    st.sidebar.info(
        f"ℹ️ Menggunakan standar GIM pasar default: {gim_pasar_default}"
    )


# ==============================================================================
# TAMPILAN UTAMA: MEMBAGI MENJADI 2 KALKULATOR (TAB)
# ==============================================================================
tab1, tab2 = st.tabs(
    ["📊 Kalkulator 1: Mencari GIM", "💰 Kalkulator 2: Prediksi Harga Sewa"]
)

with tab1:
    st.header("Kalkulator 1: Menentukan GIM Properti Baru")
    st.write(
        "Gunakan jika Anda tahu harga sewa tahunan dan ingin mencari nilai GIM properti tersebut."
    )

    col1, col2 = st.columns(2)
    with col1:
        sewa_k1 = st.number_input(
            "Harga Sewa Tahunan (Rp)", value=25000000, step=1000000, key="sewa1"
        )
        luas_tanah_k1 = st.number_input(
            "Luas Tanah Total (m²)", value=150, step=10
        )
        harga_penawaran_k1 = st.number_input(
            "Harga Penawaran Tanah per m² (Rp)", value=4500000, step=500000
        )
        diskon_k1 = (
            st.slider("Faktor Diskon Nego (%)", 0, 50, 10, step=5) / 100.0
        )

    with col2:
        luas_bangunan_k1 = st.number_input(
            "Luas Bangunan Total (m²)", value=100, step=10
        )
        btb_k1 = st.number_input(
            "Biaya Bangunan Baru (BTB) per m² (Rp)", value=4000000, step=500000
        )
        tahun_berdiri_k1 = st.number_input(
            "Tahun Bangunan Berdiri", value=2018, min_value=1980, max_value=2026
        )

    # Logika Hitung Kalkulator 1
    tanah_bersih = luas_tanah_k1 * (harga_penawaran_k1 * (1 - diskon_k1))
    umur_aktual = max(0, 2026 - tahun_berdiri_k1)
    depresiasi = min(1.0, umur_aktual / 20)
    bangunan_pasar = (luas_bangunan_k1 * btb_k1) * (1 - depresiasi)
    properti_total = tanah_bersih + bangunan_pasar
    gim_hasil = properti_total / sewa_k1 if sewa_k1 > 0 else 0

    st.markdown("---")
    st.subheader("Hasil Analisis Properti:")
    st.write(f"• Nilai Tanah Riil: **Rp {tanah_bersih:,.2f}**")
    st.write(f"• Nilai Bangunan (Setelah Depresiasi): **Rp {bangunan_pasar:,.2f}**")
    st.write(f"• Total Estimasi Nilai Properti: **Rp {properti_total:,.2f}**")
    st.metric(label="GIM HASIL KALKULASI", value=f"{gim_hasil:.2f}")

with tab2:
    st.header("Kalkulator 2: Memprediksi Harga Sewa ATM")
    st.write(
        "Gunakan jika Anda ingin mencari rekomendasi tarif harga sewa space ATM ideal."
    )

    gim_digunakan = st.number_input(
        "GIM Benchmark Pasar yang Digunakan", value=gim_pasar_default, step=0.1
    )

    col3, col4 = st.columns(2)
    with col3:
        luas_atm = st.number_input("Luas Lantai ATM (m²)", value=3.0, step=0.5)
        l_tanah_total = st.number_input(
            "Luas Tanah Total Gedung Induk (m²)", value=200, step=10
        )
        h_tanah_m2 = st.number_input(
            "Harga Pasar Tanah Sekitar per m² (Rp)", value=3500000, step=500000
        )
        l_bangunan_total = st.number_input(
            "Luas Bangunan Total Gedung Induk (m²)", value=120, step=10
        )

    with col4:
        btb_k2 = st.number_input(
            "BTB Gedung Induk per m² (Rp)", value=4500000, step=500000, key="btb2"
        )
        tahun_berdiri_k2 = st.number_input(
            "Tahun Berdiri Gedung Induk",
            value=2020,
            min_value=1980,
            max_value=2026,
            key="thn2",
        )
        tipe_mesin = st.selectbox(
            "Tipe Mesin ATM", ["CRM (Setor Tarik)", "ATM (Tarik Tunai Saja)"]
        )
        listrik = st.radio("Fasilitas Listrik", ["Include Listrik", "Exlude"])
        akses_jalan = st.selectbox(
            "Akses Lokasi Jalan", ["Jalan Utama / Arteri", "Jalan Biasa / Masuk"]
        )

    # Logika Hitung Kalkulator 2
    rasio_tanah = luas_atm / l_tanah_total
    v_tanah_atm = (l_tanah_total * h_tanah_m2) * rasio_tanah

    umur_akt_k2 = max(0, 2026 - tahun_berdiri_k2)
    dep_k2 = min(1.0, umur_akt_k2 / 20)
    v_bangunan_dep = (l_bangunan_total * btb_k2) * (1 - dep_k2)
    rasio_bgn = luas_atm / l_bangunan_total
    v_bangunan_atm = v_bangunan_dep * rasio_bgn

    total_space_atm = v_tanah_atm + v_bangunan_atm
    f_jalan = 1.2 if akses_jalan == "Jalan Utama / Arteri" else 1.0
    sewa_dasar = (total_space_atm * f_jalan) / gim_digunakan

    b_listrik = 12000000 if listrik == "Include Listrik" else 0
    b_crm = 3000000 if "CRM" in tipe_mesin else 0
    rekomendasi_sewa = sewa_dasar + b_listrik + b_crm

    st.markdown("---")
    st.subheader("Hasil Rekomendasi:")
    st.write(f"• Nilai Proporsional Lahan ATM: **Rp {v_tanah_atm:,.2f}**")
    st.write(f"• Nilai Proporsional Booth ATM: **Rp {v_bangunan_atm:,.2f}**")
    st.write(f"• Harga Sewa Dasar Bersih / Tahun: **Rp {sewa_dasar:,.2f}**")
    st.write(
        f"• Tambahan Fasilitas (Listrik & Fitur Mesin): **Rp {b_listrik + b_crm:,.2f}**"
    )
    st.success(
        f"💡 **REKOMENDASI TARIF SEWA IDEAL: Rp {rekomendasi_sewa:,.2f} / Tahun**"
    )

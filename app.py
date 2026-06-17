import datetime
import numpy as np
import pandas as pd
import streamlit as st

# Set judul dan konfigurasi dasar halaman web
st.set_page_config(
    page_title="Kalkulator GIM & Sewa ATM", page_icon="🖥️", layout="wide"
)

st.title("🖥️ Kalkulator GIM & Prediksi Harga Sewa ATM")
st.write(
    "Aplikasi web interaktif untuk menentukan kelayakan nilai sewa space/booth ATM sesuai karakteristik fisik dan lokasi."
)

# ==============================================================================
# SIDEBAR: UPLOAD DATABASE & DATA INPUT UTAMA
# ==============================================================================
st.sidebar.header("📁 1. Database Pembanding")
file_diupload = st.sidebar.file_uploader(
    "Upload File CSV Pembanding", type=["csv"]
)

# ==============================================================================
# SIDEBAR INPUT: DATA KARAKTERISTIK OBJEK (DIKONSUMSI OLEH KEDUA KALKULATOR)
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("📐 2. Data Fisik & Bangunan")

luas_atm = st.sidebar.number_input(
    "Luas Lantai ATM (m²)", min_value=0.1, value=2.0, step=0.5
)
luas_bangunan = st.sidebar.number_input(
    "Luas Bangunan Gedung Induk (m²)", min_value=1.0, value=100.0, step=10.0
)
jumlah_lantai = st.sidebar.number_input(
    "Jumlah Lantai Gedung", min_value=1, value=1, step=1
)
luas_tanah_total = st.sidebar.number_input(
    "Luas Tanah Total Gedung (m²)", min_value=1.0, value=150.0, step=10.0
)

# Logika Luas Bangunan Efektif
# 1 Lantai = 100%, >1 Lantai = 70%
persen_efektif = 1.0 if jumlah_lantai == 1 else 0.7
luas_efektif_bangunan = luas_bangunan * persen_efektif

st.sidebar.caption(
    f"Luas Efektif Bangunan ({int(persen_efektif*100)}%): {luas_efektif_bangunan:.2f} m²"
)

st.sidebar.markdown("---")
st.sidebar.header("💰 3. Nilai Pasar & Biaya")
harga_tanah_m2 = st.sidebar.number_input(
    "Harga Pasar Tanah per m² (Rp)", min_value=0, value=5000000, step=500000
)
btb_baru = st.sidebar.number_input(
    "Harga BTB Bangunan Baru per m² (Rp)", min_value=0, value=4000000, step=500000
)
tahun_dibangun = st.sidebar.number_input(
    "Tahun Bangunan Didirikan", min_value=1980, max_value=2026, value=2016
)

# Perhitungan Depresiasi Bangunan
tahun_sekarang = datetime.date.today().year
umur_ekonomis = 20  # Asumsi standar umur ekonomis ruko/gedung komersil
umur_aktual = max(0, tahun_sekarang - tahun_dibangun)
depresiasi_total_gedung = (luas_bangunan * btb_baru) * (
    min(1.0, umur_aktual / umur_ekonomis)
)

st.sidebar.markdown("---")
st.sidebar.header("🚦 4. Penyesuaian Karakteristik")
mobilitas = st.sidebar.selectbox(
    "Tingkat Mobilitas / Traffic", ["Ramai", "Sedang", "Sepi"]
)
jenis_atm = st.sidebar.selectbox(
    "Jenis Mesin ATM", ["Setor Tarik (CRM)", "Tarik Tunai Saja"]
)
jarak_jalan_utama = st.sidebar.number_input(
    "Jarak ke Jalan Utama (Meter)", min_value=0, value=10
)

# FIX: Menggunakan GIM Terbaru setelah sewa dikurangi listrik.
# Nilai adj mobilitas di-set 0 karena faktor keramaian sudah include/melekat di nilai GIM masing-masing.
if mobilitas == "Ramai":
    gim_pasar_default = 2.7475567
    nilai_adj_mobilitas = 0
elif mobilitas == "Sedang":
    gim_pasar_default = 2.1902831
    nilai_adj_mobilitas = 0
else:  # Sepi
    gim_pasar_default = 2.8581090
    nilai_adj_mobilitas = 0

# Jika file CSV diupload, override nilai gim_pasar_default dengan hasil perhitungan CSV
if file_diupload is not None:
    try:
        df = pd.read_csv(file_diupload)
        df.columns = df.columns.str.strip()

        kolom_gim = None
        if "GIM" in df.columns:
            kolom_gim = "GIM"
        elif "gim" in df.columns:
            kolom_gim = "gim"

        if kolom_gim is not None:
            data_gim = pd.to_numeric(df[kolom_gim], errors="coerce").dropna()

            if len(data_gim) > 0:
                Q1 = data_gim.quantile(0.25)
                Q3 = data_gim.quantile(0.75)
                IQR = Q3 - Q1
                batas_bawah = Q1 - (1.5 * IQR)
                batas_atas = Q3 + (1.5 * IQR)

                df_clean = df[
                    (
                        pd.to_numeric(df[kolom_gim], errors="coerce")
                        >= batas_bawah
                    )
                    & (
                        pd.to_numeric(df[kolom_gim], errors="coerce")
                        <= batas_atas
                    )
                ]
                gim_pasar_default = pd.to_numeric(
                    df_clean[kolom_gim], errors="coerce"
                ).mean()

                st.sidebar.success(
                    f"✅ Database Diproses!\n"
                    f"- Rata-rata GIM Pasar (CSV): {gim_pasar_default:.4f}"
                )
            else:
                st.sidebar.error(
                    "Tidak ada data angka yang valid di kolom GIM."
                )
        else:
            st.sidebar.error("Kolom 'GIM' tidak ditemukan!")
    except Exception as e:
        st.sidebar.error(f"Gagal memproses file: {e}")
else:
    st.sidebar.info(
        f"ℹ️ Baseline GIM ({mobilitas}): {gim_pasar_default:.4f}"
    )

# Konversi Kualitatif menjadi Penyesuaian Nominal Rupiah untuk karakteristik non-GIM
nilai_adj_jenis = 10000000 if jenis_atm == "Setor Tarik (CRM)" else 0
nilai_adj_jarak = max(
    0, (100 - jarak_jalan_utama) * 150000
)  # Semakin dekat jalan utama, penyesuaian semakin tinggi

total_penyesuaian = nilai_adj_mobilitas + nilai_adj_jenis + nilai_adj_jarak


# ==============================================================================
# PROSES UTAMA PERHITUNGAN MATEMATIKA
# ==============================================================================
# 1. Nilai tanah ATM
nilai_tanah_atm = (
    (luas_atm / luas_efektif_bangunan) * luas_tanah_total * harga_tanah_m2
)

# 2. Nilai bangunan ATM
nilai_bangunan_bersih = (luas_bangunan * btb_baru) - depresiasi_total_gedung
nilai_bangunan_atm = (luas_atm / luas_efektif_bangunan) * nilai_bangunan_bersih

# 3. Nilai ATM Total
nilai_atm_total = nilai_tanah_atm + nilai_bangunan_atm + total_penyesuaian


# ==============================================================================
# TAMPILAN INTERFACE UTAMA: DUA TAB KALKULATOR
# ==============================================================================
st.markdown("### 📋 Parameter Utama Terhitung")
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Luas Efektif Bangunan",
    f"{luas_efektif_bangunan:.2f} m²",
    f"Efisiensi {int(persen_efektif*100)}%",
)
c2.metric("Nilai Proporsional Tanah", f"Rp {nilai_tanah_atm:,.0f}")
c3.metric("Nilai Proporsional Bangunan", f"Rp {nilai_bangunan_atm:,.0f}")
c4.metric("Total Estimasi Nilai ATM", f"Rp {nilai_atm_total:,.0f}")

st.markdown("---")

tab1, tab2 = st.tabs(
    [
        "📊 Kalkulator 1: Hitung Nilai GIM",
        "💰 Kalkulator 2: Prediksi Harga Sewa Tahunan",
    ]
)

# --- KALKULATOR 1: MENCARI GIM ---
with tab1:
    st.header("Kalkulator GIM (Gross Income Multiplier)")
    st.write(
        "Menghitung indikasi nilai GIM objek dengan memasukkan data harga sewa tahunan yang telah diketahui."
    )

    harga_sewa_k1 = st.number_input(
        "Masukkan Harga Sewa Tahunan Eksisting / Aktual (Rp)",
        min_value=1000000,
        value=20000000,
        step=1000000,
        key="k1_sewa",
    )

    if harga_sewa_k1 > 0:
        gim_hasil = nilai_atm_total / harga_sewa_k1

        st.markdown("#### Ringkasan Analisis Nilai GIM:")
        st.success(f"### 📈 Nilai Indikasi GIM Objek: **{gim_hasil:.4f} x**")

        with st.expander("Lihat Detail Alur Formula Matematika"):
            st.latex(
                r"\text{Nilai Tanah ATM} = \frac{"
                + str(luas_atm)
                + "}{"
                + f"{luas_efektif_bangunan:.2f}"
                + r"} \times "
                + str(luas_tanah_total)
                + r" \times "
                + f"{harga_tanah_m2:,} = Rp\ {nilai_tanah_atm:,.0f}"
            )
            st.latex(
                r"\text{Nilai Bangunan ATM} = \frac{"
                + str(luas_atm)
                + "}{"
                + f"{luas_efektif_bangunan:.2f}"
                + r"} \times \left(("
                + str(luas_bangunan)
                + r"\times"
                + f"{btb_baru:,}"
                + r") - "
                + f"{depresiasi_total_gedung:,.0f}"
                + r"\right) = Rp\ {nilai_bangunan_atm:,.0f}"
            )
            st.latex(
                r"\text{Nilai ATM Total} = \text{Tanah} + \text{Bangunan} + \text{Penyesuaian} = Rp\ "
                + f"{nilai_atm_total:,.0f}"
            )
            st.latex(
                r"\text{Nilai GIM} = \frac{\text{Nilai ATM Total}}{\text{Harga Sewa}} = "
                + f"{gim_hasil:.4f}"
            )

# --- FIX KALKULATOR 2: PREDIKSI HARGA SEWA ---
with tab2:
    st.header("Kalkulator Harga Sewa Tahunan")
    st.write(
        "Menghitung proyeksi harga sewa tahunan yang ideal berdasarkan indikasi angka GIM pasar dari karakteristik sejenis."
    )

    col_gim, col_listrik = st.columns(2)

    with col_gim:
        gim_pasar_input = st.number_input(
            "GIM dari Pasar (Otomatis menyesuaikan tingkat mobilitas)",
            min_value=0.1,
            value=float(gim_pasar_default),
            step=0.1,
            format="%.4f",
            key="k2_gim",
        )

    with col_listrik:
        # Menyesuaikan penamaan opsi sesuai karakteristik data lapangan Anda
        opsi_listrik = st.selectbox(
            "Fasilitas Listrik",
            ["Include Listrik", "Tidak Include Listrik"],
        )

    if gim_pasar_input > 0:
        # 1. Hitung nilai dasar h (Tarif Sewa - Biaya Listrik) dari formula dasar GIM pasar
        tarif_sewa_minus_listrik = nilai_atm_total / gim_pasar_input

        # 2. Logika penentuan tarif sewa total (i) berdasarkan arah data input
        # Jika include listrik, maka tarif sewa (i) adalah h + 3.000.000 (agar validasi h = i - 3jt sesuai)
        if opsi_listrik == "Include Listrik":
            biaya_listrik = 3000000
            harga_sewa_prediksi = tarif_sewa_minus_listrik + biaya_listrik
        else:
            biaya_listrik = 0
            harga_sewa_prediksi = tarif_sewa_minus_listrik

        st.markdown("#### Proyeksi Hasil Sewa:")
        st.info(
            f"### 💵 Estimasi Tarif Sewa (per Tahun): **Rp {harga_sewa_prediksi:,.0f}**"
        )

        # Rincian pembuktian agar logis dengan berkas Excel Anda
        with st.expander("Lihat Rincian & Validasi Rumus (h = i - biaya listrik)"):
            st.write(f"**Hasil Prediksi Komponen:**")
            st.write(f"- Estimasi Tarif Sewa per Tahun (`i`): **Rp {harga_sewa_prediksi:,.0f}**")
            st.write(f"- Biaya Listrik: **Rp {biaya_listrik:,.0f}**")
            st.markdown("---")
            st.write(f"**Validasi Parameter Kolom Database Anda:**")
            st.write(
                f"- **Tarif Sewa - Biaya Listrik (`h`):** Rp {tarif_sewa_minus_listrik:,.0f} *(Hasil dari Nilai ATM ÷ GIM)*"
            )
            st.caption(
                f"Sesuai formula Anda: jika include listrik maka h = {harga_sewa_prediksi:,.0f} - {biaya_listrik:,.0f} = {harga_sewa_prediksi - biaya_listrik:,.0f}"
            )

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

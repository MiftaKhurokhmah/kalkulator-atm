import numpy as np
import pandas as pd
import streamlit as st
import datetime

# Set judul dan konfigurasi dasar halaman web
st.set_page_config(
    page_title="Kalkulator GIM & Sewa ATM Kontrol Pasar", page_icon="🖥️", layout="wide"
)

st.title("🖥️ Kalkulator GIM & Prediksi Harga Sewa ATM (Penyaringan Fleksibel)")
st.write(
    "Aplikasi ini otomatis menyelaraskan karakteristik objek dengan database Excel tanpa membuang data minim."
)

# ==============================================================================
# SIDEBAR STEP 1: UPLOAD DATABASE TERLEBIH DAHULU UNTUK MENGEKSTRAK KATA
# ==============================================================================
st.sidebar.header("📁 1. Database Pembanding")
file_diupload = st.sidebar.file_uploader("Upload File CSV Pembanding", type=["csv"])

# Inisialisasi default acuan
gim_pasar_final = 13.5
list_mobilitas = ["Sedang", "Tinggi", "Rendah"]
list_jenis_atm = ["Setor Tarik", "Tarik Tunai"]

df_pasar = None
kolom_gim, kolom_mobilitas, kolom_jenis = None, None, None

if file_diupload is not None:
    try:
        df_pasar = pd.read_csv(file_diupload)
        df_pasar.columns = df_pasar.columns.str.strip() # Bersihkan spasi nama kolom

        # Deteksi Kolom Esensial di CSV Anda
        kolom_gim = "GIM" if "GIM" in df_pasar.columns else ("gim" if "gim" in df_pasar.columns else None)
        kolom_mobilitas = "Mobilitas" if "Mobilitas" in df_pasar.columns else ("mobilitas" if "mobilitas" in df_pasar.columns else None)
        kolom_jenis = "Jenis ATM" if "Jenis ATM" in df_pasar.columns else ("jenis_atm" if "jenis_atm" in df_pasar.columns else None)
        
        if kolom_gim and kolom_mobilitas and kolom_jenis:
            # Bersihkan baris kosong atau teks error di kolom GIM
            df_pasar[kolom_gim] = pd.to_numeric(df_pasar[kolom_gim], errors='coerce')
            df_pasar = df_pasar.dropna(subset=[kolom_gim])
            
            # Ambil data unik asli dari Excel agar input pilihan sinkron 100%
            list_mobilitas = sorted(df_pasar[kolom_mobilitas].dropna().astype(str).str.strip().unique().tolist())
            list_jenis_atm = sorted(df_pasar[kolom_jenis].dropna().astype(str).str.strip().unique().tolist())
        else:
            st.sidebar.error("Struktur kolom CSV Anda tidak cocok! Pastikan ada kolom: GIM, Mobilitas, dan Jenis ATM.")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca file: {e}")

# ==============================================================================
# SIDEBAR STEP 2: PILIHAN KARAKTERISTIK (DINAMIS DARI EXCEL)
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("🚦 2. Karakteristik Objek Penilaian")
mobilitas_dipilih = st.sidebar.selectbox("Tingkat Mobilitas / Traffic", list_mobilitas)
jenis_atm_dipilih = st.sidebar.selectbox("Jenis Mesin ATM", list_jenis_atm)
jarak_jalan_utama = st.sidebar.number_input("Jarak ke Jalan Utama (Meter)", min_value=0, value=10)

# Penyesuaian Nominal Rupiah untuk Nilai ATM Fisik
nilai_adj_mobilitas = 15000000 if "tinggi" in mobilitas_dipilih.lower() else (5000000 if "sedang" in mobilitas_dipilih.lower() else 0)
nilai_adj_jenis = 10000000 if "setor" in jenis_atm_dipilih.lower() else 0
total_penyesuaian = nilai_adj_mobilitas + nilai_adj_jenis

# ==============================================================================
# PROSES PENYARINGAN DATA DENGAN BATAS TOLERANSI DATA MINIM
# ==============================================================================
status_filter_pesan = "ℹ️ Menggunakan baseline standar GIM pasar global: 13.5"

if df_pasar is not None and kolom_gim:
    # Saring baris yang memiliki karakteristik serupa
    df_filtered = df_pasar[
        (df_pasar[kolom_mobilitas].astype(str).str.strip().str.lower() == mobilitas_dipilih.lower()) &
        (df_pasar[kolom_jenis].astype(str).str.strip().str.lower() == jenis_atm_dipilih.lower())
    ]
    
    total_data_cocok = len(df_filtered)
    
    if total_data_cocok > 0:
        # PERBAIKAN UTAMA: Jika data sedikit (<= 5), JANGAN buang outlier agar data tidak habis!
        if total_data_cocok > 5:
            Q1 = df_filtered[kolom_gim].quantile(0.25)
            Q3 = df_filtered[kolom_gim].quantile(0.75)
            IQR = Q3 - Q1
            df_clean = df_filtered[
                (df_filtered[kolom_gim] >= (Q1 - 1.5 * IQR)) & 
                (df_filtered[kolom_gim] <= (Q3 + 1.5 * IQR))
            ]
            # Pastikan setelah dibuang datanya tidak sisa 0
            if len(df_clean) > 0:
                df_filtered = df_clean
        
        gim_pasar_final = df_filtered[kolom_gim].mean()
        status_filter_pesan = (
            f"✅ Sukses Menemukan Data Sejenis!\n"
            f"- Ada {len(df_filtered)} baris pembanding yang cocok di Excel.\n"
            f"- Nilai GIM Spesifik Karakteristik: {gim_pasar_final:.2f}"
        )
    else:
        # Jika benar-benar kosong kriteria tersebut, gunakan rata-rata total isi Excel
        gim_pasar_final = df_pasar[kolom_gim].mean()
        status_filter_pesan = (
            f"⚠️ Karakteristik spesifik tidak ditemukan di Excel!\n"
            f"- Dialihkan menggunakan rata-rata total database: {gim_pasar_final:.2f}"
        )

st.sidebar.success(status_filter_pesan)

# ==============================================================================
# SIDEBAR STEP 3: DATA DIMENSI FISIK & BANGUNAN INDUK
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("📐 3. Data Fisik & Bangunan")
luas_atm = st.sidebar.number_input("Luas Lantai ATM (m²)", min_value=0.1, value=1.0, step=0.5)
luas_bangunan = st.sidebar.number_input("Luas Bangunan Gedung Induk (m²)", min_value=1.0, value=100.0, step=10.0)
jumlah_lantai = st.sidebar.number_input("Jumlah Lantai Gedung", min_value=1, value=1, step=1)
luas_tanah_total = st.sidebar.number_input("Luas Tanah Total Gedung (m²)", min_value=1.0, value=150.0, step=10.0)

# Aturan Luas Bangunan Efektif (1 Lantai = 100%, >1 Lantai = 70%)
persen_efektif = 1.0 if jumlah_lantai == 1 else 0.7
luas_efektif_bangunan = luas_bangunan * persen_efektif

st.sidebar.markdown("---")
st.sidebar.header("💰 4. Nilai Pasar & Biaya Bangunan")
harga_tanah_m2 = st.sidebar.number_input("Harga Pasar Tanah per m² (Rp)", min_value=0, value=5000000, step=500000)
btb_baru = st.sidebar.number_input("Harga BTB Bangunan Baru per m² (Rp)", min_value=0, value=4000000, step=500000)
tahun_dibangun = st.sidebar.number_input("Tahun Bangunan Didirikan", min_value=1980, max_value=2026, value=2016)

# Logika Depresiasi (Asumsi umur ekonomis bangunan 20 tahun)
tahun_sekarang = datetime.date.today().year
umur_ekonomis = 20
umur_aktual = max(0, tahun_sekarang - tahun_dibangun)
depresiasi_total_gedung = (luas_bangunan * btb_baru) * (min(1.0, umur_aktual / umur_ekonomis))


# ==============================================================================
# PROSES UTAMA PERHITUNGAN MATEMATIKA (SESUAI RUMUS USER)
# ==============================================================================
# 1. Nilai tanah atm proporsional
nilai_tanah_atm = (luas_atm / luas_efektif_bangunan) * luas_tanah_total * harga_tanah_m2

# 2. Nilai bangunan atm proporsional
nilai_bangunan_bersih = (luas_bangunan * btb_baru) - depresiasi_total_gedung
nilai_bangunan_atm = (luas_atm / luas_efektif_bangunan) * nilai_bangunan_bersih

# 3. Total Nilai Indikasi Booth ATM
nilai_atm_total = nilai_tanah_atm + nilai_bangunan_atm + total_penyesuaian


# ==============================================================================
# TAMPILAN INTERFACE UTAMA
# ==============================================================================
st.markdown("### 📊 Status Karakteristik & Parameter Terhitung")
c1, c2, c3, c4 = st.columns(4)
c1.metric("GIM Acuan Karakteristik", f"{gim_pasar_final:.2f} x", f"Kombinasi Terpilih")
c2.metric("Luas Efektif Bangunan", f"{luas_efektif_bangunan:.1f} m²", f"Lantai: {jumlah_lantai}")
c3.metric("Penyesuaian Fisik + Lokasi", f"Rp {total_penyesuaian:,.0f}")
c4.metric("Total Indikasi Nilai ATM", f"Rp {nilai_atm_total:,.0f}")

st.markdown("---")

tab1, tab2 = st.tabs([
    "📊 Kalkulator 1: Cari Nilai GIM Objek", 
    "💰 Kalkulator 2: Prediksi Harga Sewa Berbasis Karakteristik"
])

# --- TAB 1 ---
with tab1:
    st.header("Kalkulator GIM Objek Baru")
    st.write("Menghitung nilai GIM spesifik objek Anda dengan membandingkan nilai total ATM terhadap harga sewa riil.")
    
    harga_sewa_k1 = st.number_input("Harga Sewa Tahunan Riil Objek (Rp)", min_value=1000000, value=24000000, step=1000000, key="k1_sewa")
    
    if harga_sewa_k1 > 0:
        gim_hasil = nilai_atm_total / harga_sewa_k1
        st.success(f"### 📈 Indikasi GIM Objek Anda: **{gim_hasil:.2f} x**")

# --- TAB 2 ---
with tab2:
    st.header("Kalkulator Proyeksi Harga Sewa Wajar")
    st.write("Menghitung harga sewa tahunan menggunakan GIM pasar acuan dari hasil saringan database otomatis.")
    
    gim_yang_dipakai = st.number_input("GIM Pasar yang Digunakan", min_value=0.1, value=gim_pasar_final, step=0.1, key="k2_gim")
    
    if gim_yang_dipakai > 0:
        harga_sewa_prediksi = nilai_atm_total / gim_yang_dipakai
        st.info(f"### 💵 Rekomendasi Harga Sewa Ideal Berdasarkan Karakteristik Sejenis: **Rp {harga_sewa_prediksi:,.0f} / Tahun**")

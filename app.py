import numpy as np
import pandas as pd
import streamlit as st
import datetime

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

gim_pasar_default = 3.38  # Nilai default jika belum ada file yang diupload

if file_diupload is not None:
    try:
        # Membaca file CSV
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
                # Filter Outlier IQR
                Q1 = data_gim.quantile(0.25)
                Q3 = data_gim.quantile(0.75)
                IQR = Q3 - Q1
                batas_bawah = Q1 - (1.5 * IQR)
                batas_atas = Q3 + (1.5 * IQR)

                df_clean = df[
                    (pd.to_numeric(df[kolom_gim], errors="coerce") >= batas_bawah)
                    & (pd.to_numeric(df[kolom_gim], errors="coerce") <= batas_atas)
                ]
                gim_pasar_default = pd.to_numeric(df_clean[kolom_gim], errors="coerce").mean()

                st.sidebar.success(
                    f"✅ Database Diproses!\n"
                    f"- Rata-rata GIM Pasar: {gim_pasar_default:.2f}"
                )
            else:
                st.sidebar.error("Tidak ada data angka yang valid di kolom GIM.")
        else:
            st.sidebar.error("Kolom 'GIM' tidak ditemukan!")
    except Exception as e:
        st.sidebar.error(f"Gagal memproses file: {e}")
else:
    st.sidebar.info(f"ℹ️ Menggunakan baseline GIM pasar default: {gim_pasar_default}")


# ==============================================================================
# SIDEBAR INPUT: DATA KARAKTERISTIK OBJEK (DIKONSUMSI OLEH KEDUA KALKULATOR)
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("📐 2. Data Fisik & Bangunan")

luas_atm = st.sidebar.number_input("Luas Lantai ATM (m²)", min_value=0.1, value=2.0, step=0.5)
luas_bangunan = st.sidebar.number_input("Luas Bangunan Gedung Induk (m²)", min_value=1.0, value=100.0, step=10.0)
jumlah_lantai = st.sidebar.number_input("Jumlah Lantai Gedung", min_value=1, value=1, step=1)
luas_tanah_total = st.sidebar.number_input("Luas Tanah Total Gedung (m²)", min_value=1.0, value=150.0, step=10.0)

# Logika Luas Bangunan Efektif sesuai Instruksi Anda
# 1 Lantai = 100%, >1 Lantai = 70%
persen_efektif = 1.0 if jumlah_lantai == 1 else 0.7
luas_efektif_bangunan = luas_bangunan * persen_efektif

st.sidebar.caption(f"Luas Efektif Bangunan ({int(persen_efektif*100)}%): {luas_efektif_bangunan:.2f} m²")

st.sidebar.markdown("---")
st.sidebar.header("💰 3. Nilai Pasar & Biaya")
harga_tanah_m2 = st.sidebar.number_input("Harga Pasar Tanah per m² (Rp)", min_value=0, value=5000000, step=500000)
btb_baru = st.sidebar.number_input("Harga BTB Bangunan Baru per m² (Rp)", min_value=0, value=4000000, step=500000)
tahun_dibangun = st.sidebar.number_input("Tahun Bangunan Didirikan", min_value=1980, max_value=2026, value=2016)

# Perhitungan Depresiasi Bangunan
tahun_sekarang = datetime.date.today().year
umur_ekonomis = 20  # Asumsi standar umur ekonomis ruko/gedung komersil
umur_aktual = max(0, tahun_sekarang - tahun_dibangun)
depresiasi_total_gedung = (luas_bangunan * btb_baru) * (min(1.0, umur_aktual / umur_ekonomis))

st.sidebar.markdown("---")
st.sidebar.header("🚦 4. Penyesuaian Karakteristik")
mobilitas = st.sidebar.selectbox("Tingkat Mobilitas / Traffic", ["Tinggi", "Sedang", "Rendah"])
jenis_atm = st.sidebar.selectbox("Jenis Mesin ATM", ["Setor Tarik (CRM)", "Tarik Tunai Saja"])
jarak_jalan_utama = st.sidebar.number_input("Jarak ke Jalan Utama (Meter)", min_value=0, value=10)

# Konversi Kualitatif menjadi Penyesuaian Nominal Rupiah (Sesuaikan dengan data pasar Anda)
nilai_adj_mobilitas = 15000000 if mobilitas == "Tinggi" else (5000000 if mobilitas == "Sedang" else 0)
nilai_adj_jenis = 10000000 if jenis_atm == "Setor Tarik (CRM)" else 0
nilai_adj_jarak = max(0, (100 - jarak_jalan_utama) * 150000) # Semakin dekat jalan utama, penyesuaian semakin tinggi

total_penyesuaian = nilai_adj_mobilitas + nilai_adj_jenis + nilai_adj_jarak


# ==============================================================================
# PROSES UTAMA PERHITUNGAN MATEMATIKA (SESUAI INDIKASI FORMULA ANDA)
# ==============================================================================
# 1. nilai tanah atm = luas atm / luas efektif bangunan * luas tanah bangunan * harga tanah m2
nilai_tanah_atm = (luas_atm / luas_efektif_bangunan) * luas_tanah_total * harga_tanah_m2

# 2. nilai bangunan atm = luas atm / luas efektif bangunan * ((luas bangunan * btb) - depresiasi)
nilai_bangunan_bersih = (luas_bangunan * btb_baru) - depresiasi_total_gedung
nilai_bangunan_atm = (luas_atm / luas_efektif_bangunan) * nilai_bangunan_bersih

# 3. Nilai ATM = nilai tanah ATM + Nilai bangunan atm + penyesuaian lokasi, mobilitas, dan jenis atm
nilai_atm_total = nilai_tanah_atm + nilai_bangunan_atm + total_penyesuaian


# ==============================================================================
# TAMPILAN INTERFACE UTAMA: DUA TAB KALKULATOR
# ==============================================================================
# Menampilkan resume data fisik di bagian atas halaman utama
st.markdown("### 📋 Parameter Utama Terhitung")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Luas Efektif Bangunan", f"{luas_efektif_bangunan:.2f} m²", f"Efisiensi {int(persen_efektif*100)}%")
c2.metric("Nilai Proposional Tanah", f"Rp {nilai_tanah_atm:,.0f}")
c3.metric("Nilai Proporsional Bangunan", f"Rp {nilai_bangunan_atm:,.0f}")
c4.metric("Total Estimasi Nilai ATM", f"Rp {nilai_atm_total:,.0f}")

st.markdown("---")

tab1, tab2 = st.tabs(
    ["📊 Kalkulator 1: Hitung Nilai GIM", "💰 Kalkulator 2: Prediksi Harga Sewa Tahunan"]
)

# --- KALKULATOR 1: MENCARI GIM ---
with tab1:
    st.header("Kalkulator GIM (Gross Income Multiplier)")
    st.write("Menghitung indikasi nilai GIM objek dengan memasukkan data harga sewa tahunan yang telah diketahui.")

    harga_sewa_k1 = st.number_input(
        "Masukkan Harga Sewa Tahunan Eksisting / Aktual (Rp)",
        min_value=1000000,
        value=20000000,
        step=1000000,
        key="k1_sewa"
    )

    if harga_sewa_k1 > 0:
        # Rumus Anda: nilai GIM = nilai ATM / harga sewa
        gim_hasil = nilai_atm_total / harga_sewa_k1

        st.markdown("#### Ringkasan Analisis Nilai GIM:")
        st.success(f"### 📈 Nilai Indikasi GIM Objek: **{gim_hasil:.2f} x**")
        
        with st.expander("Lihat Detail Alur Formula Matematika"):
            st.latex(r"\text{Nilai Tanah ATM} = \frac{" + str(luas_atm) + "}{" + f"{luas_efektif_bangunan:.2f}" + r"} \times " + str(luas_tanah_total) + r" \times " + f"{harga_tanah_m2:,} = Rp\ {nilai_tanah_atm:,.0f}")
            st.latex(r"\text{Nilai Bangunan ATM} = \frac{" + str(luas_atm) + "}{" + f"{luas_efektif_bangunan:.2f}" + r"} \times \left((" + str(luas_bangunan) + r"\times" + f"{btb_baru:,}" + r") - " + f"{depresiasi_total_gedung:,.0f}" + r"\right) = Rp\ {nilai_bangunan_atm:,.0f}")
            st.latex(r"\text{Nilai ATM Total} = \text{Tanah} + \text{Bangunan} + \text{Penyesuaian} = Rp\ " + f"{nilai_atm_total:,.0f}")
            st.latex(r"\text{Nilai GIM} = \frac{\text{Nilai ATM Total}}{\text{Harga Sewa}} = " + f"{gim_hasil:.2f}")

# --- KALKULATOR 2: PREDIKSI HARGA SEWA ---
with tab2:
    st.header("Kalkulator Harga Sewa Tahunan")
    st.write("Menghitung proyeksi harga sewa tahunan yang ideal berdasarkan indikasi angka GIM pasar dari karakteristik sejenis.")

    gim_pasar_input = st.number_input(
        "GIM dari Pasar (Otomatis Tersinkronisasi dengan Database jika Ada)",
        min_value=0.1,
        value=gim_pasar_default,
        step=0.1,
        key="k2_gim"
    )

    if gim_pasar_input > 0:
        # Turunan rumus: Harga Sewa = Nilai ATM / GIM Pasar
        harga_sewa_prediksi = nilai_atm_total / gim_pasar_input

        st.markdown("#### Proyeksi Hasil Sewa:")
        st.info(f"### 💵 Estimasi Harga Sewa Tahunan Ideal: **Rp {harga_sewa_prediksi:,.0f} / Tahun**")
        st.caption("Rumus: Total Nilai ATM / GIM Pasar")

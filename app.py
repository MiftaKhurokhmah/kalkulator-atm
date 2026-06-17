import datetime
import numpy as np
import pandas as pd
import streamlit as st

# Set judul dan konfigurasi dasar halaman web
st.set_page_config(
    page_title="Kalkulator GIM & Sewa ATM", page_icon="🖥️", layout="wide"
)

st.title("🖥️ Kalkulator GIM & Prediksi Harga Sewa ATM oleh Kelompok 6 Prakerin MPP 2024")
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

# Baseline dasar GIM pasar berdasarkan data excel riil (setelah sewa dikurangi biaya listrik)
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
                batas_top = Q3 + (1.5 * IQR)

                df_clean = df[
                    (
                        pd.to_numeric(df[kolom_gim], errors="coerce")
                        >= batas_bawah
                    )
                    & (
                        pd.to_numeric(df[kolom_gim], errors="coerce")
                        <= batas_top
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
# Nilai adjustment jenis ATM disesuaikan menjadi 3 juta agar perbedaan sewa lebih rasional
nilai_adj_jenis = 3000000 if jenis_atm == "Setor Tarik (CRM)" else 0
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

# 2. Nilai bangunan ATM terdepresiasi
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
        "Menghitung indikasi nilai GIM objek dengan memasukkan data harga sewa tahunan aktual yang disesuaikan dengan komponen biaya listrik."
    )

    col_sewa_k1, col_listrik_k1 = st.columns(2)

    with col_sewa_k1:
        harga_sewa_k1 = st.number_input(
            "Masukkan Harga Sewa Tahunan Eksisting / Aktual (Rp)",
            min_value=1000000,
            value=20000000,
            step=1000000,
            key="k1_sewa",
        )

    with col_listrik_k1:
        opsi_listrik_k1 = st.selectbox(
            "Status Kontrak Sewa Eksisting",
            ["Include Listrik", "Tidak Include Listrik"],
            key="k1_listrik_opsi"
        )

    # Logika Pengurangan Pembagi: Jika include listrik, kurangi sewa aktual (i) dengan biaya listrik Rp3.000.000 untuk dapat nilai bersih (h)
    if opsi_listrik_k1 == "Include Listrik":
        biaya_listrik_k1 = 3000000
        harga_sewa_pembagi = harga_sewa_k1 - biaya_listrik_k1
    else:
        biaya_listrik_k1 = 0
        harga_sewa_pembagi = harga_sewa_k1

    if harga_sewa_pembagi > 0:
        gim_hasil = nilai_atm_total / harga_sewa_pembagi

        st.markdown("#### Ringkasan Analisis Nilai GIM:")
        st.success(f"### 📈 Nilai Indikasi GIM Objek: **{gim_hasil:.4f} x**")

        with st.expander("Lihat Detail Alur Formula Matematika (Sesuai Karakteristik Data)"):
            st.write(f"- **Nilai ATM Total (Pembilang):** Rp {nilai_atm_total:,.0f}")
            st.write(f"- **Harga Sewa Aktual (`i`):** Rp {harga_sewa_k1:,.0f}")
            st.write(f"- **Biaya Listrik Ditanggung Pemilik Lahan:** Rp {biaya_listrik_k1:,.0f}")
            st.write(f"- **Harga Sewa Bersih Pembagi (`h`):** Rp {harga_sewa_pembagi:,.0f}")
            st.markdown("---")
            
            st.latex(
                r"\text{Nilai GIM} = \frac{\text{Nilai ATM Total}}{\text{Harga Sewa Aktual (i)} - \text{Biaya Listrik}}"
            )
            st.latex(
                rf"\text{{Nilai GIM}} = \frac{{{nilai_atm_total:,.0f}}}{{{harga_sewa_k1:,.0f} - {biaya_listrik_k1:,.0f}}} = {gim_hasil:.4f}"
            )
    else:
        st.error("Error: Harga sewa setelah dikurangi biaya listrik tidak boleh kurang dari atau sama dengan Rp 0!")

# --- KALKULATOR 2: PREDIKSI HARGA SEWA (REVISI MULTI-OPSI GIM) ---
with tab2:
    st.header("Kalkulator Harga Sewa Tahunan")
    st.write(
        "Menghitung proyeksi harga sewa tahunan yang ideal berdasarkan angka GIM pasar dari karakteristik sejenis."
    )

    col_metode, col_gim_val, col_listrik = st.columns(3)

    with col_metode:
        metode_gim = st.radio(
            "Metode Penentuan GIM Pasar:",
            ["Otomatis dari Pasar (Sesuai Sidebar)", "Input Manual (Kustom)"],
            key="k2_metode"
        )

    with col_gim_val:
        # Jika memilih otomatis, kolom di-disable dan nilainya mengunci data sidebar
        if metode_gim == "Otomatis dari Pasar (Sesuai Sidebar)":
            gim_pasar_input = st.number_input(
                f"GIM Terkunci ({mobilitas})",
                value=float(gim_pasar_default),
                format="%.4f",
                disabled=True,
                key="k2_gim_auto"
            )
        else:
            gim_pasar_input = st.number_input(
                "Masukkan Angka GIM Manual",
                min_value=0.1,
                value=float(gim_pasar_default),
                step=0.1,
                format="%.4f",
                key="k2_gim_manual"
            )

    with col_listrik:
        opsi_listrik = st.selectbox(
            "Fasilitas Listrik",
            ["Include Listrik", "Tidak Include Listrik"],
            key="k2_listrik_opsi"
        )

    if gim_pasar_input > 0:
        # 1. Hitung nilai sewa bersih h dari formula dasar kapitalisasi GIM
        tarif_sewa_minus_listrik = nilai_atm_total / gim_pasar_input

        # 2. Tambahkan biaya listrik Rp3.000.000 ke atas nilai sewa bersih jika opsi Include Listrik dipilih
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

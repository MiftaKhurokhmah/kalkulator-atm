import numpy as np
import pandas as pd
import streamlit as st
import datetime

# Set judul dan konfigurasi dasar halaman web
st.set_page_config(
    page_title="Kalkulator GIM & Sewa ATM Berbasis Karakteristik", page_icon="🖥️", layout="wide"
)

st.title("🖥️ Kalkulator GIM & Prediksi Harga Sewa ATM (Matriks Karakteristik)")
st.write(
    "Aplikasi ini otomatis menyaring database pasar dan menghitung GIM hanya dari data pembanding yang karakteristiknya cocok."
)

# ==============================================================================
# SIDEBAR STEP 1: INTERFACE UTAMA DATA KARAKTERISTIK (DITARIK KE ATAS AGAR JADI FILTER)
# ==============================================================================
st.sidebar.header("🚦 1. Karakteristik Objek Penilaian")
mobilitas_dipilih = st.sidebar.selectbox("Tingkat Mobilitas / Traffic", ["Tinggi", "Sedang", "Rendah"])
jenis_atm_dipilih = st.sidebar.selectbox("Jenis Mesin ATM", ["Setor Tarik", "Tarik Tunai"])
akses_jalan_dipilih = st.sidebar.selectbox("Aksesibilitas Lokasi Jalan", ["Jalan Utama / Arteri", "Jalan Biasa / Masuk"])

# Konversi Kualitatif menjadi Penyesuaian Nominal Rupiah untuk Nilai ATM
nilai_adj_mobilitas = 15000000 if mobilitas_dipilih == "Tinggi" else (5000000 if mobilitas_dipilih == "Sedang" else 0)
nilai_adj_jenis = 10000000 if jenis_atm_dipilih == "Setor Tarik" else 0
nilai_adj_jalan = 15000000 if akses_jalan_dipilih == "Jalan Utama / Arteri" else 0
total_penyesuaian = nilai_adj_mobilitas + nilai_adj_jenis + nilai_adj_jalan

# ==============================================================================
# SIDEBAR STEP 2: UPLOAD & FILTER DATABASE SEJENIS (DINAMIS)
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("📁 2. Database Pembanding")
file_diupload = st.sidebar.file_uploader("Upload File CSV Pembanding", type=["csv"])

gim_pasar_final = 13.5  # Standar baseline global jika tidak ada data cocok/tidak upload file
status_filter_pesan = "ℹ️ Menggunakan baseline standar GIM pasar global: 13.5"

if file_diupload is not None:
    try:
        df = pd.read_csv(file_diupload)
        df.columns = df.columns.str.strip() # Bersihkan space nama kolom

        # Deteksi Kolom Esensial di CSV Anda
        kolom_gim = "GIM" if "GIM" in df.columns else ("gim" if "gim" in df.columns else None)
        kolom_mobilitas = "Mobilitas" if "Mobilitas" in df.columns else ("mobilitas" if "mobilitas" in df.columns else None)
        kolom_jenis = "Jenis ATM" if "Jenis ATM" in df.columns else ("jenis_atm" if "jenis_atm" in df.columns else None)
        
        if kolom_gim and kolom_mobilitas and kolom_jenis:
            # 1. Bersihkan data GIM dari karakter non-numerik atau string error
            df[kolom_gim] = pd.to_numeric(df[kolom_gim], errors='coerce')
            df = df.dropna(subset=[kolom_gim])

            # 2. PROSES FILTER UTAMA: Hanya ambil baris yang karakteristiknya SAMA dengan input user
            # Mencocokkan string (mengabaikan huruf besar/kecil dan spasi)
            df_filtered = df[
                (df[kolom_mobilitas].str.strip().str.lower() == mobilitas_dipilih.lower()) &
                (df[kolom_jenis].str.strip().str.lower().str.contains(jenis_atm_dipilih.lower()))
            ]

            if len(df_filtered) > 0:
                # 3. Hilangkan Outlier dari data yang sudah terfilter (IQR Method)
                Q1 = df_filtered[kolom_gim].quantile(0.25)
                Q3 = df_filtered[kolom_gim].quantile(0.75)
                IQR = Q3 - Q1
                df_clean = df_filtered[
                    (df_filtered[kolom_gim] >= (Q1 - 1.5 * IQR)) & 
                    (df_filtered[kolom_gim] <= (Q3 + 1.5 * IQR))
                ]
                
                # Mengambil rata-rata GIM dari pembanding yang karakternya sama ruko/booth-nya
                gim_pasar_final = df_clean[kolom_gim].mean()
                status_filter_pesan = (
                    f"✅ Sukses Sinkronisasi Karakteristik!\n"
                    f"- Menemukan {len(df_clean)} data pembanding sejenis di database.\n"
                    f"- Nilai GIM Pasar Spesifik: {gim_pasar_final:.2f}"
                )
            else:
                # Jika tidak ada ruko/booth pembanding di Excel yang mirip dengan kombinasi karakteristik tersebut
                gim_pasar_final = df[kolom_gim].mean() # Fallback ke rata-rata total database
                status_filter_pesan = (
                    f"⚠️ Karakteristik spesifik tidak ditemukan di database!\n"
                    f"- Menggunakan rata-rata umum seluruh isi excel: {gim_pasar_final:.2f}"
                )
        else:
            st.sidebar.error("Struktur kolom CSV tidak lengkap (Wajib ada kolom: GIM, Mobilitas, Jenis ATM)")
    except Exception as e:
        st.sidebar.error(f"Gagal memproses penyaringan data: {e}")

st.sidebar.success(status_filter_pesan)

# ==============================================================================
# SIDEBAR STEP 3: DATA DIMENSI FISIK & BANGUNAN INDUK
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("📐 3. Data Fisik & Bangunan")
luas_atm = st.sidebar.number_input("Luas Lantai ATM (m²)", min_value=0.1, value=2.0, step=0.5)
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

# Logika Depresiasi
tahun_sekarang = datetime.date.today().year
umur_ekonomis = 20
umur_aktual = max(0, tahun_sekarang - tahun_dibangun)
depresiasi_total_gedung = (luas_bangunan * btb_baru) * (min(1.0, umur_aktual / umur_ekonomis))


# ==============================================================================
# PROSES UTAMA PERHITUNGAN MATEMATIKA (SESUAI RUMUS USER)
# ==============================================================================
# 1. Nilai tanah atm
nilai_tanah_atm = (luas_atm / luas_efektif_bangunan) * luas_tanah_total * harga_tanah_m2

# 2. Nilai bangunan atm
nilai_bangunan_bersih = (luas_bangunan * btb_baru) - depresiasi_total_gedung
nilai_bangunan_atm = (luas_atm / luas_efektif_bangunan) * nilai_bangunan_bersih

# 3. Total Nilai Indikasi Booth ATM
nilai_atm_total = nilai_tanah_atm + nilai_bangunan_atm + total_penyesuaian


# ==============================================================================
# TAMPILAN INTERFACE UTAMA
# ==============================================================================
st.markdown("### 📊 Status Karakteristik & Parameter Terhitung")
c1, c2, c3, c4 = st.columns(4)
c1.metric("GIM Karakteristik Pasar", f"{gim_pasar_final:.2f} x", f"Kombinasi Terpilih")
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
    
    harga_sewa_k1 = st.number_input("Harga Sewa Tahunan Riil Objek (Rp)", min_value=1000000, value=20000000, step=1000000, key="k1_sewa")
    
    if harga_sewa_k1 > 0:
        gim_hasil = nilai_atm_total / harga_sewa_k1
        st.success(f"### 📈 Indikasi GIM Objek Anda: **{gim_hasil:.2f} x**")
        
        # Evaluasi terhadap pasar
        selisih = gim_hasil - gim_pasar_final
        if abs(selisih) <= 1.5:
            st.write("💡 *Keterangan: GIM objek Anda berada di rentang wajar rata-rata karakteristik pasar sejenis.*")
        elif selisih > 1.5:
            st.write("⚠️ *Keterangan: GIM objek Anda cukup tinggi dibanding pasar sejenis (Kemungkinan harga sewa kemurahan atau nilai properti terlalu tinggi).*")
        else:
            st.write("⚠️ *Keterangan: GIM objek Anda rendah dibanding pasar sejenis (Kemungkinan harga sewa kemahalan).*")

# --- TAB 2 ---
with tab2:
    st.header("Kalkulator Proyeksi Harga Sewa Wajar")
    st.write("Menghitung harga sewa tahunan menggunakan GIM pasar yang sudah terfilter otomatis berdasarkan kemiripan karakteristik.")
    
    gim_yang_dipakai = st.number_input("GIM Pasar yang Digunakan (Tersinkron Otomatis dari Hasil Saringan)", min_value=0.1, value=gim_pasar_final, step=0.1, key="k2_gim")
    
    if gim_yang_dipakai > 0:
        harga_sewa_prediksi = nilai_atm_total / gim_yang_dipakai
        st.info(f"### 💵 Rekomendasi Harga Sewa Ideal Berdasarkan Karakteristik Sejenis: **Rp {harga_sewa_prediksi:,.0f} / Tahun**")
        
        with st.expander("Lihat Logika Penyaringan Karakteristik"):
            st.write(f"- Sistem mendeteksi Anda memilih tingkat mobilitas: **{mobilitas_dipilih}** dan jenis ATM: **{jenis_atm_dipilih}**.")
            st.write("- Aplikasi memotong isi file Excel Anda, membuang data yang tidak cocok, lalu membuang data ekstrem (outlier).")
            st.write(f"- Menghasilkan nilai GIM acuan khusus sebesar **{gim_yang_dipakai:.2f}**, bukan rata-rata buta dari keseluruhan isi excel.")

import streamlit as str
from datetime import datetime

st.set_page_config(page_title="Kalkulator Penilaian Booth ATM", layout="wide")
st.title("🧮 Kalkulator Penilaian Properti & Sewa Booth ATM")
st.write("Berdasarkan formulasi nilai tanah proporsional, nilai bangunan proporsional, dan GIM (*Gross Income Multiplier*).")

# ==========================================
# SIDEBAR: INPUT DATA BERSAMA
# ==========================================
st.sidebar.header("📥 Input Karakteristik Objek")

# Dimensi Fisik
luas_atm = st.sidebar.number_input("Luas Lantai ATM (m²)", min_value=0.1, value=1.0, step=0.1)
luas_bangunan = st.sidebar.number_input("Luas Bangunan Total Gedung (m²)", min_value=1.0, value=100.0)
jumlah_lantai = st.sidebar.number_input("Jumlah Lantai Gedung", min_value=1, value=1)
luas_tanah_total = st.sidebar.number_input("Luas Tanah Total Gedung (m²)", min_value=1.0, value=150.0)

# Persentase Luas Efektif Otomatis
persen_efektif = 1.0 if jumlah_lantai == 1 else 0.7
luas_efektif = luas_bangunan * persen_efektif

# Nilai Pasar Komponen
harga_tanah_m2 = st.sidebar.number_input("Harga Tanah per m² (Rp)", min_value=0, value=5000000, step=500000)
harga_btb_baru_m2 = st.sidebar.number_input("Harga BTB Bangunan Baru per m² (Rp)", min_value=0, value=4000000, step=500000)

# Umur & Depresiasi
tahun_dibangun = st.sidebar.number_input("Tahun Bangunan Didirikan", min_value=1980, max_value=2026, value=2016)
umur_ekonomis = st.sidebar.number_input("Umur Ekonomis Bangunan (Tahun)", min_value=1, value=20)
tahun_sekarang = 2026 # Disesuaikan dengan tahun berjalan

umur_aktual = max(0, tahun_sekarang - tahun_dibangun)
persen_depresiasi = min(1.0, umur_aktual / umur_ekonomis)

# Parameter Kualitatif (Penyesuaian Nilai dalam Rp)
st.sidebar.subheader("Faktor Penyesuaian (Nominal Rp)")
adj_mobilitas = st.sidebar.number_input("Penyesuaian Mobilitas (Rp)", value=0)
adj_jenis_atm = st.sidebar.number_input("Penyesuaian Jenis ATM (Rp)", value=0)
adj_jarak_jalan = st.sidebar.number_input("Penyesuaian Jarak ke Jalan Utama (Rp)", value=0)
total_penyesuaian = adj_mobilitas + adj_jenis_atm + adj_jarak_jalan

# ==========================================
# PROSES PERHITUNGAN DASAR (LOGIKA MATEMATIKA)
# ==========================================
# 1. Nilai Tanah ATM
# Rumus: (Luas ATM / Luas Efektif) * Luas Tanah * Harga Tanah per m2
nilai_tanah_atm = (luas_atm / luas_efektif) * luas_tanah_total * harga_tanah_m2

# 2. Nilai Bangunan ATM (terdepresiasi)
harga_bangunan_total = luas_bangunan * harga_btb_baru_m2
depresiasi_total = harga_bangunan_total * persen_depresiasi
nilai_bangunan_bersih = harga_bangunan_total - depresiasi_total
nilai_bangunan_atm = (luas_atm / luas_efektif) * nilai_bangunan_bersih

# 3. Total Nilai ATM
nilai_atm_total = nilai_tanah_atm + nilai_bangunan_atm + total_penyesuaian


# ==========================================
# TAMPILAN UTAMA: DUA KALKULATOR
# ==========================================
tab1, tab2 = st.tabs(["📊 Kalkulator 1: Mencari Nilai GIM", "💰 Kalkulator 2: Mencari Harga Sewa Tahunan"])

with tab1:
    st.header("Kalkulator Nilai GIM")
    st.write("Gunakan ini jika Anda sudah mengetahui **Harga Sewa Saat Ini** dan ingin tahu berapa angka GIM properti tersebut.")
    
    harga_sewa_input = st.number_input("Harga Sewa per Tahun Saat Ini (Rp)", min_value=1000000, value=25000000, step=1000000, key="sewa_k1")
    
    if harga_sewa_input > 0:
        gim_hasil = nilai_atm_total / harga_sewa_input
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Nilai Tanah ATM", f"Rp {nilai_tanah_atm:,.0f}")
        col2.metric("Nilai Bangunan ATM", f"Rp {nilai_bangunan_atm:,.0f}")
        col3.metric("Total Estimasi Nilai ATM", f"Rp {nilai_atm_total:,.0f}")
        
        st.success(f"### 📈 Nilai Indikasi GIM: **{gim_hasil:.2f}x**")

with tab2:
    st.header("Kalkulator Harga Sewa Tahunan")
    st.write("Gunakan ini jika Anda memiliki target atau data pasar **GIM Pembanding** dan ingin memproyeksikan **Harga Sewa Wajar**.")
    
    gim_input = st.number_input("Masukkan GIM Pasar Pembanding (x)", min_value=0.1, value=15.0, step=0.5, key="gim_k2")
    
    if gim_input > 0:
        harga_sewa_hasil = nilai_atm_total / gim_input
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Estimasi Nilai ATM", f"Rp {nilai_atm_total:,.0f}")
        col2.metric("GIM Pasar yang Digunakan", f"{gim_input} x")
        col3.metric("Rekomendasi Sewa / Tahun", f"Rp {harga_sewa_hasil:,.0f}")
        
        st.info(f"### 💵 Estimasi Harga Sewa Tahunan Ideal: **Rp {harga_sewa_hasil:,.0f}**")

# Info Tambahan Logika Ringkas
st.markdown("---")
with st.expander("👁️ Lihat Detail Indikator Internal Bangunan"):
    st.write(f"- **Luas Efektif Bangunan ({int(persen_efektif*100)}%):** {luas_efektif:.2f} m²")
    st.write(f"- **Umur Aktual Bangunan:** {umur_aktual} Tahun")
    st.write(f"- **Persentase Depresiasi Bangunan:** {persen_depresiasi*100:.1f}%")
    st.write(f"- **Total Akumulasi Penyesuaian Karakteristik:** Rp {total_penyesuaian:,.0f}")

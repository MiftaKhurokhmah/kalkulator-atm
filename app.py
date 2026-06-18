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
# SIDEBAR INPUT: DATA KARAKTERISTIK OBJEK
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

# Klasifikasi Jenis Bangunan untuk Menentukan Umur Ekonomis secara Dinamis
jenis_bangunan = st.sidebar.selectbox(
    "Klasifikasi Jenis Bangunan Induk",
    [
        "Rumah Tinggal Sederhana (25 Tahun)",
        "Rumah Menengah (35 Tahun)",
        "Gedung ≤ 4 Lantai (45 Tahun)",
        "Gedung > 4 Lantai (55 Tahun)"
    ]
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

# Pemetaan Umur Ekonomis berdasarkan kriteria user
if "Rumah Tinggal Sederhana" in jenis_bangunan:
    umur_ekonomis = 25
elif "Rumah Menengah" in jenis_bangunan:
    umur_ekonomis = 35
elif "Gedung ≤ 4 Lantai" in jenis_bangunan:
    umur_ekonomis = 45
else:
    umur_ekonomis = 55

# Perhitungan Depresiasi Bangunan Dinamis: (Tahun Ini - Tahun Berdiri) / Umur Ekonomis
tahun_sekarang = datetime.date.today().year
umur_aktual = max(0, tahun_sekarang - tahun_dibangun)
rasio_depresiasi = min(1.0, umur_aktual / umur_ekonomis)
depresiasi_total_gedung = (luas_bangunan * btb_baru) * rasio_depresiasi

st.sidebar.caption(
    f"Umur Aktual: {umur_aktual} tahun | Depresiasi: {rasio_depresiasi*100:.1f}%"
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

# INTERPOLASI DATA BARU (VERSI DATA C)
if mobilitas == "Ramai":
    gim_pasar_default = 2.4430
elif mobilitas == "Sedang":
    gim_pasar_default = 1.7043
else:  # Sepi
    gim_pasar_default = 2.8581

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
                st.sidebar.error("Tidak ada data angka yang valid di kolom GIM.")
        else:
            st.sidebar.error("Kolom 'GIM' tidak ditemukan!")
    except Exception as e:
        st.sidebar.error(f"Gagal memproses file: {e}")
else:
    st.sidebar.info(
        f"ℹ️ Baseline GIM ({mobilitas}): {gim_pasar_default:.4f}"
    )

# Konversi Kualitatif menjadi Penyesuaian Nominal Rupiah untuk karakteristik non-GIM
nilai_adj_jenis = 1000000 if jenis_atm == "Tarik Tunai Saja" else 0
nilai_adj_jarak = max(0, (100 - jarak_jalan_utama) * 150000)

total_penyesuaian = nilai_adj_jenis + nilai_adj_jarak


# ==============================================================================
# PROSES UTAMA PERHITUNGAN MATEMATIKA
# ==============================================================================
# 1. Nilai tanah ATM
nilai_tanah_atm = (
    (luas_atm / luas_efektif_bangunan) * luas_tanah_total * harga_tanah_m2
)

# 2. Nilai bangunan ATM terdepresiasi
nilai_bangunan_gedung_baru = luas_bangunan * btb_baru
nilai_bangunan_bersih = nilai_bangunan_gedung_baru - depresiasi_total_gedung
nilai_bangunan_atm = (luas_atm / luas_efektif_bangunan) * nilai_bangunan_bersih

# 3. Nilai ATM Total (Pembilang untuk GIM dan Pembagi Tarif Sewa)
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
        "Menghitung indikasi nilai GIM objek dengan memasukkan data harga sewa tahunan aktual."
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

        with st.expander("🔍 Lihat Detail Alur Perhitungan & Struktur Logika Pembilang", expanded=True):
            st.markdown("#### 1. Komponen Pembilang: Perhitungan Nilai Space/Booth ATM")
            
            # Detail Tanah
            st.write(f"**A. Nilai Proporsional Tanah:**")
            st.markdown(
                f"""
                * Rumus: `(Luas ATM / Luas Efektif Bangunan) * Luas Tanah Total * Harga Tanah per m²`
                * Kalkulasi: `({luas_atm} / {luas_efektif_bangunan:.2f}) * {luas_tanah_total} * Rp {harga_tanah_m2:,.0f}`
                * Hasil Nilai Tanah Proporsional = **Rp {nilai_tanah_atm:,.0f}**
                """
            )
            
            # Detail Depresiasi & Bangunan
            st.write(f"**B. Nilai Proporsional Bangunan Terdepresiasi:**")
            st.markdown(
                f"""
                * Jenis Bangunan Induk: `{jenis_bangunan}` $\\rightarrow$ Umur Ekonomis = **{umur_ekonomis} Tahun**
                * Akumulasi Penyusutan: `({tahun_sekarang} - {tahun_dibangun}) / {umur_ekonomis} = {umur_aktual}/{umur_ekonomis} ({rasio_depresiasi*100:.1f}%)`
                * Nilai Bersih Bangunan Induk: `Rp {nilai_bangunan_gedung_baru:,.0f} - Rp {depresiasi_total_gedung:,.0f} = Rp {nilai_bangunan_bersih:,.0f}`
                * Proporsi Bangunan ATM: `({luas_atm} / {luas_efektif_bangunan:.2f}) * Rp {nilai_bangunan_bersih:,.0f}`
                * Hasil Nilai Bangunan Proporsional = **Rp {nilai_bangunan_atm:,.0f}**
                """
            )

            # Detail Penyesuaian
            st.write(f"**C. Faktor Penyesuaian Karakteristik (Adjustment Nominal):**")
            st.markdown(
                f"""
                * Penyesuaian Jenis ATM (`{jenis_atm}`): `Rp {nilai_adj_jenis:,.0f}`
                * Penyesuaian Jarak ke Jalan Utama (`{jarak_jalan_utama} meter`): `Rp {nilai_adj_jarak:,.0f}`
                * Total Tambahan Nilai Penyesuaian = **Rp {total_penyesuaian:,.0f}**
                """
            )

            st.info(f"**🟢 Total Nilai Space ATM (Pembilang) = A + B + C = Rp {nilai_atm_total:,.0f}**")

            st.markdown("---")
            st.markdown("#### 2. Komponen Pembagi & Nilai GIM Akhir")
            st.markdown(
                f"""
                * Harga Sewa Aktual yang Diinput (`i`): **Rp {harga_sewa_k1:,.0f}**
                * Pengurangan Komponen Listrik: **Rp {biaya_listrik_k1:,.0f}**
                * **Harga Sewa Bersih Pembagi (`h`):** `Rp {harga_sewa_k1:,.0f} - Rp {biaya_listrik_k1:,.0f} = Rp {harga_sewa_pembagi:,.0f}`
                """
            )
            
            st.latex(
                rf"\text{{Nilai GIM Objek}} = \frac{{\text{{Rp }}{nilai_atm_total:,.0f}}}{{\text{{Rp }}{harga_sewa_pembagi:,.0f}}} = {gim_hasil:.4f}"
            )
    else:
        st.error("Error: Harga sewa bersih pembagi tidak boleh kurang dari atau sama dengan Rp 0!")

# --- KALKULATOR 2: PREDIKSI HARGA SEWA ---
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
        if metode_gim == "Otomatis dari Pasar (Sesuai Sidebar)":
            gim_pasar_input = st.number_input(
                f"GIM Terkunci ({mobilitas})",
                min_value=0.0,
                max_value=10.0,
                value=float(gim_pasar_default),
                format="%.4f",
                disabled=True,
                key=f"k2_gim_auto_{mobilitas}"
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
        # Tarif sewa bersih (h) = Nilai Booth / GIM Pasar
        tarif_sewa_minus_listrik = nilai_atm_total / gim_pasar_input

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

        # ==============================================================================
        # BLOK JUSTIFIKASI EKONOMI DAN PENGETAHUAN PENGGUNA (VERSI DATA C)
        # ==============================================================================
        st.markdown("---")
        st.markdown("### 💡 Mengapa Angka GIM Variatif & Dinamis? (Justifikasi Data Pasar)")
        st.info(
            f"""
            Analisis ini menggunakan rujukan data pasar riil yang telah diolah: 
            * **Ramai:** `2.4430` | **Sedang:** `1.7043` | **Sepi:** `2.8581`
            
            Mungkin Anda menyadari adanya anomali di mana **Lokasi Sepi memiliki nilai GIM yang lebih tinggi** dibandingkan Lokasi Sedang maupun Ramai. Berikut rincian analisis dasarnya:
            
            1. **🔴 Lokasi Sepi (GIM Tertinggi — {2.8581:.4f}x):** Di area yang sepi, harga sewa tahunan drop menjadi sangat murah. Namun, biaya untuk membangun fisik ATM (seperti beton, kaca, AC, dan interior standar) memiliki batas minimum yang tidak bisa ikut murah begitu saja. Karena nilai fisik bangunan yang konstan ini dibagi dengan harga sewa yang sangat kecil, hasil rasionya (GIM) otomatis melonjak tinggi.
               
            2. **🟢 Lokasi Ramai (GIM Tinggi — {2.4430:.4f}x):** Di zona premium, nilai tanahnya sudah pasti sangat mahal. Meskipun pihak bank berani membayar harga sewa yang tinggi, tingginya nilai investasi tanah dan properti di sana membuat angka pengalinya tetap berada di level yang kuat.
               
            3. **🔵 Lokasi Sedang (GIM Paling Efisien — {1.7043:.4f}x):** Ini adalah titik keseimbangan (*sweet spot*) di pasar. Di lokasi sedang, nilai properti dan harga sewa tahunan yang berlaku di lapangan saling mengimbangi secara proporsional, sehingga menghasilkan nilai pengali yang lebih rendah dan efisien bagi kedua belah pihak.
            """
        )

        with st.expander("🔍 Lihat Detail Alur Perhitungan & Struktur Validasi Formula", expanded=True):
            st.markdown("#### 1. Komponen Dasar yang Digunakan")
            st.markdown(
                f"""
                * **Nilai Space/Booth ATM Terhitung:** Rp {nilai_atm_total:,.0f} *(Gabungan proporsional Tanah + Bangunan Depresiasi + Adjustment)*
                * **Angka Indikator GIM Pasar (`GIM`):** {gim_pasar_input:.4f} *(Tingkat mobilitas: {mobilitas})*
                """
            )
            
            st.markdown("---")
            st.markdown("#### 2. Langkah Perhitungan Tarif (Sesuai Struktur Rumus)")
            st.write("**Langkah A: Menghitung Tarif Sewa Bersih Tanpa Komponen Listrik (`h`):**")
            st.latex(
                rf"h = \frac{{\text{{Nilai Space ATM}}}}{{\text{{GIM Pasar}}}} = \frac{{\text{{Rp }}{nilai_atm_total:,.0f}}}{{{gim_pasar_input:.4f}}} = \text{{Rp }}{tarif_sewa_minus_listrik:,.0f}"
            )
            
            st.write("**Langkah B: Menyesuaikan Kontrak Fasilitas Listrik Terpilih:**")
            st.markdown(
                f"""
                * Pilihan Fasilitas: `{opsi_listrik}`
                * Tambahan Biaya Listrik: **Rp {biaya_listrik:,.0f}**
                """
            )
            
            st.write("**Langkah C: Rumus Akhir Estimasi Tarif Sewa per Tahun (`i`):**")
            if opsi_listrik == "Include Listrik":
                st.latex(
                    rf"i = h + \text{{Biaya Listrik}} = \text{{Rp }}{tarif_sewa_minus_listrik:,.0f} + \text{{Rp }}{biaya_listrik:,.0f}"
                )
            else:
                st.latex(
                    rf"i = h = \text{{Rp }}{tarif_sewa_minus_listrik:,.0f}"
                )
                
            st.success(f"### 🎉 Rekomendasi Nilai Sewa Wajar (`i`) = **Rp {harga_sewa_prediksi:,.0f} / Tahun**")

import numpy as np
import pandas as pd
import streamlit as st

# Set judul dan konfigurasi dasar halaman web
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
file_diupload = st.sidebar.file_uploader(
    "Upload File CSV Pembanding", type=["csv"]
)

gim_pasar_default = 13.5  # Nilai default jika belum ada file yang diupload

if file_diupload is not None:
    try:
        # Membaca file CSV
        df = pd.read_csv(file_diupload)

        # Membersihkan spasi pada nama kolom
        df.columns = df.columns.str.strip()

        # Cek ketersediaan kolom GIM (fleksibel huruf besar/kecil)
        kolom_gim = None
        if "GIM" in df.columns:
            kolom_gim = "GIM"
        elif "gim" in df.columns:
            kolom_gim = "gim"

        if kolom_gim is not None:
            # Konversi data ke numerik dan buang nilai kosong atau eror (#DIV/0!)
            data_gim = pd.to_numeric(df[kolom_gim], errors="coerce").dropna()

            if len(data_gim) > 0:
                # Hitung batasan IQR untuk membuang outlier
                Q1 = data_gim.quantile(0.25)
                Q3 = data_gim.quantile(0.75)
                IQR = Q3 - Q1

                batas_bawah = Q1 - (1.5 * IQR)
                batas_atas = Q3 + (1.5 * IQR)

                # Filter data bersih (Non-Outlier)
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

                # Hitung rata-rata baru dari data bersih
                gim_pasar_default = pd.to_numeric(
                    df_clean[kolom_gim], errors="coerce"
                ).mean()

                st.sidebar.success(
                    f"✅ Database Berhasil Diproses!\n"
                    f"- Total Data Awal: {len(df)} baris\n"
                    f"- Data Setelah Outlier Dibuang: {len(df_clean)} baris\n"
                    f"- Rata-rata GIM Pasar Aktual: {gim_pasar_default:.2f}"
                )
            else:
                st.sidebar.error(
                    "Tidak ada data angka yang valid di kolom GIM."
                )
        else:
            st.sidebar.error(
                "Kolom 'GIM' tidak ditemukan. Periksa nama kolom di file Anda!"
            )

    except Exception as e:
        st.sidebar.error(f"Gagal memproses file: {e}")
else:
    st.sidebar.info(
        f"ℹ️ Belum ada database diupload. Menggunakan standar baseline GIM pasar default: {gim_pasar_default}"
    )


# ==============================================================================
# TAMPILAN UTAMA: MEMBAGI MENJADI 2 KALKULATOR (TAB)
# ==============================================================================
tab1, tab2 = st.tabs(
    ["📊 Kalkulator 1: Mencari GIM", "💰 Kalkulator 2: Prediksi Harga Sewa"]
)

# --- TAB 1: KALKULATOR MENCARI GIM ---
with tab1:
    st.header("Kalkulator 1: Menentukan GIM Properti Baru")
    st.write(
        "Gunakan jika Anda tahu harga sewa tahunan ruko/properti induk dan ingin mencari nilai GIM ruko tersebut."
    )

    col1, col2 = st.columns(2)
    with col1:
        sewa_k1 = st.number_input(
            "Harga Sewa Tahunan Eksisting (Rp)",
            value=25000000,
            step=1000000,
            key="sewa1",
        )
        luas_tanah_k1 = st.number_input(
            "Luas Tanah Total Properti (m²)", value=150, step=10, key="lt1"
        )
        harga_penawaran_k1 = st.number_input(
            "Harga Penawaran Tanah per m² (Rp)",
            value=4500000,
            step=500000,
            key="hp1",
        )
        diskon_k1 = (
            st.slider(
                "Faktor Diskon / Ruang Nego Tanah (%)",
                0,
                50,
                10,
                step=5,
                key="disk1",
            )
            / 100.0
        )

    with col2:
        luas_bangunan_k1 = st.number_input(
            "Luas Bangunan Total Properti (m²)", value=100, step=10, key="lb1"
        )
        btb_k1 = st.number_input(
            "Biaya Bangunan Baru (BTB) per m² (Rp)",
            value=4000000,
            step=500000,
            key="btb1",
        )
        tahun_berdiri_k1 = st.number_input(
            "Tahun Bangunan Berdiri",
            value=2018,
            min_value=1980,
            max_value=2026,
            key="thn1",
        )

    # Logika Hitung Kalkulator 1
    harga_tanah_terkoreksi = harga_penawaran_k1 * (1 - diskon_k1)
    tanah_bersih = luas_tanah_k1 * harga_tanah_terkoreksi

    umur_aktual = max(0, 2026 - tahun_berdiri_k1)
    depresiasi = min(1.0, umur_aktual / 20)  # Asumsi umur ekonomis bangunan 20 thn
    bangunan_pasar = (luas_bangunan_k1 * btb_k1) * (1 - depresiasi)

    properti_total = tanah_bersih + bangunan_pasar
    gim_hasil = properti_total / sewa_k1 if sewa_k1 > 0 else 0

    st.markdown("---")
    st.subheader("📋 Ringkasan Hasil Analisis Properti (Kalkulator 1):")
    st.write(
        f"• Nilai Dasar Tanah Ternegosiasi: **Rp {harga_tanah_terkoreksi:,.2f} / m²**"
    )
    st.write(f"• Total Nilai Aset Tanah: **Rp {tanah_bersih:,.2f}**")
    st.write(
        f"• Nilai Realistis Bangunan (Setelah Penyusutan {depresiasi*100:.0f}%): **Rp {bangunan_pasar:,.2f}**"
    )
    st.write(
        f"• Estimasi Total Nilai Properti Kedudukan Ruko: **Rp {properti_total:,.2f}**"
    )
    st.write("")
    st.metric(label="HASIL HITUNG NILAI GIM PROPERTI", value=f"{gim_hasil:.2f}")


# --- TAB 2: KALKULATOR PREDIKSI HARGA SEWA (UPDATE: LUAS EFEKTIF) ---
with tab2:
    st.header("Kalkulator 2: Memprediksi Harga Sewa ATM")
    st.write(
        "Gunakan jika Anda ingin mencari rekomendasi tarif harga sewa space ATM yang ideal berbasis proporsional luas efektif."
    )

    gim_digunakan = st.number_input(
        "GIM Benchmark Pasar yang Digunakan (Otomatis Tersinkron Database)",
        value=gim_pasar_default,
        step=0.1,
        key="gim_ref",
    )

    col3, col4 = st.columns(2)
    with col3:
        luas_atm = st.number_input(
            "Luas Lantai ATM (m²)", value=3.0, step=0.5, key="la2"
        )
        l_tanah_total = st.number_input(
            "Luas Tanah Total Gedung Induk (m²)", value=200, step=10, key="lt2"
        )
        h_tanah_m2 = st.number_input(
            "Harga Pasar Tanah Wilayah per m² (Rp)",
            value=3500000,
            step=500000,
            key="ht2",
        )
        # UPDATE: Menggunakan Luas Bangunan Efektif sebagai variabel utama
        l_bangunan_efektif = st.number_input(
            "Luas Bangunan Efektif Gedung Induk (m²)",
            value=100,
            step=5,
            key="lb_efektif2",
        )

    with col4:
        btb_k2 = st.number_input(
            "BTB Gedung Induk per m² (Rp)",
            value=4500000,
            step=500000,
            key="btb2",
        )
        tahun_berdiri_k2 = st.number_input(
            "Tahun Berdiri Gedung Induk",
            value=2020,
            min_value=1980,
            max_value=2026,
            key="thn2",
        )
        tipe_mesin = st.selectbox(
            "Tipe Fungsi Mesin ATM",
            ["CRM (Setor Tarik)", "ATM (Tarik Tunai Saja)"],
            key="mesin2",
        )
        listrik = st.radio(
            "Fasilitas Biaya Listrik",
            ["Include Listrik (Ditanggung Gedung)", "Exclude Listrik"],
            key="list2",
        )
        akses_jalan = st.selectbox(
            "Aksesibilitas Lokasi Jalan",
            ["Jalan Utama / Arteri", "Jalan Biasa / Masuk"],
            key="jalan2",
        )

    # --- LOGIKA HITUNG KALKULATOR 2 DENGAN LUAS EFEKTIF ---
    # 1. Nilai tanah proporsional ATM terhadap Luas Tanah Gedung Induk
    rasio_tanah = luas_atm / l_tanah_total
    v_tanah_atm = (l_tanah_total * h_tanah_m2) * rasio_tanah

    # 2. Nilai bangunan proporsional ATM terhadap Luas Bangunan Efektif
    umur_akt_k2 = max(0, 2026 - tahun_berdiri_k2)
    dep_k2 = min(1.0, umur_akt_k2 / 20)

    # Nilai depresiasi dihitung dari total luas bangunan efektif induk
    v_bangunan_dep = (l_bangunan_efektif * btb_k2) * (1 - dep_k2)
    rasio_bgn = luas_atm / l_bangunan_efektif
    v_bangunan_atm = v_bangunan_dep * rasio_bgn

    # 3. Total nilai space fisik ATM
    total_space_atm = v_tanah_atm + v_bangunan_atm

    # 4. Faktor Penyesuaian Jalan dan Sewa Dasar Bersih
    f_jalan = 1.2 if akses_jalan == "Jalan Utama / Arteri" else 1.0
    sewa_dasar = (
        (total_space_atm * f_jalan) / gim_digunakan if gim_digunakan > 0 else 0
    )

    # 5. Penyesuaian Fasilitas Tambahan
    b_listrik = 12000000 if "Include" in listrik else 0
    b_crm = 3000000 if "CRM" in tipe_mesin else 0
    rekomendasi_sewa = sewa_dasar + b_listrik + b_crm

    st.markdown("---")
    st.subheader("📋 Komponen Perhitungan & Rekomendasi Sewa (Kalkulator 2):")
    st.write(
        f"• Rasio Luas ATM / Luas Bangunan Efektif Induk: **{rasio_bgn*100:.2f}%**"
    )
    st.write(f"• Nilai Tanah Proporsional (Luas ATM): **Rp {v_tanah_atm:,.2f}**")
    st.write(
        f"• Nilai Bangunan Proporsional (Berbasis Luas Efektif Terdepresiasi): **Rp {v_bangunan_atm:,.2f}**"
    )
    st.write(f"• Total Nilai Fisik Proposional Booth: **Rp {total_space_atm:,.2f}**")
    st.write(f"• Harga Sewa Dasar Bersih / Tahun: **Rp {sewa_dasar:,.2f}**")
    st.write(
        f"• Tambahan Operasional (Beban Listrik & Mekanis CRM): **Rp {b_listrik + b_crm:,.2f}**"
    )
    st.write("")
    st.success(
        f"💡 **REKOMENDASI TARIF SEWA ATM IDEAL: Rp {rekomendasi_sewa:,.2f} / Tahun**"
    )

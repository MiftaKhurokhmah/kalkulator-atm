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

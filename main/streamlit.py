# streamlit.py
import streamlit as st
import pandas as pd

# Import data dan fungsi dari backend (main.py)
try:
    from main import df_hotel, df_wisata_final, rekomendasi_wisata_dari_hotel, buat_paket_itinerary, hitung_analisis_sensitivitas
except ImportError as e:
    st.error(f"Gagal mengimpor file backend (main.py). Pastikan nama file dan foldernya sama! Error: {e}")

# Pastikan konfigurasi halaman ditaruh di paling atas kode UI
st.set_page_config(page_title="SPK Wisata DIY", layout="wide")

st.title("Sistem Pendukung Keputusan Wisata DIY")
st.write("### Metode Weighted Product (WP) - Backend & Frontend Terintegrasi")
st.write("NIM: 123240242 - Reinnent Rasika Z & Tim")
st.divider()

# Validasi apakah data dari backend kosong atau tidak
if 'df_hotel' not in locals() or df_hotel.empty:
    st.warning("Data hotel belum termuat dengan benar dari backend.")
else:
    # BIKIN TAB MENU UTAMA
    tab1, tab2, tab3 = st.tabs([
        "🔍 Rekomendasi Utama (Filter & Sort)", 
        "📦 Paket Itinerary Rute", 
        "📊 Analisis Sensitivitas Bobot"
    ])

    with tab1:
        st.header("Cari Wisata Berdasarkan Hotel Tempat Menginap")
        
        # Split Layout Input Kiri dan Kanan
        col_input, col_slider = st.columns([1, 1])
        
        with col_input:
            hotel_pilih = st.selectbox(
                "Pilih Lokasi Hotel Anda saat ini:", 
                df_hotel['NAMA PENGINAPAN'].dropna().unique().tolist()
            )
            
            kat_pilih = st.selectbox(
                "Filter Kategori Wisata:", 
                ["Semua"] + df_wisata_final['type'].dropna().unique().tolist()
            )
            
            budget_pilih = st.number_input(
                "Budget Tiket Masuk Maksimal (Rp):", 
                min_value=0, value=100000, step=5000
            )
            
            keyword_pilih = st.text_input(
                "Cari Kata Kunci Spesifik (Misal: Candi / Pantai):", 
                value=""
            )
            
            # FITUR SHORTCUT SORTING
            order_pilih = st.radio(
                "Urutan Hasil Rekomendasi (Shortcut Sorting):", 
                ["Skor Tertinggi ke Terendah (Descend)", "Skor Terendah ke Tertinggi (Ascend)"]
            )
            sort_order = 'descending' if "Tertinggi" in order_pilih else 'ascending'

        with col_slider:
            st.write("**Atur Bobot Kepentingan Kriteria (Semakin tinggi semakin prioritas):**")
            b_rate = st.slider("Rating Tempat Wisata (Benefit)", 1, 5, 4)
            b_pop = st.slider("Popularitas / Jumlah Ulasan (Benefit)", 1, 5, 3)
            b_harga = st.slider("Harga Tiket Murah (Cost)", 1, 5, 4)
            b_jarak = st.slider("Jarak Dekat dari Hotel (Cost)", 1, 5, 5)

        # Membungkus bobot ke dalam dictionary sesuai format main.py
        bobot_user = {
            'vote_average': b_rate, 
            'vote_count': b_pop,
            'htm_weekday': b_harga, 
            'htm_weekend': b_harga, 
            'jarak_ke_hotel': b_jarak
        }

        st.write("")
        if st.button("Hitung Rekomendasi Wisata", type="primary"):
            # Memanggil fungsi di main.py milikmu
            hasil = rekomendasi_wisata_dari_hotel(
                hotel_pilih, bobot_user, budget_pilih, kat_pilih, keyword_pilih, sort_order
            )
            
            if hasil.empty:
                st.warning("Tidak ada tempat wisata yang cocok dengan kombinasi filter Anda (Budget / Kata Kunci terlalu ketat).")
            else:
                st.success("Perhitungan Weighted Product Berhasil Dieksekusi!")
                kolon_tampil = ['nama', 'type', 'htm_weekday', 'jarak_ke_hotel', 'vote_average', 'Vector_V', 'Ranking']
                st.dataframe(hasil[kolon_tampil].head(10), use_container_width=True)

    with tab2:
        st.header("Fitur Paket Wisata Harian Terdekat (Itinerary)")
        st.write("Sistem akan mencarikan paket 3 objek wisata terdekat yang paling optimal berdasarkan lokasi hotel pilihan.")
        
        hotel_itinerary = st.selectbox(
            "Pilih Lokasi Hotel Awal:", 
            df_hotel['NAMA PENGINAPAN'].dropna().unique().tolist(), 
            key="itinerary_hotel"
        )
        radius_input = st.slider("Batas Maksimal Radius Wisata dari Hotel (KM):", 5, 30, 15)
        
        if st.button("Rekomendasikan Paket Rute Perjalanan"):
            paket = buat_paket_itinerary(hotel_itinerary, bobot_user, radius_input)
            if paket.empty:
                st.warning(f"Tidak ditemukan tempat wisata dalam radius {radius_input} KM dari hotel tersebut.")
            else:
                st.info(f"Berikut adalah 3 Destinasi Wisata Terbaik terdekat dari {hotel_itinerary}:")
                st.dataframe(paket[['nama', 'type', 'jarak_ke_hotel', 'vote_average']], use_container_width=True)

    with tab3:
        st.header("Analisis Sensitivitas Bobot Kriteria")
        st.write("Gunakan fitur ini untuk menganalisis bagaimana pergeseran peringkat objek wisata jika salah satu bobot kriteria dinaikkan sebesar +2 poin.")
        
        kriteria_tes = st.selectbox(
            "Pilih Kriteria yang ingin diuji sensitivitasnya:", 
            ['vote_average', 'vote_count', 'htm_weekday', 'jarak_ke_hotel']
        )
        
        if st.button("Jalankan Analisis Pergeseran"):
            tabel_sensitivitas = hitung_analisis_sensitivitas(hotel_pilih, bobot_user, kriteria_tes, delta=2)
            st.warning("Tabel Perbandingan Urutan Ranking (Nilai 'Perubahan_Posisi' positif menunjukkan ranking alternatif tersebut naik setelah bobot diubah):")
            st.dataframe(tabel_sensitivitas, use_container_width=True)
# main.py
from pathlib import Path
import pandas as pd
import numpy as np
# Mengambil rumus dari file wp.py
from wp import core_weighted_product, hitung_jarak_haversine

# Setup Path Data Sesuai Kepunyaanmu
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

CSV_PATH_HOTEL = PROJECT_ROOT / "dataset" / "clean" / "data_hotel_clean.csv"
CSV_PATH_PARIWISATA = PROJECT_ROOT / "dataset" / "clean" / "data_pariwisata_clean.csv"
CSV_PATH_WISATA_FINAL = PROJECT_ROOT / "dataset" / "clean" / "data_wisata_clean.csv"

# Load global data
df_hotel = pd.read_csv(CSV_PATH_HOTEL)
df_pariwisata = pd.read_csv(CSV_PATH_PARIWISATA)
df_wisata_final = pd.read_csv(CSV_PATH_WISATA_FINAL)

# TAMBAHKAN BARIS INI UNTUK DIAGNOSIS DI TERMINAL
print(f"--> Sukses memuat {len(df_hotel)} data hotel.")
print(f"--> Sukses memuat {len(df_wisata_final)} data wisata.")

# ==========================================
# FUNGSI REKOMENDASI UTAMA & REKOMENDASI DINAMIS
# ==========================================

def rekomendasi_wisata_dari_hotel(nama_hotel, bobot_user, budget_maks=None, kategori=None, keyword=None, sort_order='descending'):
    """Fitur 1, 2, dan 5: Rekomendasi Wisata + Multi-filtering"""
    hotel_terpilih = df_hotel[df_hotel['NAMA PENGINAPAN'] == nama_hotel].iloc[0]
    
    df_dinamis = df_wisata_final.copy()
    # Hitung Jarak Terdekat secara real-time
    df_dinamis['jarak_ke_hotel'] = hitung_jarak_haversine(
        hotel_terpilih['Latitude'], hotel_terpilih['Longitude'], 
        df_dinamis['latitude'], df_dinamis['longitude']
    )
    
    # Jalankan Filter Kategori & Budget jika diinput user
    if budget_maks:
        df_dinamis = df_dinamis[df_dinamis['htm_weekday'] <= budget_maks]
    if kategori and kategori.lower() != 'semua':
        df_dinamis = df_dinamis[df_dinamis['type'].str.lower() == kategori.lower()]
    if keyword:
        df_dinamis = df_dinamis[df_dinamis['nama'].str.contains(keyword, case=False) | df_dinamis['description'].str.contains(keyword, case=False)]
        
    jenis_kri = {
        'vote_average': 'benefit', 'vote_count': 'benefit',
        'htm_weekday': 'cost', 'htm_weekend': 'cost', 'jarak_ke_hotel': 'cost'
    }
    return core_weighted_product(df_dinamis, bobot_user, jenis_kri, sort_order)


def rekomendasi_hotel_dari_wisata(nama_wisata, bobot_user, sort_order='descending'):
    """Rekomendasi Hotel berdasarkan objek wisata terpilih"""
    wisata_terpilih = df_wisata_final[df_wisata_final['nama'] == nama_wisata].iloc[0]
    
    df_dinamis = df_hotel.copy()
    df_dinamis['BINTANG_SCORE'] = df_dinamis['BINTANG/NON BINTANG'].map({'Bintang': 2, 'Non Bintang': 1}).fillna(1)
    df_dinamis['GOLONGAN_SCORE'] = df_dinamis['GOLONGAN'].astype('category').cat.codes + 1
    
    # Hitung Kriteria Jarak dan Estimasi Waktu Tempuh
    df_dinamis['jarak_ke_wisata'] = hitung_jarak_haversine(
        wisata_terpilih['latitude'], wisata_terpilih['longitude'], 
        df_dinamis['Latitude'], df_dinamis['Longitude']
    )
    df_dinamis['estimasi_waktu_menit'] = (df_dinamis['jarak_ke_wisata'] / 40) * 60
    
    jenis_kri = {
        'JUMLAH KAMAR': 'benefit', 'BINTANG_SCORE': 'benefit', 'GOLONGAN_SCORE': 'benefit',
        'jarak_ke_wisata': 'cost', 'estimasi_waktu_menit': 'cost'
    }
    return core_weighted_product(df_dinamis, bobot_user, jenis_kri, sort_order)


# ==========================================
# FITUR ADVANCED: ITINERARY & SENSITIVITAS
# ==========================================

def buat_paket_itinerary(nama_hotel, bobot_user, radius_km=15):
    """Fitur 3: Membuat paket rute 3 wisata terdekat dari hotel"""
    hotel_terpilih = df_hotel[df_hotel['NAMA PENGINAPAN'] == nama_hotel].iloc[0]
    df_dinamis = df_wisata_final.copy()
    df_dinamis['jarak_ke_hotel'] = hitung_jarak_haversine(
        hotel_terpilih['Latitude'], hotel_terpilih['Longitude'], df_dinamis['latitude'], df_dinamis['longitude']
    )
    
    # Ambil yang masuk radius saja
    df_radius = df_dinamis[df_dinamis['jarak_ke_hotel'] <= radius_km]
    jenis_kri = {
        'vote_average': 'benefit', 'vote_count': 'benefit',
        'htm_weekday': 'cost', 'htm_weekend': 'cost', 'jarak_ke_hotel': 'cost'
    }
    hasil = core_weighted_product(df_radius, bobot_user, jenis_kri, sort_order='descending')
    return hasil.head(3)


def hitung_analisis_sensitivitas(nama_hotel, bobot_base, kriteria_diubah, delta=1):
    """Fitur 4: Melihat efek pergeseran ranking jika bobot kriteria diubah"""
    jenis_kri = {
        'vote_average': 'benefit', 'vote_count': 'benefit',
        'htm_weekday': 'cost', 'htm_weekend': 'cost', 'jarak_ke_hotel': 'cost'
    }
    
    # Ambil hasil kalkulasi awal
    df_awal = rekomendasi_wisata_dari_hotel(nama_hotel, bobot_base)
    df_awal_sub = df_awal[['nama', 'Ranking']].rename(columns={'Ranking': 'Rank_Awal'})
    
    # Modifikasi bobot kriteria target
    bobot_baru = bobot_base.copy()
    bobot_baru[kriteria_diubah] += delta
    
    df_baru = rekomendasi_wisata_dari_hotel(nama_hotel, bobot_baru)
    df_baru_sub = df_baru[['nama', 'Ranking']].rename(columns={'Ranking': 'Rank_Baru'})
    
    merge_df = pd.merge(df_awal_sub, df_baru_sub, on='nama')
    merge_df['Perubahan_Posisi'] = merge_df['Rank_Awal'] - merge_df['Rank_Baru']
    return merge_df.sort_values(by='Rank_Baru').head(10)
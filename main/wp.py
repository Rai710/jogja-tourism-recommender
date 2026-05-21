from pathlib import Path
import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = CURRENT_DIR.parent.parent

CSV_PATH_HOTEL = PROJECT_ROOT / "dataset" / "clean" / "data_hotel_clean.csv"
CSV_PATH_PARIWISATA = PROJECT_ROOT / "dataset" / "clean" / "data_pariwisata_clean.csv"
CSV_PATH_WISATA_FINAL = PROJECT_ROOT / "dataset" / "clean" / "data_wisata_final.csv"

df_hotel = pd.read_csv(CSV_PATH_HOTEL)
df_pariwisata = pd.read_csv(CSV_PATH_PARIWISATA)
df_wisata_final = pd.read_csv(CSV_PATH_WISATA_FINAL)

def 
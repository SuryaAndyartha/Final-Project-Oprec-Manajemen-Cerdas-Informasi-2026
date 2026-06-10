import os
from pathlib import Path
import pandas as pd

DATA_SOURCE_DIR = os.environ.get("DATA_SOURCE_DIR", "/opt/airflow/data")
DATA_LAKE_DIR   = os.environ.get("DATA_LAKE_DIR",   "/opt/airflow/data_lake")
RAW_PARQUET_DIR = os.path.join(DATA_LAKE_DIR, "raw_parquet")

FILES = [
    "orders",
    "order_items",
    "sellers",
    "customers",
    "geolocation",
    "order_reviews",
    "products",
    "category_translation",
    "order_payments",
    "closed_deals",
    "mql",
]

def extract():
    print("\n[extract] DustiniaDelixia_Groceria")

    for name in FILES:
        csv_path     = os.path.join(DATA_SOURCE_DIR, f"{name}.csv")
        parquet_path = os.path.join(RAW_PARQUET_DIR, name)

        if not Path(csv_path).exists():
            print(f"File tidak ditemukan, skip: {csv_path}")
            continue

        # Semua kolom dibaca sebagai string — konsisten, tidak ada inferSchema
        df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

        os.makedirs(parquet_path, exist_ok=True)
        df.to_parquet(
            os.path.join(parquet_path, "part-0.parquet"),
            index=False
        )

        print(f"{name:30s} {len(df):>8,} rows → {parquet_path}")

    print("\nExtract selesai!")

if __name__ == "__main__":
    extract()

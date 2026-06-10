import os
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import shutil

DATA_LAKE_DIR        = os.environ.get("DATA_LAKE_DIR", "/opt/airflow/data_lake")
RAW_PARQUET_DIR      = os.path.join(DATA_LAKE_DIR, "raw_parquet")
CLEAN_PARQUET_DIR    = os.path.join(DATA_LAKE_DIR, "clean_parquet")
REJECTED_PARQUET_DIR = os.path.join(DATA_LAKE_DIR, "rejected_parquet")


def log(name, before, after, note=""):
    dropped = before - after
    pct     = (dropped / before * 100) if before > 0 else 0
    tag     = f"  dropped {dropped:,} rows ({pct:.1f}%)" if dropped > 0 else "  no rows dropped"
    suffix  = f" [{note}]" if note else ""
    print(f"{name:30s} {before:>8,} -> {after:>8,}{tag}{suffix}")

def _write_parquet(df: pd.DataFrame, path: str):
    if os.path.exists(path):
        shutil.rmtree(path)      
    os.makedirs(path)
    pq.write_table(
        pa.Table.from_pandas(df, preserve_index=False),
        os.path.join(path, "part-0.parquet")
    )


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    timestamp_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in timestamp_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    carrier_before_approved = (
        df["order_delivered_carrier_date"].notna() &
        df["order_approved_at"].notna() &
        (df["order_delivered_carrier_date"] < df["order_approved_at"])
    )
    customer_before_carrier = (
        df["order_delivered_customer_date"].notna() &
        df["order_delivered_carrier_date"].notna() &
        (df["order_delivered_customer_date"] < df["order_delivered_carrier_date"])
    )

    anomaly = carrier_before_approved | customer_before_carrier
    rejected = df[anomaly].copy()

    if len(rejected) > 0:
        rejected["reject_reason"] = "carrier_before_approved"
        rejected.loc[customer_before_carrier & anomaly, "reject_reason"] = "customer_before_carrier"
        rejected.loc[carrier_before_approved & customer_before_carrier, "reject_reason"] = (
            "carrier_before_approved AND customer_before_carrier"
        )
        _write_parquet(rejected, os.path.join(REJECTED_PARQUET_DIR, "orders"))

    df_clean = df[~anomaly].reset_index(drop=True)
    log("orders", before, len(df_clean))
    return df_clean


def transform_order_reviews(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    df["review_score"]            = pd.to_numeric(df["review_score"], errors="coerce").astype("Int64")
    df["review_creation_date"]    = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")

    log("order_reviews", before, len(df))
    return df


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    before   = len(df)
    int_cols = ["product_name_lenght", "product_description_lenght", "product_photos_qty"]

    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    log("products", before, len(df))
    return df


def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df["customer_zip_code_prefix"] = (
        df["customer_zip_code_prefix"].astype(str).str.zfill(5)
    )
    log("customers", before, len(df))
    return df


def transform_sellers(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df["seller_zip_code_prefix"] = (
        df["seller_zip_code_prefix"].astype(str).str.zfill(5)
    )
    log("sellers", before, len(df))
    return df


def transform_geolocation():
    raw_path      = os.path.join(RAW_PARQUET_DIR,      "geolocation")
    clean_path    = os.path.join(CLEAN_PARQUET_DIR,    "geolocation")
    rejected_path = os.path.join(REJECTED_PARQUET_DIR, "geolocation")

    df     = pq.read_table(raw_path).to_pandas()
    before = len(df)

    df["geolocation_zip_code_prefix"] = (
        df["geolocation_zip_code_prefix"].astype(str).str.zfill(5)
    )
    df["geolocation_lat"] = pd.to_numeric(df["geolocation_lat"], errors="coerce")
    df["geolocation_lng"] = pd.to_numeric(df["geolocation_lng"], errors="coerce")

    df         = df.drop_duplicates()
    after_dedup = len(df)

    in_bounds = (
        df["geolocation_lat"].between(-35, 5) &
        df["geolocation_lng"].between(-75, -30)
    )
    rejected = df[~in_bounds]
    df_clean = df[in_bounds].reset_index(drop=True)

    if len(rejected) > 0:
        _write_parquet(rejected, rejected_path)

    _write_parquet(df_clean, clean_path)

    print(f"  geolocation dedup: {before:,} -> {after_dedup:,} (dropped {before - after_dedup:,} duplicates)")
    log("geolocation", after_dedup, len(df_clean), "out-of-bounds Brazil removed")


def transform_passthrough(df: pd.DataFrame, name: str) -> pd.DataFrame:
    print(f"{name:30s} {len(df):>8,} passthrough")
    return df


def transform():
    print("\n[transform] DustiniaDelixia_Groceria")

    transform_map = {
        "orders":        transform_orders,
        "order_reviews": transform_order_reviews,
        "products":      transform_products,
        "customers":     transform_customers,
        "sellers":       transform_sellers,
    }

    FILES = [
        "orders", "order_items", "sellers", "customers",
        "order_reviews", "products", "category_translation",
        "order_payments", "closed_deals", "mql",
    ]

    for name in FILES:
        raw_path   = os.path.join(RAW_PARQUET_DIR,   name)
        clean_path = os.path.join(CLEAN_PARQUET_DIR, name)

        df = pq.read_table(raw_path).to_pandas()

        if name in transform_map:
            df_clean = transform_map[name](df)
        else:
            df_clean = transform_passthrough(df, name)

        _write_parquet(df_clean, clean_path)

    transform_geolocation()

    print("[done] Transform selesai")


if __name__ == "__main__":
    transform()
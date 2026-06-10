import os
import re
import pyarrow.parquet as pq
from clickhouse_driver import Client
import pandas as pd

DATA_LAKE_DIR     = os.environ.get("DATA_LAKE_DIR", "/opt/airflow/data_lake")
CLEAN_PARQUET_DIR = os.path.join(DATA_LAKE_DIR, "clean_parquet")

TABLE_SCHEMAS = {
    "orders": """
        CREATE TABLE groceria.orders (
            order_id                        String,
            customer_id                     String,
            order_status                    String,
            order_purchase_timestamp        Nullable(DateTime),
            order_approved_at               Nullable(DateTime),
            order_delivered_carrier_date    Nullable(DateTime),
            order_delivered_customer_date   Nullable(DateTime),
            order_estimated_delivery_date   Nullable(DateTime)
        ) ENGINE = MergeTree()
        ORDER BY order_id
    """,
    "order_items": """
        CREATE TABLE groceria.order_items (
            order_id            String,
            order_item_id       Int32,
            product_id          String,
            seller_id           String,
            shipping_limit_date Nullable(DateTime),
            price               Float64,
            freight_value       Float64
        ) ENGINE = MergeTree()
        ORDER BY (order_id, order_item_id)
    """,
    "sellers": """
        CREATE TABLE groceria.sellers (
            seller_id               String,
            seller_zip_code_prefix  String,
            seller_city             String,
            seller_state            String
        ) ENGINE = MergeTree()
        ORDER BY seller_id
    """,
    "customers": """
        CREATE TABLE groceria.customers (
            customer_id                 String,
            customer_unique_id          String,
            customer_zip_code_prefix    String,
            customer_city               String,
            customer_state              String
        ) ENGINE = MergeTree()
        ORDER BY customer_id
    """,
    "geolocation": """
        CREATE TABLE groceria.geolocation (
            geolocation_zip_code_prefix String,
            geolocation_lat             Float64,
            geolocation_lng             Float64,
            geolocation_city            String,
            geolocation_state           String
        ) ENGINE = MergeTree()
        ORDER BY geolocation_zip_code_prefix
    """,
    "order_reviews": """
        CREATE TABLE groceria.order_reviews (
            review_id               String,
            order_id                String,
            review_score            Nullable(Int32),
            review_comment_title    Nullable(String),
            review_comment_message  Nullable(String),
            review_creation_date    Nullable(DateTime),
            review_answer_timestamp Nullable(DateTime)
        ) ENGINE = MergeTree()
        ORDER BY review_id
    """,
    "products": """
        CREATE TABLE groceria.products (
            product_id                      String,
            product_category_name           Nullable(String),
            product_name_lenght             Nullable(Int32),
            product_description_lenght      Nullable(Int32),
            product_photos_qty              Nullable(Int32),
            product_weight_g                Nullable(Float64),
            product_length_cm               Nullable(Float64),
            product_height_cm               Nullable(Float64),
            product_width_cm                Nullable(Float64)
        ) ENGINE = MergeTree()
        ORDER BY product_id
    """,
    "category_translation": """
        CREATE TABLE groceria.category_translation (
            product_category_name           String,
            product_category_name_english   String
        ) ENGINE = MergeTree()
        ORDER BY product_category_name
    """,
    "order_payments": """
        CREATE TABLE groceria.order_payments (
            order_id                String,
            payment_sequential      Int32,
            payment_type            String,
            payment_installments    Int32,
            payment_value           Float64
        ) ENGINE = MergeTree()
        ORDER BY (order_id, payment_sequential)
    """,
    "closed_deals": """
        CREATE TABLE groceria.closed_deals (
            mql_id                          String,
            seller_id                       String,
            sdr_id                          Nullable(String),
            sr_id                           Nullable(String),
            won_date                        Nullable(String),
            business_segment                Nullable(String),
            lead_type                       Nullable(String),
            lead_behaviour_profile          Nullable(String),
            has_company                     Nullable(String),
            has_gtin                        Nullable(String),
            average_stock                   Nullable(String),
            business_type                   Nullable(String),
            declared_product_catalog_size   Nullable(Float64),
            declared_monthly_revenue        Nullable(Float64)
        ) ENGINE = MergeTree()
        ORDER BY mql_id
    """,
    "mql": """
        CREATE TABLE groceria.mql (
            mql_id                  String,
            first_contact_date      Nullable(String),
            landing_page_id         Nullable(String),
            origin                  Nullable(String)
        ) ENGINE = MergeTree()
        ORDER BY mql_id
    """,
}

FILES = [
    "orders", "order_items", "sellers", "customers", "geolocation",
    "order_reviews", "products", "category_translation",
    "order_payments", "closed_deals", "mql",
]

_COL_RE = re.compile(
    r"^\s+(\w+)\s+(?:Nullable\()?(\w+)(?:\))?\s*,?\s*$",
    re.MULTILINE,
)

def _parse_schema(ddl: str) -> dict[str, str]:
    """Return {col_name: clickhouse_type} dari DDL string."""
    result = {}
    for col, ch_type in _COL_RE.findall(ddl):
        result[col] = ch_type
    return result

SCHEMA_TYPES: dict[str, dict[str, str]] = {
    name: _parse_schema(ddl) for name, ddl in TABLE_SCHEMAS.items()
}

INT_CH_TYPES = {"Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64"}

DATETIME_CH_TYPES = {"DateTime", "Date"}

FLOAT_CH_TYPES = {"Float32", "Float64"}


def safe_val(x):
    if pd.isna(x):
        return None
    if isinstance(x, pd.Timestamp):
        return x.to_pydatetime()
    return x.item() if hasattr(x, "item") else x


def prepare_df(df: pd.DataFrame, name: str):
    col_types = SCHEMA_TYPES.get(name, {})

    for col in df.columns:
        ch_type = col_types.get(col, "")

        if ch_type in INT_CH_TYPES:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        elif ch_type in FLOAT_CH_TYPES:                                      
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
        elif ch_type == "String":
            df[col] = df[col].fillna("").astype(str)
        elif ch_type in DATETIME_CH_TYPES:                       
            df[col] = pd.to_datetime(df[col], errors="coerce") 

    schema_cols  = list(df.columns)
    data_tuples  = [
        tuple(safe_val(row[col]) for col in schema_cols)
        for _, row in df[schema_cols].iterrows()
    ]
    return schema_cols, data_tuples


# def load():
#     client = Client(host="clickhouse-server", user="admin", password="rahasia")
#     client.execute("CREATE DATABASE IF NOT EXISTS groceria")

#     print("\n[load] DustiniaDelixia_Groceria")

#     for name in FILES:
#         parquet_path = os.path.join(CLEAN_PARQUET_DIR, name)
#         df           = pq.read_table(parquet_path).to_pandas()
#         row_count    = len(df)

#         client.execute(TABLE_SCHEMAS[name].replace(
#             f"CREATE TABLE groceria.{name}",
#             f"CREATE TABLE IF NOT EXISTS groceria.{name}"
#         ))
#         client.execute(f"TRUNCATE TABLE groceria.{name}")

#         schema_cols, data_tuples = prepare_df(df, name)

#         if data_tuples:
#             client.execute(
#                 f"INSERT INTO groceria.{name} VALUES",
#                 data_tuples,
#             )

#         print(f"{name:30s} {row_count:>8,} rows → groceria.{name}")

#     print("[done] Load selesai!")

def load():
    client = Client(host="clickhouse-server", user="admin", password="rahasia")
    client.execute("CREATE DATABASE IF NOT EXISTS groceria")
 
    print("\n[load] DustiniaDelixia_Groceria")
 
    # Fase 1: CREATE + TRUNCATE semua tabel sekaligus sebelum ada insert.
    # Ini memastikan kalau pipeline di-run ulang (retry / manual trigger),
    # tidak ada data lama yang tersisa di tabel manapun.
    print("[load] Fase 1 — mempersiapkan tabel (create + truncate)...")
    for name in FILES:
        client.execute(TABLE_SCHEMAS[name].replace(
            f"CREATE TABLE groceria.{name}",
            f"CREATE TABLE IF NOT EXISTS groceria.{name}"
        ))
        client.execute(f"TRUNCATE TABLE groceria.{name}")
 
    # Fase 2: Insert data ke semua tabel.
    print("[load] Fase 2 — insert data...")
    for name in FILES:
        parquet_path = os.path.join(CLEAN_PARQUET_DIR, name)
        df           = pq.read_table(parquet_path).to_pandas()
        row_count    = len(df)
 
        schema_cols, data_tuples = prepare_df(df, name)
 
        if data_tuples:
            client.execute(
                f"INSERT INTO groceria.{name} VALUES",
                data_tuples,
            )
 
        print(f"{name:30s} {row_count:>8,} rows → groceria.{name}")
 
    print("[done] Load selesai!")


if __name__ == "__main__":
    load()
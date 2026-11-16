
from pathlib import Path
import duckdb

# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = PROCESSED_DIR / "olist_warehouse.duckdb"

# --------------------------------------------------
# 2. SOURCE FILES AND TARGET TABLES
# --------------------------------------------------

datasets = {
    "raw_customers": "olist_customers_dataset.csv",
    "raw_geolocation": "olist_geolocation_dataset.csv",
    "raw_order_items": "olist_order_items_dataset.csv",
    "raw_order_payments": "olist_order_payments_dataset.csv",
    "raw_order_reviews": "olist_order_reviews_dataset.csv",
    "raw_orders": "olist_orders_dataset.csv",
    "raw_products": "olist_products_dataset.csv",
    "raw_sellers": "olist_sellers_dataset.csv",
    "raw_category_translation": "product_category_name_translation.csv"
}

# --------------------------------------------------
# 3. CONNECT TO DUCKDB
# --------------------------------------------------

print("=" * 70)
print("OLIST RAW DATA LOADING")
print("=" * 70)

print(f"\nDatabase: {DB_PATH}")

con = duckdb.connect(str(DB_PATH))

# --------------------------------------------------
# 4. LOAD CSV FILES INTO RAW TABLES
# --------------------------------------------------

for table_name, filename in datasets.items():

    csv_path = RAW_DIR / filename

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {csv_path}"
        )

    print(f"\nLoading: {filename}")

    # Escape single quotes in file paths
    safe_path = csv_path.as_posix().replace("'", "''")

    con.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT *
        FROM read_csv_auto(
            '{safe_path}',
            all_varchar = true
        )
    """)

    row_count = con.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    column_count = len(
        con.execute(f"DESCRIBE {table_name}").fetchall()
    )

    print(f"Table created: {table_name}")
    print(f"Rows: {row_count:,}")
    print(f"Columns: {column_count}")

# --------------------------------------------------
# 5. VERIFY LOADED TABLES
# --------------------------------------------------

print("\n" + "=" * 70)
print("RAW LAYER VALIDATION")
print("=" * 70)

tables = con.execute("SHOW TABLES").fetchall()

for table in tables:
    print(table[0])

print("\nTotal tables loaded:", len(tables))

# --------------------------------------------------
# 6. CLOSE CONNECTION
# --------------------------------------------------

con.close()

print("\n" + "=" * 70)
print("RAW DATA LOADING COMPLETED")
print("=" * 70)

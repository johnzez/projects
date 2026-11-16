from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_DIR / "data" / "processed" / "olist_warehouse.duckdb"

con = duckdb.connect(str(DB_PATH))

result = con.execute("""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT review_id || '-' || order_id) AS unique_pairs
    FROM raw_order_reviews
""").fetchone()

total_rows, unique_pairs = result

print("Total review rows:", total_rows)
print("Unique review-order pairs:", unique_pairs)
print("Duplicate composite keys:", total_rows - unique_pairs)

con.close()


from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"

print("\n========== MISSING VALUES INVESTIGATION ==========\n")

for filename in [
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv"
]:
    df = pd.read_csv(RAW_DIR / filename, low_memory=False)

    missing = df.isna().sum()
    missing = missing[missing > 0]

    print(f"\nFILE: {filename}")
    print(missing.to_string())

print("\n========== GEOLOCATION DUPLICATES ==========\n")

geo = pd.read_csv(
    RAW_DIR / "olist_geolocation_dataset.csv"
)

print("Total rows:", len(geo))
print("Exact duplicate rows:", geo.duplicated().sum())

print(
    "Unique ZIP prefixes:",
    geo["geolocation_zip_code_prefix"].nunique()
)

print(
    "Unique coordinate pairs:",
    geo[["geolocation_lat", "geolocation_lng"]]
    .drop_duplicates().shape[0]
)

print(
    "\nSample duplicate rows:"
)

print(
    geo[geo.duplicated(keep=False)]
    .head(10).to_string(index=False)
)

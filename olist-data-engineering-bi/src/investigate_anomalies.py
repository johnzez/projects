from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"

print("=" * 70)
print("ANOMALY INVESTIGATION")
print("=" * 70)

# 1. INVESTIGATE DUPLICATE REVIEW IDs

reviews = pd.read_csv(
    RAW_DIR / "olist_order_reviews_dataset.csv"
)

print("\n1. DUPLICATE REVIEW IDs")
print("-" * 70)

duplicate_mask = reviews.duplicated(
    subset=["review_id"],
    keep=False
)

duplicate_reviews = reviews[duplicate_mask]

print("Total review records:", len(reviews))
print("Unique review IDs:", reviews["review_id"].nunique())
print("Rows involved in duplicate IDs:", len(duplicate_reviews))
print(
    "Number of duplicated review IDs:",
    duplicate_reviews["review_id"].nunique()
)

print("\nSample duplicate review records:")

print(
    duplicate_reviews
    .sort_values("review_id")
    .head(10)
    .to_string(index=False)
)

print("\nAre the duplicate rows completely identical?")

print(
    "Exact duplicate rows:",
    reviews.duplicated().sum()
)

print("\n2. DELIVERED ORDERS WITH MISSING DATES")
print("-" * 70)

orders = pd.read_csv(
    RAW_DIR / "olist_orders_dataset.csv"
)

date_columns = [
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date"
]

delivered = orders[
    orders["order_status"] == "delivered"
]

anomalies = delivered[
    delivered[date_columns].isna().any(axis=1)
]

print("Total delivered orders:", len(delivered))
print("Delivered orders with missing dates:", len(anomalies))

print("\nAffected records:")

print(
    anomalies[
        ["order_id", "order_status"] + date_columns
    ].head(15).to_string(index=False)
)

print("\nAnomaly investigation completed.")
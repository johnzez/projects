
from pathlib import Path
import pandas as pd

# Locate the raw data directory
PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_DIR / "data" / "raw"

print("=" * 60)
print("OLIST DATASET INSPECTION")
print("=" * 60)

csv_files = list(RAW_DATA_DIR.glob("*.csv"))

if not csv_files:
    print("No CSV files found!")
else:
    print(f"\nFound {len(csv_files)} CSV files.\n")

    for file in sorted(csv_files):
        print("-" * 60)
        print(f"FILE: {file.name}")

        try:
            df = pd.read_csv(file, nrows=5)

            print(f"COLUMNS: {list(df.columns)}")
            print("\nSAMPLE DATA:")
            print(df.head(3).to_string(index=False))

        except Exception as error:
            print(f"ERROR: {error}")

print("\nInspection completed.")


from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Store profiling results
summary_results = []
column_results = []

print("=" * 70)
print("OLIST DATA QUALITY & PROFILING")
print("=" * 70)

csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))

for file in csv_files:

    print(f"\nAnalyzing: {file.name}")

    # Load complete dataset
    df = pd.read_csv(file, low_memory=False)

    total_rows = len(df)
    total_columns = len(df.columns)
    duplicate_rows = int(df.duplicated().sum())
    total_missing = int(df.isna().sum().sum())

    missing_percentage = (
        total_missing / (total_rows * total_columns) * 100
        if total_rows * total_columns > 0 else 0
    )

    # File-level summary
    summary_results.append({
        "file_name": file.name,
        "total_rows": total_rows,
        "total_columns": total_columns,
        "duplicate_rows": duplicate_rows,
        "missing_values": total_missing,
        "missing_percentage": round(missing_percentage, 2)
    })

    print(f"Rows: {total_rows:,}")
    print(f"Columns: {total_columns}")
    print(f"Duplicate rows: {duplicate_rows:,}")
    print(f"Missing values: {total_missing:,}")
    print(f"Missing percentage: {missing_percentage:.2f}%")

    # Column-level analysis
    for column in df.columns:

        missing_count = int(df[column].isna().sum())

        column_results.append({
            "file_name": file.name,
            "column_name": column,
            "data_type": str(df[column].dtype),
            "missing_values": missing_count,
            "missing_percentage": round(
                missing_count / total_rows * 100, 2
            ) if total_rows > 0 else 0,
            "unique_values": int(df[column].nunique())
        })

# Convert results into DataFrames
summary_df = pd.DataFrame(summary_results)
columns_df = pd.DataFrame(column_results)

# Export reports
summary_path = OUTPUT_DIR / "dataset_summary.csv"
columns_path = OUTPUT_DIR / "column_profile.csv"

summary_df.to_csv(summary_path, index=False)
columns_df.to_csv(columns_path, index=False)

print("\n" + "=" * 70)
print("DATA PROFILING COMPLETED")
print("=" * 70)

print("\nDATASET SUMMARY:")
print(summary_df.to_string(index=False))

print(f"\nReports saved:")
print(summary_path)
print(columns_path)

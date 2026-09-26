import duckdb
from pathlib import Path


# -----------------------------
# Paths
# -----------------------------

database_path = "data/warehouse/f1_weather.duckdb"
output_directory = Path("data/processed/analysis")

output_directory.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Connect to DuckDB
# -----------------------------

conn = duckdb.connect(database_path)


# -----------------------------
# Export dashboard data
# -----------------------------

parquet_path = output_directory / "lap_analysis.parquet"
csv_path = output_directory / "lap_analysis.csv"

conn.execute(f"""
    COPY lap_analysis
    TO '{parquet_path}'
    (FORMAT PARQUET);
""")

conn.execute(f"""
    COPY lap_analysis
    TO '{csv_path}'
    (HEADER, DELIMITER ',');
""")


# -----------------------------
# Validate exports
# -----------------------------

row_count = conn.execute("""
    SELECT COUNT(*)
    FROM lap_analysis;
""").fetchone()[0]

print(f"Rows exported: {row_count}")
print(f"Parquet: {parquet_path}")
print(f"CSV: {csv_path}")


# -----------------------------
# Close connection
# -----------------------------

conn.close()

print("\nDashboard data export complete")
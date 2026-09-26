import json
import pandas as pd
from pathlib import Path


# -----------------------------
# Paths
# -----------------------------

input_path = "data/raw/openf1/session_9636_race_control.json"
output_path = "data/processed/openf1/session_9636_race_control.parquet"


# -----------------------------
# Load raw data
# -----------------------------

with open(input_path, "r") as file:
    data = json.load(file)

df = pd.DataFrame(data)


# -----------------------------
# Clean timestamp
# -----------------------------

df["date"] = pd.to_datetime(
    df["date"],
    format="ISO8601",
    utc=True
)


# -----------------------------
# Select useful columns
# -----------------------------

df = df[
    [
        "meeting_key",
        "session_key",
        "date",
        "lap_number",
        "category",
        "flag",
        "scope",
        "sector",
        "driver_number",
        "message"
    ]
]


# -----------------------------
# Validate
# -----------------------------

print("Shape:", df.shape)
print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isna().sum())


# -----------------------------
# Save processed data
# -----------------------------

Path(output_path).parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_parquet(
    output_path,
    index=False
)

print("\nSaved to:", output_path)